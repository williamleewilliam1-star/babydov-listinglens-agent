from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .vision import VisionMetrics, analyze_image, load_bgr, opencv_version, safe_crop, write_image


@dataclass(frozen=True)
class Policy:
    min_sharpness: float = 90.0
    min_luma: float = 55.0
    max_luma: float = 238.0
    max_shadow_clip: float = 0.08
    max_highlight_clip: float = 0.12
    min_occupancy: float = 0.30
    max_occupancy: float = 0.88
    max_center_offset: float = 0.24
    max_border_std: float = 28.0


def _hard_failures(m: VisionMetrics, p: Policy) -> list[str]:
    reasons: list[str] = []
    if m.sharpness < p.min_sharpness:
        reasons.append("blur")
    if m.mean_luma < p.min_luma or m.shadow_clip_pct > p.max_shadow_clip:
        reasons.append("underexposed")
    if m.mean_luma > p.max_luma or m.highlight_clip_pct > p.max_highlight_clip:
        reasons.append("overexposed")
    if m.bbox is None:
        reasons.append("object_not_detected")
    if m.border_std > p.max_border_std:
        reasons.append("background_not_uniform")
    return reasons
def _composition_failures(m: VisionMetrics, p: Policy) -> list[str]:
    reasons: list[str] = []
    if m.bbox is None:
        return reasons
    if m.object_occupancy < p.min_occupancy:
        reasons.append("too_much_margin")
    if m.object_occupancy > p.max_occupancy:
        reasons.append("object_too_large")
    if m.center_offset > p.max_center_offset:
        reasons.append("off_center")
    return reasons


def _snapshot(m: VisionMetrics) -> dict[str, Any]:
    return m.to_dict()


def evaluate_metrics(m: VisionMetrics, policy: Policy) -> dict[str, Any]:
    hard = _hard_failures(m, policy)
    composition = _composition_failures(m, policy)
    return {
        "hard_failures": hard,
        "composition_failures": composition,
        "passes": not hard and not composition,
    }


def run_agent(
    input_path: str | Path,
    output_dir: str | Path,
    policy: Policy | None = None,
) -> dict[str, Any]:
    policy = policy or Policy()
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    image = load_bgr(input_path)
    before = analyze_image(image)
    initial_eval = evaluate_metrics(before, policy)
    trace: list[dict[str, Any]] = [
        {
            "step": 1,
            "kind": "PERCEPTION",
            "engine": f"OpenCV {opencv_version()}",
            "metrics": _snapshot(before),
        },
        {
            "step": 2,
            "kind": "DECISION",
            "evaluation": initial_eval,
        },
    ]

    if initial_eval["hard_failures"]:
        final = {
            "decision": "HUMAN_RESHOOT",
            "reason_codes": initial_eval["hard_failures"] + initial_eval["composition_failures"],
            "corrected_image": None,
            "before": _snapshot(before),
            "after": None,
        }
        trace.append(
            {
                "step": 3,
                "kind": "ACTION",
                "action": "REQUEST_HUMAN_RESHOOT",
                "reason_codes": final["reason_codes"],
            }
        )
        return _result(input_path, policy, final, trace)

    composition = initial_eval["composition_failures"]
    crop_worthy = set(composition) & {"too_much_margin", "off_center"}
    if crop_worthy and before.bbox is not None and "object_too_large" not in composition:
        corrected = safe_crop(image, before.bbox)
        corrected_path = output_dir / f"{input_path.stem}.autocrop.png"
        write_image(corrected_path, corrected)
        after = analyze_image(corrected)
        post_eval = evaluate_metrics(after, policy)
        trace.extend(
            [
                {
                    "step": 3,
                    "kind": "ACTION",
                    "action": "AUTO_CROP",
                    "output": str(corrected_path),
                    "triggered_by": sorted(crop_worthy),
                },
                {
                    "step": 4,
                    "kind": "RE_PERCEPTION",
                    "engine": f"OpenCV {opencv_version()}",
                    "metrics": _snapshot(after),
                },
                {
                    "step": 5,
                    "kind": "FINAL_DECISION",
                    "evaluation": post_eval,
                },
            ]
        )
        improved = (
            after.object_occupancy > before.object_occupancy
            and after.center_offset <= before.center_offset + 1e-9
        )
        if post_eval["passes"] and improved:
            final = {
                "decision": "ACCEPT_AFTER_FIX",
                "reason_codes": [],
                "corrected_image": str(corrected_path),
                "before": _snapshot(before),
                "after": _snapshot(after),
            }
        else:
            final = {
                "decision": "HUMAN_REVIEW",
                "reason_codes": post_eval["hard_failures"] + post_eval["composition_failures"],
                "corrected_image": str(corrected_path),
                "before": _snapshot(before),
                "after": _snapshot(after),
            }
        return _result(input_path, policy, final, trace)

    if initial_eval["passes"]:
        final = {
            "decision": "ACCEPT",
            "reason_codes": [],
            "corrected_image": None,
            "before": _snapshot(before),
            "after": None,
        }
        trace.append({"step": 3, "kind": "ACTION", "action": "NO_CHANGE"})
        return _result(input_path, policy, final, trace)
    final = {
        "decision": "HUMAN_REVIEW",
        "reason_codes": composition,
        "corrected_image": None,
        "before": _snapshot(before),
        "after": None,
    }
    trace.append(
        {
            "step": 3,
            "kind": "ACTION",
            "action": "REQUEST_HUMAN_REVIEW",
            "reason_codes": composition,
        }
    )
    return _result(input_path, policy, final, trace)


def _result(input_path: Path, policy: Policy, final: dict[str, Any], trace: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "product": "ListingLens Agent",
        "opencv_version": opencv_version(),
        "input": str(input_path),
        "policy": {
            key: getattr(policy, key)
            for key in policy.__dataclass_fields__
        },
        "final": final,
        "trace": trace,
    }
