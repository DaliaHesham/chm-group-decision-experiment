# AI Usage Log

- **Model:** Claude Opus 5.5 (`claude-opus-5-5`)
- **Tool:** Claude desktop app (claude.ai), one continuous conversation
- **Date:** 2026-11-16 (times are local, UTC+2)

All prompts are listed in order. Typed prompts are verbatim. Pasted terminal output,
pasted file contents, attachments and screenshots are noted in [brackets] rather than reproduced.

## How I worked with the AI

- I asked the AI to guide me **one step at a time** and not to continue until I said "done",
  so that I could run, check and understand each part before moving on.
- I made the design decisions (AI behavior, round feedback, tie-breaking, self-votes) from the
  options it proposed. I later decided to drop an untestable "LLM mode".
- Most of my prompts are **terminal output, screenshots and file contents**, used to verify each
  step and debug problems together (e.g. a full disk making Docker's storage read-only, commands
  pasted onto one line, a config change not taking effect without a backend restart).
- From testing screenshots, I spotted that an AI participant said "Happy to do it" but voted for
  someone else; we fixed it so AI votes stay consistent with what it says.

---

## Prompts

### 1 (08:54)
[Attached: the job posting text]

### 2
ive already applied and they've sent me this
[pasted the invitation email for the technical assessment]

### 3
[Attached: technical-assessment-multi-participant-human-ai-experiment-platform-v4.md]

### 4
can they see this chat between us?

### 5 (09:02)
tell me what to do step by step from receiving the email and don't go to the next step unless i say done

### 6 (09:03)
Open a terminal and run each of these:
which terminal vs or mac terminal

### 7 (09:07)
[pasted terminal output: git/docker/node/python version checks; docker not found]

### 8 (09:14)
[pasted terminal output: docker and docker compose versions, `docker run hello-world` still downloading]

### 9 (09:15)
[pasted terminal output: `docker run hello-world` succeeded]

### 10 (09:22)
Then in VS Code, go to File → Open Folder and then where is ~/projects/chm-group-decision-experiment

u mean the downloaded file from the email i recieved?

### 11 (09:27)
[pasted terminal output: git config user.name / user.email]

### 12 (09:30)
[pasted terminal output: first commit and push of ai_prompts.md, committed empty]

### 13 (09:32)
[pasted terminal output: second commit and push of ai_prompts.md]

### 14 (09:34)
add all prompt to the log  after we finish

### 15 (09:34)
done

### 16
[Answered multiple-choice design questions: AI agent = "Scripted + optional LLM"; after round 1 = "Show round 1 tally"; final vote = "Round 2; tie → round 1 → random"; self-votes = "Allow self-votes"]

### 17 (09:37)
done

### 18 (09:40)
[pasted terminal output: `docker compose up --build` failed with "read-only file system"]

### 19 (09:41)
[pasted terminal output: `df -h /`, only 565 MB free]

### 20 (09:42)
[pasted terminal output: `du -sh` of home folders]

### 21 (09:43)
[Attached: terminal output listing the largest caches and files in Downloads/Desktop]

### 22 (09:45)
[Attached: terminal output of the cache/installer deletion commands]

### 23 (09:45)
[pasted terminal output: `~/.cache` sizes and `df -h /`, 6.8 GB free]

### 24 (09:47)
[pasted terminal output: "failed to connect to the docker API", Docker Desktop not started yet]

### 25 (09:48)
its loading, 
i want to ask if we are using the file i downloaded from the email or still?

### 26 (09:49)
[Attached: terminal output of `docker compose up --build` succeeding, backend logged the loaded config]

### 27 (09:51)
[pasted terminal output: commit and push of the backend skeleton]

### 28 (09:56)
[pasted current contents of config.yml]

### 29 (10:00)
[Screenshot: browser console WebSocket test, full session ran but chat was sent during voting]

### 30 (10:03)
ws.send(JSON.stringify({type: "chat", text: "Hi, I think I'd be a good decision maker"}))

when i see what exactly

### 31 (10:05)
[Screenshot: browser console test with chat echo, vote_ack and results]

### 32 (10:07)
[pasted terminal output: psql query of the events table, paged]

### 33 (10:08)
[pasted terminal output: psql query of the latest events]

### 34 (10:09)
[pasted current contents of config.yml]

### 35 (10:10)
press Ctrl + C in the Docker terminal

### 36 (10:13)
done

### 37 (10:14)
mkdir -p frontend/src

in which terminal in vs code there is two

### 38 (10:15)
[pasted terminal output: `touch` command split over two lines, "Command not found"]

### 39 (10:18)
[pasted current contents of docker-compose.yml]

### 40 (10:21)
[Screenshot: frontend discussion screen with two tabs connected]

### 41 (10:23)
[Screenshot: frontend voting screen]

### 42 (10:23)
[Screenshot: frontend final results screen]

### 43 (10:25)
[pasted terminal output: commit and push of the frontend]

### 44 (10:27)
[pasted current contents of backend/app/config.py]

### 45 (10:27)
[pasted current contents of config.yml]

### 46 (10:28)
[pasted current contents of README.md]

### 47 (10:31)
[Screenshot: AI participants chatting; one AI replied when mentioned by name]

### 48 (10:31)
[Screenshots: round 2 chat with both AIs, and final results]

### 49 (10:34)
[pasted backend/app/ai_agent.py after adding the vote-consistency fix]

### 50 (10:34)
[pasted current contents of config.yml, test values]

### 51 (10:35)
done

### 52 (10:36)
[pasted current contents of config.yml]

### 53 (10:41)
[Screenshot: Test 1 (3 humans) results, some tabs did not vote in time]

### 54 (10:45)
[Screenshot: Test 1 results, 1–1–1 tie in both rounds → "tie broken randomly"]

### 55 (10:49)
after test 1 i opened directly two tabs for test 2

### 56 (10:49)
[pasted current contents of config.yml, still the Test 1 condition]

### 57 (10:50)
what to do for test 2 exactly

### 58 (10:53)
[Screenshot: Test 2 (2 humans + 1 AI) results]

### 59 (10:56)
[Screenshot: Test 3 (1 human + 2 AI) results]

### 60 (10:56)
[pasted terminal output: psql query showing one session per condition with winner and reason]

### 61 (10:58)
[pasted terminal output: `git status` clean, plus current config.yml]

### 62 (11:00)
i started 8:40 and finished 11

### 63 (11:00)
[pasted the README "Development" section]

### 64 (11:01)
done
