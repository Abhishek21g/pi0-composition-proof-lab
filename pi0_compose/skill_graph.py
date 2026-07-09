from __future__ import annotations

import re

from pi0_compose.models import Skill


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def decompose_task(task: str, skills: list[Skill]) -> list[Skill]:
    """Return skills whose keywords overlap the task text."""
    task_tokens = tokenize(task)
    selected: list[Skill] = []
    for skill in skills:
        keywords = tokenize(skill.label)
        for kw in skill.keywords:
            keywords |= tokenize(kw)
        if keywords & task_tokens:
            selected.append(skill)
    if not selected:
        return skills
    return selected
