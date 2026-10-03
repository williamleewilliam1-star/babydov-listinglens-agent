# ListingLens Agent

ListingLens is an **OpenCV 5 agentic vision workflow** for product/catalog photography QA.

It does more than score an image. Vision evidence changes the next action:

1. OpenCV 5 measures the image.
2. A deterministic policy decides whether the frame is acceptable, automatically fixable, or requires a human.
3. Fixable composition issues trigger a bounded automatic crop.
4. OpenCV 5 analyzes the corrected image again.
5. The second measurement decides whether the result can be accepted.

That makes the vision model part of an observable perception → decision → action loop rather than a decorative analysis step.

## Decisions

- `ACCEPT` — image already satisfies the policy.
- `ACCEPT_AFTER_FIX` — OpenCV evidence triggered an auto-crop, and re-perception verified improvement.
- `HUMAN_REVIEW` — a bounded correction was attempted but still does not pass.
- `HUMAN_RESHOOT` — blur, severe exposure failure, missing object, or background uncertainty should not be silently fixed.
## OpenCV 5 evidence

Current signals:
- sharpness (variance of Laplacian)
- mean luminance
- shadow/highlight clipping
- border-background variation
- foreground bounding box
- object occupancy
- center offset

Every run returns an audit trace containing the OpenCV version, measurements, policy decision, action, optional corrected artifact, re-measurement, and final decision.

## Quick start

Requires Python 3.10+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
python listinglens.py --synthetic-suite
```

Analyze a real local image:

```bash
python listinglens.py /path/to/product-photo.jpg --output-dir artifacts
```
## Synthetic lab

The project includes deterministic image generation, so the agent can be tested without external assets.

| Input | Expected behavior |
| --- | --- |
| good | ACCEPT |
| too much margin + off-center | AUTO_CROP → re-perception → ACCEPT_AFTER_FIX |
| blur | HUMAN_RESHOOT |
| dark | HUMAN_RESHOOT |
| overexposed | HUMAN_RESHOOT |

See [docs/SYNTHETIC_LAB.md](docs/SYNTHETIC_LAB.md) for observed metrics and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the workflow diagram.

## Live evidence demo

Recorded OpenCV 5 evidence: https://williamleewilliam1-star.github.io/babydov-listinglens-agent/

The page is generated from the same agent core and shows the before/after image, measurements, decision, action, re-perception, and final decision. It is intentionally labeled recorded evidence; the final real AWS deployment is tracked separately.

## OpenCV AI Competition 2026

Target: **Agentic Vision Award**.

The entry is designed around the competition requirement that OpenCV 5 output materially changes a later decision/tool/action. ListingLens exposes that causality directly in its trace.

A deploy-ready AWS S3→Lambda→OpenCV→S3 component lives under `aws/`. The cloud contract is tested locally; real AWS deployment evidence is still pending credentials/account access and is not claimed as completed.

## License

MIT
