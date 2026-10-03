from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEMO_URL = "https://williamleewilliam1-star.github.io/babydov-listinglens-agent/"

REQUIRED = [
    "LICENSE",
    "README.md",
    "requirements.txt",
    "src/vision.py",
    "src/agent.py",
    "tests/test_agent.py",
    "tests/test_aws_lambda.py",
    "docs/ARCHITECTURE.md",
    "docs/TECHNICAL_REPORT.md",
    "docs/SYNTHETIC_LAB.md",
    "docs/index.html",
    "docs/demo-data.json",
    "aws/Dockerfile",
    "aws/template.yaml",
    "aws/lambda_handler.py",
]


def check_demo_data() -> dict:
    data = json.loads((ROOT / "docs/demo-data.json").read_text())
    cases = data["cases"]
    expected = {
        "good": "ACCEPT",
        "margin": "ACCEPT_AFTER_FIX",
        "blur": "HUMAN_RESHOOT",
        "dark": "HUMAN_RESHOOT",
        "bright": "HUMAN_RESHOOT",
    }
    mismatches = {
        name: {"expected": decision, "actual": cases.get(name, {}).get("decision")}
        for name, decision in expected.items()
        if cases.get(name, {}).get("decision") != decision
    }
    versions = sorted({c.get("opencv_version") for c in cases.values()})
    return {"case_count": len(cases), "mismatches": mismatches, "opencv_versions": versions}
def check_public_demo() -> dict:
    try:
        req = urllib.request.Request(DEMO_URL, headers={"User-Agent": "ListingLens-Preflight/1.0"})
        with urllib.request.urlopen(req, timeout=12) as response:
            text = response.read().decode("utf-8", "replace")
            return {
                "ok": response.status == 200 and "ListingLens Agent" in text,
                "status": response.status,
            }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--network", action="store_true")
    args = parser.parse_args()

    missing = [name for name in REQUIRED if not (ROOT / name).exists()]
    demo = check_demo_data()
    checks = {
        "required_files": {"ok": not missing, "missing": missing},
        "demo_evidence": {
            "ok": demo["case_count"] == 5
            and not demo["mismatches"]
            and demo["opencv_versions"] == ["5.0.0"],
            **demo,
        },
        "public_demo": (
            check_public_demo()
            if args.network
            else {"ok": None, "skipped": "run with --network"}
        ),
    }
    blockers = []
    if missing:
        blockers.append("required_files_missing")
    if not checks["demo_evidence"]["ok"]:
        blockers.append("demo_evidence_invalid")
    if args.network and not checks["public_demo"]["ok"]:
        blockers.append("public_demo_unreachable")

    # Final-submission gates that require external evidence, not code alone.
    blockers.extend(
        [
            "real_aws_deployment_evidence_pending",
            "judge_video_pending",
            "devpost_final_submission_pending",
        ]
    )

    payload = {
        "project": "ListingLens Agent",
        "demo_url": DEMO_URL,
        "checks": checks,
        "final_submission_ready": len(blockers) == 0,
        "blockers": blockers,
    }
    print(json.dumps(payload, indent=2))
    return 0 if all(
        c.get("ok") is not False
        for c in checks.values()
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
