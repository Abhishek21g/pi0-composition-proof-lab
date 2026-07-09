from __future__ import annotations

from pathlib import Path

from pi0_compose.io_utils import new_run_id, write_plan, write_receipt
from pi0_compose.manifest_search import search_manifest, tangential_episode_ids
from pi0_compose.models import DoctorResult, Plan, Receipt, Skill
from pi0_compose.remix_detector import (
    choose_verdict,
    coaching_required,
    embodiment_gap,
    remix_score,
)
from pi0_compose.skill_graph import decompose_task, tokenize


def instruction_similarity(task: str, instruction: str) -> float:
    task_tokens = tokenize(task)
    inst_tokens = tokenize(instruction)
    if not task_tokens:
        return 0.0
    return len(task_tokens & inst_tokens) / len(task_tokens)


def build_plan(
    *,
    task: str,
    skills: list[Skill],
    episodes: list,
    eval_robot: str = "mobile_manipulator",
    source_robot: str | None = None,
    run_id: str | None = None,
) -> Plan:
    return Plan(
        run_id=run_id or new_run_id(),
        task=task,
        skills=decompose_task(task, skills),
        episodes=episodes,
        eval_robot=eval_robot,
        source_robot=source_robot,
    )


def run_plan(plan: Plan, *, mock: bool = True) -> Receipt:
    del mock  # reserved for future live manifest backends

    matches = search_manifest(plan.skills, plan.episodes)
    tangential = tangential_episode_ids(matches)
    remix = remix_score(plan.skills, matches, tangential)
    embodiment = embodiment_gap(plan.eval_robot, plan.episodes, matches)
    covered = len({m.skill_id for m in matches if m.score >= 0.2})
    skill_coverage = covered / max(len(plan.skills), 1)
    retrieve_hits = sum(
        1
        for m in matches
        if instruction_similarity(plan.task, m.instruction) >= 0.55
    )
    coaching = coaching_required(plan.task, remix, embodiment)
    verdict = choose_verdict(
        remix=remix,
        retrieve_hits=retrieve_hits,
        coaching=coaching,
        skill_coverage=skill_coverage,
    )

    doctors = [
        DoctorResult(
            name="skill_graph",
            passed=skill_coverage >= 0.5,
            score=round(skill_coverage, 3),
            detail=f"{covered}/{len(plan.skills)} task skills have manifest support",
        ),
        DoctorResult(
            name="manifest_search",
            passed=len(matches) > 0,
            score=round(min(1.0, len(matches) / max(len(plan.skills), 1)), 3),
            detail=f"{len(matches)} skill→episode matches",
        ),
        DoctorResult(
            name="remix_detector",
            passed=remix < 0.75,
            score=round(remix, 3),
            detail="high remix means tangential training evidence dominates",
        ),
        DoctorResult(
            name="embodiment_gap",
            passed=embodiment < 0.5,
            score=round(embodiment, 3),
            detail=f"eval robot={plan.eval_robot}",
        ),
        DoctorResult(
            name="coaching_oracle",
            passed=not coaching,
            score=1.0 if coaching else 0.0,
            detail="step-by-step language coaching likely required" if coaching else "zero-shot may be viable",
        ),
    ]

    notes = [
        "mock mode: heuristic manifest search only",
        f"tangential episodes: {', '.join(tangential) if tangential else 'none'}",
    ]

    return Receipt(
        run_id=plan.run_id,
        task=plan.task,
        verdict=verdict,
        coaching_required=coaching,
        skill_matches=matches,
        tangential_episodes=tangential,
        doctors=doctors,
        notes=notes,
    )


def persist_plan(plan: Plan, root: Path) -> Path:
    plan_dir = root / "plans" / plan.run_id
    write_plan(plan_dir / "manifest.json", plan)
    return plan_dir


def persist_receipt(receipt: Receipt, root: Path) -> Path:
    receipt_dir = root / "receipts" / receipt.run_id
    write_receipt(receipt_dir / "receipt.json", receipt)
    return receipt_dir
