from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pi0_compose.doctor import all_passed, load_and_doctor
from pi0_compose.report import render_html, render_markdown
from pi0_compose.io_utils import load_episodes, load_skills, read_receipt
from pi0_compose.runner import build_plan, persist_plan, persist_receipt, run_plan


def _default_out() -> Path:
    return Path("out")


def cmd_plan(args: argparse.Namespace) -> int:
    skills = load_skills(Path(args.skills))
    episodes = load_episodes(Path(args.manifest))
    plan = build_plan(
        task=args.task,
        skills=skills,
        episodes=episodes,
        eval_robot=args.eval_robot,
        source_robot=args.source_robot,
    )
    plan_dir = persist_plan(plan, Path(args.out))
    payload = {
        "run_id": plan.run_id,
        "plan_dir": str(plan_dir),
        "task": plan.task,
        "skills": [s.id for s in plan.skills],
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"plan written: {plan_dir}")
        print(f"run_id: {plan.run_id}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    plan_path = Path(args.plan)
    manifest = plan_path / "manifest.json" if plan_path.is_dir() else plan_path
    data = json.loads(manifest.read_text())

    skills_path = Path(args.skills) if args.skills else Path("examples/pi07_airfryer_skills.yaml")
    manifest_path = Path(args.manifest) if args.manifest else Path("examples/bundled_episodes.jsonl")

    plan = build_plan(
        task=data["task"],
        skills=load_skills(skills_path),
        episodes=load_episodes(manifest_path),
        eval_robot=data.get("eval_robot", "mobile_manipulator"),
        source_robot=data.get("source_robot"),
        run_id=data["run_id"],
    )
    receipt = run_plan(plan, mock=args.mock)
    receipt_dir = persist_receipt(receipt, Path(args.out))

    payload = {
        "run_id": receipt.run_id,
        "receipt_dir": str(receipt_dir),
        "verdict": receipt.verdict.value,
        "coaching_required": receipt.coaching_required,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"receipt written: {receipt_dir}")
        print(f"verdict: {receipt.verdict.value}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    receipt_dir = Path(args.receipt)
    results = load_and_doctor(receipt_dir)
    payload = {
        "passed": all_passed(results),
        "doctors": [
            {"name": r.name, "passed": r.passed, "score": r.score, "detail": r.detail}
            for r in results
        ],
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        for r in results:
            status = "PASS" if r.passed else "FAIL"
            print(f"[{status}] {r.name}: {r.detail}")
        print(f"overall: {'PASS' if payload['passed'] else 'FAIL'}")
    return 0 if payload["passed"] else 1


def cmd_report(args: argparse.Namespace) -> int:
    receipt_dir = Path(args.receipt)
    receipt = read_receipt(receipt_dir / "receipt.json")
    results = load_and_doctor(receipt_dir)

    if args.html:
        content = render_html(receipt, results)
        out = receipt_dir / "report.html"
    else:
        content = render_markdown(receipt, results)
        out = receipt_dir / "report.md"

    out.write_text(content)
    if args.json:
        print(json.dumps({"report": str(out), "verdict": receipt.verdict.value}, indent=2))
    else:
        print(f"report written: {out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pi0-compose", description="π0 Composition Proof Lab")
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan", help="decompose task and write plan manifest")
    plan.add_argument("--task", required=True)
    plan.add_argument("--skills", required=True)
    plan.add_argument("--manifest", required=True)
    plan.add_argument("--eval-robot", default="mobile_manipulator")
    plan.add_argument("--source-robot", default=None)
    plan.add_argument("--out", default=str(_default_out()))
    plan.add_argument("--json", action="store_true")
    plan.set_defaults(func=cmd_plan)

    run = sub.add_parser("run", help="search manifest and write receipt")
    run.add_argument("--plan", required=True)
    run.add_argument("--skills", default=None)
    run.add_argument("--manifest", default=None)
    run.add_argument("--mock", action=argparse.BooleanOptionalAction, default=True)
    run.add_argument("--out", default=str(_default_out()))
    run.add_argument("--json", action="store_true")
    run.set_defaults(func=cmd_run)

    doctor = sub.add_parser("doctor", help="validate a receipt")
    doctor.add_argument("--receipt", required=True)
    doctor.add_argument("--json", action="store_true")
    doctor.set_defaults(func=cmd_doctor)

    report = sub.add_parser("report", help="render markdown or html report")
    report.add_argument("--receipt", required=True)
    report.add_argument("--html", action="store_true")
    report.add_argument("--json", action="store_true")
    report.set_defaults(func=cmd_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
