# π0 Composition Proof Lab

Falsify compositional generalization claims for π0-style VLAs **before** betting a real robot demo.

Physical Intelligence's π0.7 work shows the hard part is not inference latency — it is proving whether a novel task is **true skill composition** or **dataset remix** (tangential episodes + coaching). This lab automates that postmortem.

## Quick start

```bash
pip install -e ".[dev]"

pi0-compose plan \
  --task "load a sweet potato into the air fryer" \
  --skills examples/pi07_airfryer_skills.yaml \
  --manifest examples/bundled_episodes.jsonl \
  --json

pi0-compose run --plan out/plans/<run-id> --mock
pi0-compose doctor --receipt out/receipts/<run-id>/
pi0-compose report --receipt out/receipts/<run-id>/ --html
```

## Verdicts

| Verdict | Meaning |
|---------|---------|
| `COMPOSE` | Primitive skills covered; low tangential remix risk |
| `REMIX` | Tangential training episodes likely explain the behavior |
| `RETRIEVE` | Near-duplicate demonstrations dominate |
| `COACH_REQUIRED` | Step-by-step language coaching needed (π0.7 air fryer pattern) |
| `NO-GO` | Insufficient skill/manifest support for zero-shot claims |

## Why this exists

π0.7's air fryer demo required manually searching the training manifest for tangential episodes. This tool makes that falsification step explicit and receipt-shaped — independent of any single openpi PR.

## Tests

```bash
pytest -q
```

## Demo site

Static demo: `site/index.html` · target publish: `enaguthi.com/pi0-composition-proof/site/`

## Related upstream work

Separate track: [openpi#983](https://github.com/Physical-Intelligence/openpi/issues/983) GPU timing fix (inference correctness, not generalization eval).
