from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

import yaml

from pi0_compose.models import Episode, Plan, Receipt, Skill


def new_run_id() -> str:
    return uuid.uuid4().hex[:12]


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:48] or "run"


def load_skills(path: Path) -> list[Skill]:
    raw = yaml.safe_load(path.read_text())
    return [
        Skill(
            id=item["id"],
            label=item["label"],
            keywords=list(item.get("keywords", [])),
        )
        for item in raw["skills"]
    ]


def load_episodes(path: Path) -> list[Episode]:
    episodes: list[Episode] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        episodes.append(
            Episode(
                episode_id=row["episode_id"],
                instruction=row["instruction"],
                robot=row["robot"],
                scene=row.get("scene", "unknown"),
                skills=list(row.get("skills", [])),
                objects=list(row.get("objects", [])),
            )
        )
    return episodes


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))


def write_plan(path: Path, plan: Plan) -> None:
    payload = {
        "run_id": plan.run_id,
        "task": plan.task,
        "eval_robot": plan.eval_robot,
        "source_robot": plan.source_robot,
        "skills": [
            {"id": s.id, "label": s.label, "keywords": s.keywords}
            for s in plan.skills
        ],
        "episode_count": len(plan.episodes),
    }
    write_json(path, payload)


def write_receipt(path: Path, receipt: Receipt) -> None:
    write_json(path, receipt.to_dict())


def read_receipt(path: Path) -> Receipt:
    from pi0_compose.models import DoctorResult, SkillMatch, Verdict

    data = json.loads(path.read_text())
    return Receipt(
        run_id=data["run_id"],
        task=data["task"],
        verdict=Verdict(data["verdict"]),
        coaching_required=data["coaching_required"],
        skill_matches=[SkillMatch(**m) for m in data["skill_matches"]],
        tangential_episodes=list(data["tangential_episodes"]),
        doctors=[DoctorResult(**d) for d in data["doctors"]],
        notes=list(data.get("notes", [])),
    )
