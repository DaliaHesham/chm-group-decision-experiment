# Multi-Participant Human-AI Group Decision Experiment

A lightweight real-time platform for a 3-participant group decision experiment
(React + FastAPI + PostgreSQL, Dockerized).

> Setup and run instructions will be added once the app runs.

## Design Decisions

| Topic | Decision | Rationale |
|---|---|---|
| Blinding | Labels (Player A/B/C) are randomly shuffled per session; participant type is never sent to the client; AI messages use human-like typing delays; a random 3–8 s "matching" pause runs before every session; the UI never mentions AI | Prevents identifying the AI by position, network payload, response speed, or by how fast the session starts |
| AI agent | Rule-based agent: 2–3 messages per round with human-like delays, reacts to being mentioned and to the round-1 tally, votes consistently with what it said; two AIs never repeat each other | Fully offline and deterministic enough to test; an LLM-backed agent is natural future work |
| Feedback after round 1 | Round 1 vote tally is shown before round 2 | Gives the second discussion something to react to |
| Final decision | Round 2 votes decide; ties broken by round 1 votes, then randomly | Deterministic where possible, random only as last resort |
| Self-votes | Allowed | Simpler; self-nomination is meaningful research data |
| Missing votes | Recorded as abstention | Experiment never blocks on an inactive participant |
| Timing | Server-authoritative timers; clients only display countdowns | All participants share one consistent clock |
| Database | PostgreSQL with an append-only event log (messages, votes, phase changes, timestamps) | Full session data available for later analysis |

## Out of Scope (time-boxed)

- Reconnection after a participant disconnects
- Authentication / participant IDs from a recruitment platform
- Admin dashboard and data export (data is queryable directly in PostgreSQL)