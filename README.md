# Multi-Participant Human-AI Group Decision Experiment

A lightweight real-time platform for a 3-participant group decision experiment.
Participants chat for two rounds, vote after each round, and elect a **Decision Maker**.
Participants can be humans or AI agents, and humans are never told which is which.

**Stack:** React (Vite) · FastAPI (WebSockets) · PostgreSQL · Docker Compose · nginx

## Quick Start

Requires Docker Desktop.

```bash
docker compose up --build
```

Then open **http://localhost:3000**, once per human participant (e.g. in separate browser tabs).
The session starts automatically once all human slots are filled.

Stop with `Ctrl + C` (or `docker compose down`).

## Switching Experimental Conditions

Edit `participants` in [`config.yml`](config.yml):

| Condition | `participants` | Browser tabs needed |
|---|---|---|
| 3 humans | `[human, human, human]` | 3 |
| 2 humans + 1 AI | `[human, human, ai]` (default) | 2 |
| 1 human + 2 AI | `[human, ai, ai]` | 1 |

`config.yml` is mounted into the backend container, so **no rebuild is needed**: just run

```bash
docker compose restart backend
```

Round count and phase durations are configured in the same file. Invalid configs
(e.g. not exactly 3 participants, or no human) fail at startup with a clear error.

## Architecture

```
Browser (React) ──WebSocket /ws──► nginx :3000 ──► FastAPI :8000 ──► PostgreSQL
```

- **`backend/app/session.py`**: `SessionManager` assigns each connecting human to the
  waiting session and starts it when all human slots are filled. Each `Session` runs the
  full experiment as one async task with **server-authoritative timers**:
  waiting → discussion → voting → round feedback → … → results.
- **`backend/app/ai_agent.py`**: rule-based AI participant (see Design Decisions).
- **`backend/app/db.py`**: append-only event log in PostgreSQL.
- **`frontend/src/App.jsx`**: a single reducer maps server messages to UI state;
  the client never decides anything on its own.

### WebSocket protocol

| Direction | Message |
|---|---|
| server → client | `welcome {you, players}` · `phase {phase, round, seconds, …}` · `chat {from, text}` · `vote_ack {target}` |
| client → server | `chat {text}` (accepted only during discussion) · `vote {target}` (one per round, only during voting) |

## Data

Every session is fully reconstructable from three tables: `sessions` (condition),
`participants` (label → human/ai, server-side only) and `events` (joins, chat messages,
votes, abstentions, phase changes, tallies, result, all timestamped).

```bash
docker compose exec db psql -U chm -d experiment -c \
  "SELECT ts, type, participant, payload FROM events ORDER BY id DESC LIMIT 30;"
```

## Design Decisions

| Topic | Decision | Rationale |
|---|---|---|
| Blinding | Labels (Player A/B/C) are randomly shuffled per session; participant type is never sent to the client; AI messages use human-like typing delays; a random 3–8 s "matching" pause runs before every session; the UI never mentions AI | Prevents identifying the AI by position, network payload, response speed, or by how fast the session starts |
| AI agent | Rule-based agent: 2–3 messages per round with human-like delays, reacts to being mentioned and to the round-1 tally, votes consistently with what it said; two AIs never repeat each other | Fully offline and deterministic enough to test; an LLM-backed agent is natural future work |
| Feedback after round 1 | Round 1 vote tally is shown before round 2 | Gives the second discussion something to react to |
| Final decision | Round 2 votes decide; ties broken by round 1 votes, then randomly | Deterministic where possible, random only as last resort |
| Self-votes | Allowed | Simpler; self-nomination is meaningful research data |
| Missing votes | Recorded as abstention; voting ends early once everyone has voted | Experiment never blocks on an inactive participant |
| Timing | Server-authoritative timers; clients only display countdowns | All participants share one consistent clock |
| Database | PostgreSQL with an append-only event log | Full session data available for later analysis |

### Known limitations

- The AI agent matches keywords and does not understand meaning: if addressed by name it
  always responds as if asked to take the role.
- With 2 AI agents, their "back the round-1 leader" strategy strongly steers the outcome.
  For a real study, the AI strategy should itself be a configurable experimental parameter.

## Out of Scope (time-boxed)

- Reconnection after a participant disconnects
- Authentication / participant IDs from a recruitment platform
- Admin dashboard and data export (data is queryable directly in PostgreSQL)
- Automated tests (all three conditions and the tie-break paths were tested manually)

## Development

- **Time spent:** about 2 h 20 min in total (08:40–11:00), including ~20 min of local environment
  setup (installing Docker Desktop and fixing a full-disk issue that made Docker's storage read-only)
  and ~20 min of manual end-to-end testing of all three conditions.
- **AI usage:** built with an AI assistant; all prompts and the model used are in
  [`ai_prompts.md`](ai_prompts.md).