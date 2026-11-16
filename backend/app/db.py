import json

import asyncpg

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT PRIMARY KEY,
    condition   JSONB NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS participants (
    session_id  TEXT NOT NULL REFERENCES sessions(id),
    label       TEXT NOT NULL,
    kind        TEXT NOT NULL,
    PRIMARY KEY (session_id, label)
);
CREATE TABLE IF NOT EXISTS events (
    id          BIGSERIAL PRIMARY KEY,
    session_id  TEXT NOT NULL REFERENCES sessions(id),
    ts          TIMESTAMPTZ NOT NULL DEFAULT now(),
    type        TEXT NOT NULL,
    participant TEXT,
    payload     JSONB NOT NULL DEFAULT '{}'
);
"""


class EventLog:
    """Persists sessions and an append-only log of everything that happens."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def init_schema(self):
        async with self.pool.acquire() as conn:
            await conn.execute(SCHEMA)

    async def create_session(self, session_id: str, condition: dict, participants: dict[str, str]):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "INSERT INTO sessions (id, condition) VALUES ($1, $2)",
                    session_id, json.dumps(condition),
                )
                await conn.executemany(
                    "INSERT INTO participants (session_id, label, kind) VALUES ($1, $2, $3)",
                    [(session_id, label, kind) for label, kind in participants.items()],
                )

    async def log(self, session_id: str, type: str, participant: str | None = None, **payload):
        await self.pool.execute(
            "INSERT INTO events (session_id, type, participant, payload) VALUES ($1, $2, $3, $4)",
            session_id, type, participant, json.dumps(payload),
        )