import { useEffect, useReducer, useRef, useState } from "react";

const PHASE_LABEL = { discussion: "Discussion", voting: "Voting", feedback: "Round results" };

const initialState = {
  status: "connecting", // connecting | connected | closed
  me: null,
  players: [],
  phase: null,
  round: 0,
  totalRounds: 0,
  deadline: null,
  log: [],
  myVote: null,
  tally: null,
  result: null,
};

// Every server message is turned into UI state here -- the server is the source of truth.
function reducer(state, msg) {
  switch (msg.type) {
    case "welcome":
      return { ...state, me: msg.you, players: msg.players };
    case "phase": {
      const next = {
        ...state,
        status: "connected",
        phase: msg.phase,
        round: msg.round,
        totalRounds: msg.total_rounds,
        deadline: msg.seconds ? Date.now() + msg.seconds * 1000 : null,
      };
      if (msg.phase === "discussion") {
        next.myVote = null;
        next.log = [...state.log, { system: true, text: `Round ${msg.round} discussion started` }];
      }
      if (msg.phase === "feedback") next.tally = msg.tally;
      if (msg.phase === "results") next.result = { winner: msg.winner, reason: msg.reason, tallies: msg.tallies };
      return next;
    }
    case "chat":
      return { ...state, log: [...state.log, { from: msg.from, text: msg.text }] };
    case "vote_ack":
      return { ...state, myVote: msg.target };
    case "closed":
      return { ...state, status: "closed" };
    default:
      return state;
  }
}

function useExperimentSocket(dispatch) {
  const wsRef = useRef(null);
  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${protocol}://${window.location.host}/ws`);
    wsRef.current = ws;
    ws.onmessage = (e) => dispatch(JSON.parse(e.data));
    ws.onclose = () => dispatch({ type: "closed" });
    return () => ws.close();
  }, [dispatch]);

  return (msg) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) wsRef.current.send(JSON.stringify(msg));
  };
}

function Countdown({ deadline }) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 250);
    return () => clearInterval(id);
  }, []);
  if (!deadline) return null;
  const seconds = Math.max(0, Math.ceil((deadline - now) / 1000));
  return <span className="timer">{seconds}s</span>;
}

const you = (player, me) => (player === me ? " (you)" : "");

function Chat({ log, me, canSend, onSend }) {
  const [text, setText] = useState("");
  const endRef = useRef(null);
  useEffect(() => endRef.current?.scrollIntoView({ behavior: "smooth" }), [log.length]);

  const submit = (e) => {
    e.preventDefault();
    if (text.trim()) {
      onSend(text.trim());
      setText("");
    }
  };

  return (
    <div className="chat">
      <div className="messages">
        {log.map((m, i) =>
          m.system ? (
            <div key={i} className="system">{m.text}</div>
          ) : (
            <div key={i} className={m.from === me ? "msg mine" : "msg"}>
              <b>{m.from}{you(m.from, me)}:</b> {m.text}
            </div>
          )
        )}
        <div ref={endRef} />
      </div>
      <form onSubmit={submit}>
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={!canSend}
          maxLength={500}
          placeholder={canSend ? "Type a message…" : "Chat is closed during this phase"}
        />
        <button disabled={!canSend || !text.trim()}>Send</button>
      </form>
    </div>
  );
}

export default function App() {
  const [s, dispatch] = useReducer(reducer, initialState);
  const send = useExperimentSocket(dispatch);

  if (s.phase === "results" && s.result) {
    const { winner, reason, tallies } = s.result;
    return (
      <div className="screen">
        <h2>The group has chosen its Decision Maker</h2>
        <div className="winner">{winner}{you(winner, s.me)}</div>
        <p className="task">Decided by: {reason}</p>
        <table>
          <thead>
            <tr>
              <th>Participant</th>
              {tallies.map((_, i) => <th key={i}>Round {i + 1}</th>)}
            </tr>
          </thead>
          <tbody>
            {s.players.map((p) => (
              <tr key={p}>
                <td>{p}{you(p, s.me)}</td>
                {tallies.map((t, i) => <td key={i}>{t[p]}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
        <p>Thank you for participating!</p>
      </div>
    );
  }

  if (s.status === "closed") {
    return (
      <div className="screen">
        <h2>Connection lost</h2>
        <p>Please reload the page.</p>
      </div>
    );
  }

  if (!s.phase || s.phase === "waiting") {
    return (
      <div className="screen">
        <h2>Waiting for other participants…</h2>
        <p className="task">The study will start automatically once everyone has joined.</p>
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div className="app">
      <header>
        <span>You are <b>{s.me}</b></span>
        <span>Round {s.round} of {s.totalRounds} · {PHASE_LABEL[s.phase]}</span>
        <Countdown deadline={s.deadline} />
      </header>

      <p className="task">
        Discuss with the other participants and decide who should be the <b>Decision Maker</b> for the next study.
      </p>

      {s.phase === "voting" && (
        <div className="panel">
          <h3>Vote for the Decision Maker</h3>
          {s.myVote ? (
            <p>You voted for <b>{s.myVote}</b>. Waiting for the others…</p>
          ) : (
            <div className="vote-buttons">
              {s.players.map((p) => (
                <button key={p} onClick={() => send({ type: "vote", target: p })}>
                  {p}{you(p, s.me)}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {s.phase === "feedback" && s.tally && (
        <div className="panel">
          <h3>Round {s.round} votes</h3>
          <ul className="tally">
            {Object.entries(s.tally).map(([p, n]) => (
              <li key={p}>{p}{you(p, s.me)}: {n} vote{n === 1 ? "" : "s"}</li>
            ))}
          </ul>
          <p>The next discussion round starts shortly.</p>
        </div>
      )}

      <Chat
        log={s.log}
        me={s.me}
        canSend={s.phase === "discussion"}
        onSend={(text) => send({ type: "chat", text })}
      />
    </div>
  );
}