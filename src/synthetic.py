from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def product_frame(
    width: int = 900,
    height: int = 900,
    *,
    object_scale: float = 0.56,
    center: tuple[float, float] = (0.5, 0.5),
    background: int = 242,
    object_value: int = 55,
    blur_sigma: float = 0.0,
) -> np.ndarray:
    image = np.full((height, width, 3), background, dtype=np.uint8)
    ow = max(40, int(width * object_scale))
    oh = max(40, int(height * object_scale * 0.82))
    cx = int(width * center[0])
    cy = int(height * center[1])
    x0 = max(0, cx - ow // 2)
    y0 = max(0, cy - oh // 2)
    x1 = min(width - 1, cx + ow // 2)
    y1 = min(height - 1, cy + oh // 2)

    cv2.rectangle(image, (x0, y0), (x1, y1), (object_value,) * 3, thickness=-1)
    inset = max(8, int(min(ow, oh) * 0.12))
    cv2.rectangle(
        image,
        (x0 + inset, y0 + inset),
        (x1 - inset, y1 - inset),
        (object_value + 65,) * 3,
        thickness=4,
    )
    cv2.line(image, (x0 + inset, cy), (x1 - inset, cy), (object_value + 95,) * 3, 5)

    if blur_sigma > 0:
        k = max(3, int(round(blur_sigma * 6)) | 1)
        image = cv2.GaussianBlur(image, (k, k), blur_sigma)
    return image


def write_suite(directory: str | Path) -> dict[str, Path]:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    cases = {
        "good": product_frame(object_scale=0.62),
        "margin": product_frame(object_scale=0.32, center=(0.37, 0.47)),
        "blur": product_frame(object_scale=0.62, blur_sigma=9.0),
        "dark": product_frame(object_scale=0.62, background=42, object_value=4),
        "bright": product_frame(object_scale=0.62, background=254, object_value=236),
    }
    paths: dict[str, Path] = {}
    for name, image in cases.items():
        path = directory / f"{name}.png"
        if not cv2.imwrite(str(path), image):
            raise OSError(f"Could not write {path}")
        paths[name] = path
    return paths
