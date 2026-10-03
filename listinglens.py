#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.agent import run_agent
from src.synthetic import write_suite


def main() -> int:
    parser = argparse.ArgumentParser(description="ListingLens OpenCV 5 agent")
    parser.add_argument("image", nargs="?", help="Path to a product image")
    parser.add_argument("--output-dir", default="artifacts", help="Directory for corrected images")
    parser.add_argument("--synthetic-suite", action="store_true", help="Generate and analyze synthetic QA cases")
    args = parser.parse_args()

    if args.synthetic_suite:
        sample_dir = Path("samples/generated")
        cases = write_suite(sample_dir)
        results = {
            name: run_agent(path, args.output_dir)
            for name, path in cases.items()
        }
        print(json.dumps(results, indent=2))
        return 0

    if not args.image:
        parser.error("image is required unless --synthetic-suite is used")

    result = run_agent(args.image, args.output_dir)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
