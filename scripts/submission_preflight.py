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
    "docs/judge-video.html",
    "docs/judge-video-manifest.json",
    "docs/listinglens-judge-video.mp4",
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
def check_judge_video() -> dict:
    manifest_path = ROOT / "docs/judge-video-manifest.json"
    video_path = ROOT / "docs/listinglens-judge-video.mp4"
    if not manifest_path.exists() or not video_path.exists():
        return {"ok": False, "error": "judge video or manifest missing"}
    try:
        manifest = json.loads(manifest_path.read_text())
        video = manifest.get("video") or {}
        expected_sha = manifest.get("sha256")
        import hashlib
        actual_sha = hashlib.sha256(video_path.read_bytes()).hexdigest()
        duration = float(manifest.get("duration_seconds", 0))
        ok = (
            expected_sha == actual_sha
            and manifest.get("bytes") == video_path.stat().st_size
            and 1 <= duration <= 300
            and video.get("codec_name") == "h264"
            and video.get("width") == 1920
            and video.get("height") == 1080
            and video.get("r_frame_rate") == "30/1"
        )
        return {
            "ok": ok,
            "duration_seconds": duration,
            "bytes": video_path.stat().st_size,
            "sha256": actual_sha,
            "codec": video.get("codec_name"),
            "resolution": f"{video.get('width')}x{video.get('height')}",
            "fps": video.get("r_frame_rate"),
            "public_url": DEMO_URL + "judge-video.html",
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


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
        "judge_video": check_judge_video(),
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
    if not checks["judge_video"]["ok"]:
        blockers.append("judge_video_invalid")
    if args.network and not checks["public_demo"]["ok"]:
        blockers.append("public_demo_unreachable")

    # Final-submission gates that still require external evidence/actions.
    blockers.extend(
        [
            "real_aws_deployment_evidence_pending",
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
