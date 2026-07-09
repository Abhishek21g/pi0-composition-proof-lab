from __future__ import annotations

from pi0_compose.models import Episode, Skill, SkillMatch
from pi0_compose.skill_graph import tokenize


def _episode_tokens(episode: Episode) -> set[str]:
    tokens = tokenize(episode.instruction)
    for obj in episode.objects:
        tokens |= tokenize(obj)
    for skill in episode.skills:
        tokens |= tokenize(skill)
    return tokens


def _skill_tokens(skill: Skill) -> set[str]:
    tokens = tokenize(skill.label)
    for kw in skill.keywords:
        tokens |= tokenize(kw)
    return tokens


def score_episode_for_skill(skill: Skill, episode: Episode) -> float:
    if skill.id in episode.skills:
        return 1.0

    overlap = _skill_tokens(skill) & _episode_tokens(episode)
    if not overlap:
        return 0.0

    union = _skill_tokens(skill) | _episode_tokens(episode)
    return len(overlap) / max(len(union), 1)


def search_manifest(
    skills: list[Skill],
    episodes: list[Episode],
    *,
    top_k: int = 3,
    min_score: float = 0.08,
) -> list[SkillMatch]:
    matches: list[SkillMatch] = []
    for skill in skills:
        ranked = sorted(
            ((score_episode_for_skill(skill, ep), ep) for ep in episodes),
            key=lambda pair: pair[0],
            reverse=True,
        )
        for score, episode in ranked[:top_k]:
            if score < min_score:
                continue
            matches.append(
                SkillMatch(
                    skill_id=skill.id,
                    episode_id=episode.episode_id,
                    score=round(score, 3),
                    instruction=episode.instruction,
                    robot=episode.robot,
                )
            )
    return matches


def tangential_episode_ids(matches: list[SkillMatch], *, threshold: float = 0.2) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for match in sorted(matches, key=lambda m: m.score, reverse=True):
        if match.score < threshold:
            continue
        if match.episode_id in seen:
            continue
        seen.add(match.episode_id)
        ordered.append(match.episode_id)
    return ordered
