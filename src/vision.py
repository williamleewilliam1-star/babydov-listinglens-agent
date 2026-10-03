from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass(frozen=True)
class VisionMetrics:
    width: int
    height: int
    sharpness: float
    mean_luma: float
    shadow_clip_pct: float
    highlight_clip_pct: float
    border_std: float
    object_occupancy: float
    center_offset: float
    bbox: tuple[int, int, int, int] | None

    def to_dict(self) -> dict:
        data = asdict(self)
        data["bbox"] = list(self.bbox) if self.bbox else None
        return data
def load_bgr(path: str | Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Could not read image: {path}")
    return image


def _border_pixels(gray: np.ndarray, frac: float = 0.08) -> np.ndarray:
    h, w = gray.shape
    t = max(1, int(min(h, w) * frac))
    top = gray[:t, :].ravel()
    bottom = gray[-t:, :].ravel()
    left = gray[t:-t or None, :t].ravel()
    right = gray[t:-t or None, -t:].ravel()
    return np.concatenate([top, bottom, left, right])


def _foreground_mask(gray: np.ndarray) -> np.ndarray:
    border = _border_pixels(gray)
    bg = float(np.median(border))
    diff = cv2.absdiff(gray, np.full_like(gray, int(round(bg))))
    _, mask = cv2.threshold(diff, 18, 255, cv2.THRESH_BINARY)
    k = max(3, int(round(min(gray.shape) * 0.012)) | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    return mask
def analyze_image(image: np.ndarray) -> VisionMetrics:
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("Expected a BGR color image")

    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    mean_luma = float(gray.mean())
    shadow_clip_pct = float(np.mean(gray <= 5))
    highlight_clip_pct = float(np.mean(gray >= 250))
    border_std = float(_border_pixels(gray).std())

    mask = _foreground_mask(gray)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_area = max(24.0, h * w * 0.002)
    contours = [c for c in contours if cv2.contourArea(c) >= min_area]

    bbox = None
    occupancy = 0.0
    center_offset = 1.0
    if contours:
        pts = np.vstack(contours)
        x, y, bw, bh = cv2.boundingRect(pts)
        bbox = (int(x), int(y), int(bw), int(bh))
        occupancy = float((bw * bh) / (w * h))
        cx = x + bw / 2.0
        cy = y + bh / 2.0
        dx = (cx - w / 2.0) / (w / 2.0)
        dy = (cy - h / 2.0) / (h / 2.0)
        center_offset = float(min(1.0, (dx * dx + dy * dy) ** 0.5))

    return VisionMetrics(
        width=w,
        height=h,
        sharpness=sharpness,
        mean_luma=mean_luma,
        shadow_clip_pct=shadow_clip_pct,
        highlight_clip_pct=highlight_clip_pct,
        border_std=border_std,
        object_occupancy=occupancy,
        center_offset=center_offset,
        bbox=bbox,
    )
def safe_crop(image: np.ndarray, bbox: tuple[int, int, int, int], pad: float = 0.12) -> np.ndarray:
    h, w = image.shape[:2]
    x, y, bw, bh = bbox
    px = int(round(bw * pad))
    py = int(round(bh * pad))
    x0 = max(0, x - px)
    y0 = max(0, y - py)
    x1 = min(w, x + bw + px)
    y1 = min(h, y + bh + py)
    if x1 - x0 < 2 or y1 - y0 < 2:
        raise ValueError("Computed crop is too small")
    return image[y0:y1, x0:x1].copy()


def write_image(path: str | Path, image: np.ndarray) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), image):
        raise OSError(f"Could not write image: {path}")


def opencv_version() -> str:
    return cv2.__version__
