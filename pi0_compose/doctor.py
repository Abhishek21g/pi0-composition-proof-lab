from __future__ import annotations

from pathlib import Path

from pi0_compose.io_utils import read_receipt
from pi0_compose.models import DoctorResult, Receipt, Verdict


def doctor_receipt(receipt: Receipt) -> list[DoctorResult]:
    checks = list(receipt.doctors)
    checks.append(
        DoctorResult(
            name="verdict_consistency",
            passed=receipt.verdict != Verdict.NO_GO or receipt.coaching_required,
            score=1.0,
            detail=f"final verdict={receipt.verdict.value}",
        )
    )
    checks.append(
        DoctorResult(
            name="evidence_present",
            passed=bool(receipt.skill_matches),
            score=1.0 if receipt.skill_matches else 0.0,
            detail=f"{len(receipt.skill_matches)} manifest matches recorded",
        )
    )
    return checks


def load_and_doctor(receipt_dir: Path) -> list[DoctorResult]:
    receipt = read_receipt(receipt_dir / "receipt.json")
    return doctor_receipt(receipt)


def all_passed(results: list[DoctorResult]) -> bool:
    return all(r.passed for r in results)
