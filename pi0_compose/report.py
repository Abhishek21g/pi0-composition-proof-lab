from __future__ import annotations

from pi0_compose.models import DoctorResult, Receipt


def render_markdown(receipt: Receipt, doctor_results: list[DoctorResult] | None = None) -> str:
    doctor_results = doctor_results or receipt.doctors
    doctor_rows = "\n".join(
        f"| {d.name} | {'PASS' if d.passed else 'FAIL'} | {d.score:.2f} | {d.detail} |"
        for d in doctor_results
    )
    match_rows = "\n".join(
        f"| {m.skill_id} | {m.episode_id} | {m.score:.2f} | {m.robot} | {m.instruction} |"
        for m in receipt.skill_matches[:12]
    )
    if not match_rows:
        match_rows = "| _none_ | _n/a_ | _n/a_ | _n/a_ | _n/a_ |"

    tangential = ", ".join(receipt.tangential_episodes) or "none"
    notes = "\n".join(f"- {n}" for n in receipt.notes)

    return f"""# π0 Composition Proof Receipt

**Task:** {receipt.task}

**Verdict:** `{receipt.verdict.value}`

**Coaching required:** `{receipt.coaching_required}`

**Run ID:** `{receipt.run_id}`

## Tangential episodes

{tangential}

## Doctor gates

| Gate | Status | Score | Detail |
| --- | --- | --- | --- |
{doctor_rows}

## Top manifest matches

| Skill | Episode | Score | Robot | Instruction |
| --- | --- | --- | --- | --- |
{match_rows}

## Notes

{notes}
"""


def render_html(receipt: Receipt, doctor_results: list[DoctorResult] | None = None) -> str:
    body = render_markdown(receipt, doctor_results)
    escaped = (
        body.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>π0 Composition Proof — {receipt.run_id}</title>
  <style>
    body {{ font-family: ui-sans-serif, system-ui, sans-serif; max-width: 920px; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }}
    pre {{ white-space: pre-wrap; background: #0f172a; color: #e2e8f0; padding: 1rem; border-radius: 8px; }}
    h1 {{ letter-spacing: -0.02em; }}
  </style>
</head>
<body>
  <h1>π0 Composition Proof Lab</h1>
  <p>Verdict: <strong>{receipt.verdict.value}</strong> · coaching_required={receipt.coaching_required}</p>
  <pre>{escaped}</pre>
</body>
</html>
"""
