import logging
import os
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI, Request

from .config import load_config

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.config = load_config()
    app.state.db = await asyncpg.create_pool(os.environ["DATABASE_URL"])
    # Logged server-side only: the condition must never be exposed to participants.
    logger.info("Loaded config: %s", app.state.config.model_dump())
    yield
    await app.state.db.close()


app = FastAPI(title="CHM Group Decision Experiment", lifespan=lifespan)


@app.get("/health")
async def health(request: Request):
    async with request.app.state.db.acquire() as conn:
        await conn.fetchval("SELECT 1")
    return {"status": "ok"}