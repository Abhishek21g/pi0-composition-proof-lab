from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Verdict(str, Enum):
    COMPOSE = "COMPOSE"
    REMIX = "REMIX"
    RETRIEVE = "RETRIEVE"
    COACH_REQUIRED = "COACH_REQUIRED"
    NO_GO = "NO-GO"


@dataclass
class Skill:
    id: str
    label: str
    keywords: list[str] = field(default_factory=list)


@dataclass
class Episode:
    episode_id: str
    instruction: str
    robot: str
    scene: str
    skills: list[str] = field(default_factory=list)
    objects: list[str] = field(default_factory=list)


@dataclass
class SkillMatch:
    skill_id: str
    episode_id: str
    score: float
    instruction: str
    robot: str


@dataclass
class DoctorResult:
    name: str
    passed: bool
    score: float
    detail: str


@dataclass
class Plan:
    run_id: str
    task: str
    skills: list[Skill]
    episodes: list[Episode]
    eval_robot: str
    source_robot: str | None = None


@dataclass
class Receipt:
    run_id: str
    task: str
    verdict: Verdict
    coaching_required: bool
    skill_matches: list[SkillMatch]
    tangential_episodes: list[str]
    doctors: list[DoctorResult]
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["verdict"] = self.verdict.value
        return data
