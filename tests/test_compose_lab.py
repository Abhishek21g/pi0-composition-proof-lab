from __future__ import annotations

import json
from pathlib import Path

import pytest

from pi0_compose.doctor import all_passed, doctor_receipt
from pi0_compose.io_utils import load_episodes, load_skills, read_receipt
from pi0_compose.manifest_search import score_episode_for_skill, search_manifest, tangential_episode_ids
from pi0_compose.models import DoctorResult, Episode, Receipt, Skill, SkillMatch, Verdict
from pi0_compose.remix_detector import choose_verdict, coaching_required, embodiment_gap, remix_score
from pi0_compose.runner import build_plan, run_plan
from pi0_compose.skill_graph import decompose_task, tokenize


EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


@pytest.fixture
def skills() -> list[Skill]:
    return load_skills(EXAMPLES / "pi07_airfryer_skills.yaml")


@pytest.fixture
def episodes() -> list[Episode]:
    return load_episodes(EXAMPLES / "bundled_episodes.jsonl")


def test_tokenize_normalizes_words():
    assert "air" in tokenize("Load a sweet potato into the Air Fryer!")


def test_decompose_task_selects_airfryer_skills(skills):
    selected = decompose_task("load a sweet potato into the air fryer", skills)
    ids = {s.id for s in selected}
    assert "operate_appliance" in ids
    assert "place_in_container" in ids


def test_decompose_task_falls_back_to_all_skills(skills):
    selected = decompose_task("xyz unknown task", skills)
    assert len(selected) == len(skills)


def test_score_episode_exact_skill_match(skills, episodes):
    skill = next(s for s in skills if s.id == "close_container")
    ep = next(e for e in episodes if e.episode_id == "home_airfryer_close_01")
    assert score_episode_for_skill(skill, ep) == 1.0


def test_score_episode_partial_overlap(skills, episodes):
    skill = Skill(id="pick_object", label="pick up object", keywords=["pick", "grab"])
    ep = episodes[0]
    assert score_episode_for_skill(skill, ep) >= 0.0


def test_search_manifest_returns_matches(skills, episodes):
    task_skills = decompose_task("load sweet potato into air fryer", skills)
    matches = search_manifest(task_skills, episodes)
    assert matches
    assert any(m.episode_id.startswith("home_airfryer") for m in matches)


def test_tangential_episode_ids_sorted(episodes, skills):
    matches = search_manifest(skills, episodes)
    tangential = tangential_episode_ids(matches)
    assert tangential
    assert tangential[0] in {m.episode_id for m in matches}


def test_embodiment_gap_for_new_robot(episodes, skills):
    matches = search_manifest(skills[:2], episodes)
    gap = embodiment_gap("ur5e_bimanual", episodes, matches)
    assert gap > 0.0


def test_embodiment_gap_zero_when_same_robot(episodes, skills):
    appliance_skills = [s for s in skills if s.id in {"close_container", "operate_appliance"}]
    matches = search_manifest(appliance_skills, episodes)
    gap = embodiment_gap("mobile_manipulator", episodes, matches)
    assert gap == 0.0


def test_remix_score_increases_with_tangential(skills):
    matches = [
        SkillMatch("close_container", "home_airfryer_close_01", 1.0, "push basket", "mobile_manipulator"),
        SkillMatch("operate_appliance", "home_airfryer_close_02", 0.8, "basket on counter", "mobile_manipulator"),
    ]
    score = remix_score(skills[:3], matches, ["home_airfryer_close_01", "home_airfryer_close_02"])
    assert score >= 0.4


def test_coaching_required_for_airfryer_task():
    assert coaching_required("load a sweet potato into the air fryer", remix=0.5, embodiment=0.0)


def test_coaching_not_required_for_low_remix():
    assert not coaching_required("pick up a towel", remix=0.1, embodiment=0.0)


def test_choose_verdict_remix():
    verdict = choose_verdict(remix=0.6, retrieve_hits=0, coaching=False, skill_coverage=0.7)
    assert verdict == Verdict.REMIX


def test_choose_verdict_compose():
    verdict = choose_verdict(remix=0.1, retrieve_hits=0, coaching=False, skill_coverage=0.9)
    assert verdict == Verdict.COMPOSE


def test_choose_verdict_coach_required():
    verdict = choose_verdict(remix=0.5, retrieve_hits=0, coaching=True, skill_coverage=0.7)
    assert verdict == Verdict.COACH_REQUIRED


def test_choose_verdict_retrieve():
    verdict = choose_verdict(remix=0.9, retrieve_hits=3, coaching=False, skill_coverage=0.9)
    assert verdict == Verdict.RETRIEVE


def test_airfryer_run_receipt_is_remix_or_coach(skills, episodes):
    plan = build_plan(
        task="load a sweet potato into the air fryer",
        skills=skills,
        episodes=episodes,
        eval_robot="mobile_manipulator",
    )
    receipt = run_plan(plan, mock=True)
    assert receipt.verdict in {Verdict.REMIX, Verdict.COACH_REQUIRED, Verdict.RETRIEVE}
    assert receipt.coaching_required
    assert "home_airfryer_close_01" in receipt.tangential_episodes


def test_receipt_has_doctor_gates(skills, episodes):
    plan = build_plan(task="load a sweet potato into the air fryer", skills=skills, episodes=episodes)
    receipt = run_plan(plan)
    names = {d.name for d in receipt.doctors}
    assert {"skill_graph", "manifest_search", "remix_detector", "coaching_oracle"} <= names


def test_doctor_receipt_adds_checks(skills, episodes):
    receipt = run_plan(build_plan(task="load a sweet potato into the air fryer", skills=skills, episodes=episodes))
    results = doctor_receipt(receipt)
    assert any(r.name == "evidence_present" for r in results)


def test_all_passed_false_when_gate_fails():
    results = [DoctorResult("x", False, 0.0, "fail")]
    assert not all_passed(results)


def test_load_examples_roundtrip(skills, episodes):
    assert len(skills) >= 5
    assert len(episodes) >= 6


def test_receipt_json_roundtrip(skills, episodes, tmp_path):
    receipt = run_plan(build_plan(task="load a sweet potato into the air fryer", skills=skills, episodes=episodes))
    path = tmp_path / "receipt.json"
    path.write_text(json.dumps(receipt.to_dict()))
    loaded = read_receipt(path)
    assert loaded.verdict == receipt.verdict
    assert loaded.tangential_episodes == receipt.tangential_episodes


def test_cli_end_to_end(tmp_path, skills, episodes):
    from pi0_compose.cli import main

    out = tmp_path / "out"
    plan_code = main(
        [
            "plan",
            "--task",
            "load a sweet potato into the air fryer",
            "--skills",
            str(EXAMPLES / "pi07_airfryer_skills.yaml"),
            "--manifest",
            str(EXAMPLES / "bundled_episodes.jsonl"),
            "--out",
            str(out),
            "--json",
        ]
    )
    assert plan_code == 0

    plans = list((out / "plans").iterdir())
    plan_dir = plans[0]
    run_code = main(["run", "--plan", str(plan_dir), "--out", str(out), "--json"])
    assert run_code == 0

    receipts = list((out / "receipts").iterdir())
    receipt_dir = receipts[0]
    doctor_code = main(["doctor", "--receipt", str(receipt_dir), "--json"])
    assert doctor_code in {0, 1}

    report_code = main(["report", "--receipt", str(receipt_dir), "--html"])
    assert report_code == 0
    assert (receipt_dir / "report.html").exists()
