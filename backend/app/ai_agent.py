import asyncio
import random
import time

OPENERS = [
    "Hi everyone! How do you want to decide this?",
    "Hey all, maybe we each say why we'd be a good pick?",
    "Hello :) I don't mind who it is, as long as they take it seriously.",
    "Hi! Has anyone done something like this before?",
]
SUPPORT = [
    "{name} sounds like a good choice to me.",
    "I'd be fine with {name} doing it.",
    "Honestly I'd go with {name}.",
    "What do you think about {name}? Seems reasonable to me.",
]
SELF_PITCH = [
    "I'm usually pretty careful with decisions, so I could do it.",
    "I'd be ok taking the role, I like thinking things through.",
]
ROUND_TWO = [
    "Looks like {name} got the most votes last round, I'm ok with that.",
    "Should we just go with {name}? Seems like the group leans that way.",
    "I still think {name} is a reasonable pick.",
]
REPLY_MENTIONED = [
    "Thanks! Happy to do it, but I'm also fine with someone else.",
    "Haha sure, if the group agrees.",
]


def pick(session, options: list[str]) -> str:
    """Pick a line not yet used in this session, so two AIs never repeat each other."""
    fresh = [o for o in options if o not in session.used_lines]
    line = random.choice(fresh or options)
    session.used_lines.add(line)
    return line


class ScriptedAgent:
    """Rule-based participant: a few human-paced messages per round, votes consistently with what it says."""

    def __init__(self, label: str, labels: list[str], cfg):
        self.label = label
        self.labels = labels
        self.cfg = cfg
        self.favorite = random.choice([l for l in labels if l != label])

    def update_for_round(self, previous_tally: dict[str, int]):
        """After a round, back the leader unless our favorite is already among the leaders."""
        top = max(previous_tally.values())
        leaders = [l for l in self.labels if previous_tally[l] == top]
        if self.favorite not in leaders:
            self.favorite = random.choice(leaders)

    async def discuss(self, session, rnd: int, seconds: int):
        stop_at = time.monotonic() + seconds - 3
        for i in range(random.randint(2, 3)):
            delay = random.uniform(self.cfg.min_typing_delay_seconds, self.cfg.max_typing_delay_seconds)
            if i == 0:
                delay += random.uniform(2, 6)  # people take a moment before their first message
            await asyncio.sleep(delay)
            if time.monotonic() > stop_at:
                return
            await session.post_chat(self.label, self.compose(session, rnd, i))

    def compose(self, session, rnd: int, i: int) -> str:
        if self.was_mentioned(session, rnd):
            self.favorite = self.label  # it just accepted the role, so vote consistently
            return pick(session, REPLY_MENTIONED)
        if i == 0 and rnd == 1:
            return pick(session, OPENERS)
        return self.about_favorite(session, ROUND_TWO if i == 0 else SUPPORT)

    def about_favorite(self, session, templates: list[str]) -> str:
        if self.favorite == self.label:
            return pick(session, SELF_PITCH)
        return pick(session, templates).format(name=self.favorite)

    def was_mentioned(self, session, rnd: int) -> bool:
        """Did someone address me since my last message in this round?"""
        for r, sender, text in reversed(session.chat):
            if r != rnd or sender == self.label:
                break
            if self.label.lower() in text.lower():
                return True
        return False