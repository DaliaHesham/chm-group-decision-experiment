import logging
import os
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect

from .config import load_config
from .db import EventLog
from .session import SessionManager

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = load_config()
    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"])
    log = EventLog(pool)
    await log.init_schema()
    app.state.db = pool
    app.state.manager = SessionManager(config, log)
    # Logged server-side only: the condition must never be exposed to participants.
    logger.info("Loaded config: %s", config.model_dump())
    yield
    await pool.close()


app = FastAPI(title="CHM Group Decision Experiment", lifespan=lifespan)


@app.get("/health")
async def health(request: Request):
    async with request.app.state.db.acquire() as conn:
        await conn.fetchval("SELECT 1")
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    manager = ws.app.state.manager
    session, me = await manager.join(ws)
    try:
        while True:
            await session.handle(me, await ws.receive_json())
    except WebSocketDisconnect:
        pass
    finally:
        await manager.leave(session, me)