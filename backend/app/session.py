import asyncio
import logging
import random
import time
import uuid
from collections import Counter

from fastapi import WebSocket

from .ai_agent import ScriptedAgent
from .config import ExperimentConfig
from .db import EventLog

logger = logging.getLogger("uvicorn.error")
LABELS = ["Player A", "Player B", "Player C"]


class Participant:
    def __init__(self, label: str, kind: str):
        self.label = label
        self.kind = kind  # "human" | "ai" -- server-side only, never sent to clients
        self.ws: WebSocket | None = None


class Session:
    def __init__(self, config: ExperimentConfig, log: EventLog):
        self.id = uuid.uuid4().hex[:8]
        self.config = config
        self.log = log
        kinds = list(config.participants)
        random.shuffle(kinds)  # blinding: the AI is not always the same label
        self.participants = {label: Participant(label, kind) for label, kind in zip(LABELS, kinds)}
        self.agents = {
            label: ScriptedAgent(label, LABELS, config.ai)
            for label, p in self.participants.items() if p.kind == "ai"
        }
        self.phase = "waiting"
        self.round = 0
        self.votes: dict[int, dict[str, str]] = {}
        self.chat: list[tuple[int, str, str]] = []  # (round, sender, text) -- read by AI agents
        self.used_lines: set[str] = set()
        self.all_voted = asyncio.Event()

    async def persist(self):
        await self.log.create_session(
            self.id, self.config.model_dump(),
            {label: p.kind for label, p in self.participants.items()},
        )

    def open_human_slot(self) -> Participant | None:
        return next((p for p in self.participants.values() if p.kind == "human" and p.ws is None), None)

    # ---------- messaging ----------
    async def send(self, p: Participant, msg: dict):
        if p.ws is not None:
            try:
                await p.ws.send_json(msg)
            except Exception:
                p.ws = None

    async def broadcast(self, msg: dict):
        for p in self.participants.values():
            await self.send(p, msg)

    async def set_phase(self, phase: str, seconds: int | None = None, **extra):
        self.phase = phase
        await self.log.log(self.id, "phase", None, phase=phase, round=self.round)
        await self.broadcast({
            "type": "phase", "phase": phase, "round": self.round,
            "total_rounds": self.config.rounds, "seconds": seconds, **extra,
        })

    # ---------- incoming messages ----------
    async def handle(self, p: Participant, msg: dict):
        kind = msg.get("type")
        if kind == "chat" and self.phase == "discussion":
            text = str(msg.get("text", "")).strip()[:500]
            if text:
                await self.post_chat(p.label, text)
        elif kind == "vote" and self.phase == "voting":
            target = msg.get("target")
            if target in self.participants and p.label not in self.votes[self.round]:
                await self.record_vote(p.label, target)
                await self.send(p, {"type": "vote_ack", "target": target})

    async def post_chat(self, label: str, text: str):
        if self.phase != "discussion":
            return
        self.chat.append((self.round, label, text))
        await self.log.log(self.id, "chat", label, round=self.round, text=text)
        await self.broadcast({"type": "chat", "from": label, "text": text, "ts": time.time()})

    async def record_vote(self, voter: str, target: str):
        self.votes[self.round][voter] = target
        await self.log.log(self.id, "vote", voter, round=self.round, target=target)
        if len(self.votes[self.round]) == len(LABELS):
            self.all_voted.set()  # everyone voted -> end voting early

    async def cast_ai_votes(self):
        for agent in self.agents.values():
            await self.record_vote(agent.label, agent.favorite)

    # ---------- results ----------
    def tally(self, rnd: int) -> dict[str, int]:
        counts = Counter(self.votes.get(rnd, {}).values())
        return {label: counts.get(label, 0) for label in LABELS}

    def decide(self) -> tuple[str, str]:
        """Final round decides; ties -> previous round's votes -> random."""
        final = self.tally(self.config.rounds)
        top = max(final.values())
        tied = [label for label in LABELS if final[label] == top]
        if len(tied) == 1:
            return tied[0], "most votes in the final round"
        if self.config.rounds > 1:
            previous = self.tally(self.config.rounds - 1)
            best = max(previous[label] for label in tied)
            tied = [label for label in tied if previous[label] == best]
            if len(tied) == 1:
                return tied[0], "tie broken by previous round's votes"
        return random.choice(tied), "tie broken randomly"

    # ---------- experiment flow ----------
    async def run(self):
        try:
            await self._run()
        except Exception:
            logger.exception("Session %s crashed", self.id)

    async def _run(self):
        c = self.config
        # Blinding: same "matching" pause whether or not we waited for other humans.
        await asyncio.sleep(random.uniform(3, 8))
        for rnd in range(1, c.rounds + 1):
            self.round = rnd
            self.votes[rnd] = {}

            if rnd > 1:
                for agent in self.agents.values():
                    agent.update_for_round(self.tally(rnd - 1))
            await self.set_phase("discussion", c.discussion_seconds)
            ai_tasks = [asyncio.create_task(a.discuss(self, rnd, c.discussion_seconds)) for a in self.agents.values()]
            await asyncio.sleep(c.discussion_seconds)
            for task in ai_tasks:
                task.cancel()

            self.all_voted = asyncio.Event()
            await self.set_phase("voting", c.voting_seconds)
            await self.cast_ai_votes()
            try:
                await asyncio.wait_for(self.all_voted.wait(), c.voting_seconds)
            except asyncio.TimeoutError:
                pass
            for label in LABELS:
                if label not in self.votes[rnd]:
                    await self.log.log(self.id, "abstain", label, round=rnd)

            tally = self.tally(rnd)
            await self.log.log(self.id, "round_tally", None, round=rnd, tally=tally)
            if rnd < c.rounds:
                await self.set_phase("feedback", c.feedback_seconds, tally=tally)
                await asyncio.sleep(c.feedback_seconds)

        winner, reason = self.decide()
        tallies = [self.tally(r) for r in range(1, c.rounds + 1)]
        await self.log.log(self.id, "result", winner, reason=reason, tallies=tallies)
        await self.set_phase("results", winner=winner, reason=reason, tallies=tallies)


class SessionManager:
    """Fills one waiting session at a time; starts it once all human slots are taken."""

    def __init__(self, config: ExperimentConfig, log: EventLog):
        self.config = config
        self.log = log
        self.waiting: Session | None = None
        self.lock = asyncio.Lock()
        self.tasks: set[asyncio.Task] = set()

    async def join(self, ws: WebSocket) -> tuple[Session, Participant]:
        async with self.lock:
            if self.waiting is None:
                self.waiting = Session(self.config, self.log)
                await self.waiting.persist()
            session = self.waiting
            me = session.open_human_slot()
            me.ws = ws
            await self.log.log(session.id, "join", me.label)
            await session.send(me, {"type": "welcome", "you": me.label, "players": LABELS})
            await session.send(me, {"type": "phase", "phase": "waiting", "round": 0,
                                    "total_rounds": self.config.rounds, "seconds": None})
            if session.open_human_slot() is None:  # all human slots filled
                self.waiting = None
                task = asyncio.create_task(session.run())
                self.tasks.add(task)
                task.add_done_callback(self.tasks.discard)
            return session, me

    async def leave(self, session: Session, me: Participant):
        me.ws = None  # in the waiting room this frees the slot for someone else
        await self.log.log(session.id, "leave", me.label, phase=session.phase)