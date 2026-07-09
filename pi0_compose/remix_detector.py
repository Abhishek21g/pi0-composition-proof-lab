from __future__ import annotations

from pi0_compose.models import Episode, Skill, SkillMatch, Verdict


def embodiment_gap(eval_robot: str, episodes: list[Episode], matches: list[SkillMatch]) -> float:
    if not matches:
        return 1.0
    matched_robots = {
        ep.robot
        for ep in episodes
        if ep.episode_id in {m.episode_id for m in matches}
    }
    if not matched_robots:
        return 1.0
    if eval_robot in matched_robots:
        return 0.0
    return 0.8


def remix_score(
    skills: list[Skill],
    matches: list[SkillMatch],
    tangential: list[str],
) -> float:
    if not skills:
        return 0.0
    covered_skills = {m.skill_id for m in matches if m.score >= 0.2}
    coverage = len(covered_skills) / len(skills)
    tangential_bonus = min(len(tangential), 3) * 0.12
    return min(1.0, coverage * 0.7 + tangential_bonus)


def coaching_required(task: str, remix: float, embodiment: float) -> bool:
    # Long-horizon appliance tasks with tangential evidence usually need step coaching.
    tokens = task.lower()
    appliance_task = any(word in tokens for word in ("air fryer", "oven", "appliance", "microwave"))
    if appliance_task and remix >= 0.35:
        return True
    if embodiment >= 0.5 and remix >= 0.25:
        return True
    return remix >= 0.55


def choose_verdict(
    *,
    remix: float,
    retrieve_hits: int,
    coaching: bool,
    skill_coverage: float,
) -> Verdict:
    if retrieve_hits >= 2 and remix >= 0.75:
        return Verdict.RETRIEVE
    if coaching and remix >= 0.3:
        return Verdict.COACH_REQUIRED
    if remix >= 0.45:
        return Verdict.REMIX
    if skill_coverage >= 0.8 and remix < 0.25:
        return Verdict.COMPOSE
    if skill_coverage < 0.4:
        return Verdict.NO_GO
    return Verdict.REMIX
