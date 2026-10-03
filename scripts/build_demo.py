from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agent import run_agent
from src.synthetic import write_suite
DOCS = ROOT / "docs"
ASSETS = DOCS / "demo-assets"
GENERATED = ROOT / "samples" / "generated-demo"


def clean_result(name: str, result: dict) -> dict:
    final = result["final"]
    return {
        "case": name,
        "decision": final["decision"],
        "reason_codes": final["reason_codes"],
        "before": final["before"],
        "after": final["after"],
        "trace": result["trace"],
        "input_image": f"demo-assets/{name}-before.png",
        "corrected_image": (
            f"demo-assets/{name}-after.png"
            if final.get("corrected_image")
            else None
        ),
        "opencv_version": result["opencv_version"],
    }
def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    cases = write_suite(GENERATED)
    payload = {
        "product": "ListingLens Agent",
        "generated_from": "scripts/build_demo.py",
        "cases": {},
    }

    for name, source in cases.items():
        before_public = ASSETS / f"{name}-before.png"
        shutil.copy2(source, before_public)
        result = run_agent(source, ASSETS / "_agent-output")
        corrected = result["final"].get("corrected_image")
        if corrected:
            shutil.copy2(corrected, ASSETS / f"{name}-after.png")
        payload["cases"][name] = clean_result(name, result)

    shutil.rmtree(ASSETS / "_agent-output", ignore_errors=True)
    (DOCS / "demo-data.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    summary = {
        name: case["decision"]
        for name, case in payload["cases"].items()
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
