import random


def choose_vote(me: str, labels: list[str], previous_tally: dict[str, int] | None) -> str:
    """Round 1: vote for someone else at random. Later rounds: back the previous leader."""
    if previous_tally:
        top = max(previous_tally.values())
        leaders = [label for label in labels if previous_tally[label] == top]
        return random.choice(leaders)
    return random.choice([label for label in labels if label != me])