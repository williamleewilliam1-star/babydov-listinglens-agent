from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import cv2

from src.agent import run_agent
from src.synthetic import write_suite


class ListingLensAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.samples = write_suite(self.root / "samples")
        self.out = self.root / "out"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_good_frame_is_accepted(self) -> None:
        result = run_agent(self.samples["good"], self.out)
        self.assertEqual(result["final"]["decision"], "ACCEPT")
        self.assertEqual(result["opencv_version"], "5.0.0")
        self.assertEqual(result["trace"][0]["kind"], "PERCEPTION")
    def test_margin_frame_is_autocropped_then_accepted(self) -> None:
        result = run_agent(self.samples["margin"], self.out)
        self.assertEqual(result["final"]["decision"], "ACCEPT_AFTER_FIX")
        self.assertIsNotNone(result["final"]["corrected_image"])
        self.assertGreater(
            result["final"]["after"]["object_occupancy"],
            result["final"]["before"]["object_occupancy"],
        )
        self.assertLessEqual(
            result["final"]["after"]["center_offset"],
            result["final"]["before"]["center_offset"] + 1e-9,
        )
        self.assertEqual(result["trace"][2]["action"], "AUTO_CROP")
        self.assertEqual(result["trace"][3]["kind"], "RE_PERCEPTION")
        self.assertTrue(Path(result["final"]["corrected_image"]).exists())

    def test_blur_requires_human_reshoot(self) -> None:
        result = run_agent(self.samples["blur"], self.out)
        self.assertEqual(result["final"]["decision"], "HUMAN_RESHOOT")
        self.assertIn("blur", result["final"]["reason_codes"])
    def test_dark_or_bright_requires_human_reshoot(self) -> None:
        dark = run_agent(self.samples["dark"], self.out)
        bright = run_agent(self.samples["bright"], self.out)
        self.assertEqual(dark["final"]["decision"], "HUMAN_RESHOOT")
        self.assertIn("underexposed", dark["final"]["reason_codes"])
        self.assertEqual(bright["final"]["decision"], "HUMAN_RESHOOT")
        self.assertIn("overexposed", bright["final"]["reason_codes"])

    def test_trace_is_json_serializable_and_has_decision_after_perception(self) -> None:
        result = run_agent(self.samples["margin"], self.out)
        encoded = json.dumps(result)
        self.assertIn('"PERCEPTION"', encoded)
        self.assertIn('"AUTO_CROP"', encoded)
        kinds = [step["kind"] for step in result["trace"]]
        self.assertLess(kinds.index("PERCEPTION"), kinds.index("DECISION"))
        self.assertLess(kinds.index("ACTION"), kinds.index("RE_PERCEPTION"))


if __name__ == "__main__":
    unittest.main()
