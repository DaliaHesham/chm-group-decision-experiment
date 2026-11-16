import os
from typing import Literal

import yaml
from pydantic import BaseModel, field_validator


class AIConfig(BaseModel):
    mode: Literal["scripted", "llm"] = "scripted"
    min_typing_delay_seconds: float = 3
    max_typing_delay_seconds: float = 9


class ExperimentConfig(BaseModel):
    participants: list[Literal["human", "ai"]]
    rounds: int = 2
    discussion_seconds: int = 60
    voting_seconds: int = 20
    feedback_seconds: int = 8
    ai: AIConfig = AIConfig()

    @field_validator("participants")
    @classmethod
    def three_participants_with_a_human(cls, v):
        if len(v) != 3:
            raise ValueError("exactly 3 participants are required")
        if "human" not in v:
            raise ValueError("at least one participant must be human")
        return v

    @property
    def human_slots(self) -> int:
        return self.participants.count("human")


def load_config(path: str | None = None) -> ExperimentConfig:
    path = path or os.getenv("CONFIG_PATH", "config.yml")
    with open(path) as f:
        return ExperimentConfig(**yaml.safe_load(f))