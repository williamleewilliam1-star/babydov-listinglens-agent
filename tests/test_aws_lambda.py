from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import cv2

from aws.lambda_handler import process_event
from src.synthetic import product_frame


class FakeS3:
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], bytes] = {}

    def download_file(self, bucket: str, key: str, filename: str) -> None:
        Path(filename).write_bytes(self.objects[(bucket, key)])

    def upload_file(self, filename: str, bucket: str, key: str, ExtraArgs=None) -> None:
        self.objects[(bucket, key)] = Path(filename).read_bytes()

    def put_object(self, *, Bucket: str, Key: str, Body: bytes, ContentType: str) -> None:
        self.objects[(Bucket, Key)] = bytes(Body)


def encode_png(image) -> bytes:
    ok, encoded = cv2.imencode(".png", image)
    if not ok:
        raise RuntimeError("encode failed")
    return encoded.tobytes()
class ListingLensLambdaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.s3 = FakeS3()
        self.bucket = "catalog-input"

    def test_margin_image_creates_corrected_image_and_audit_json(self) -> None:
        key = "incoming/item 01.png"
        self.s3.objects[(self.bucket, key)] = encode_png(
            product_frame(object_scale=0.32, center=(0.37, 0.47))
        )
        result = process_event(
            {
                "bucket": self.bucket,
                "key": key,
                "output_prefix": "qa",
            },
            self.s3,
        )
        self.assertEqual(result["final"]["decision"], "ACCEPT_AFTER_FIX")
        self.assertEqual(result["opencv_version"], "5.0.0")
        self.assertIn((self.bucket, "qa/item_01/corrected.png"), self.s3.objects)
        raw = self.s3.objects[(self.bucket, "qa/item_01/result.json")]
        stored = json.loads(raw)
        self.assertEqual(stored["final"]["decision"], "ACCEPT_AFTER_FIX")
        self.assertTrue(stored["aws"]["corrected"].endswith("/qa/item_01/corrected.png"))
    def test_s3_event_blur_routes_to_human_without_corrected_artifact(self) -> None:
        key = "incoming/blurry.jpg"
        self.s3.objects[(self.bucket, key)] = encode_png(
            product_frame(object_scale=0.62, blur_sigma=9.0)
        )
        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": self.bucket},
                        "object": {"key": "incoming%2Fblurry.jpg"},
                    }
                }
            ],
            "output_prefix": "qa",
        }
        result = process_event(event, self.s3)
        self.assertEqual(result["final"]["decision"], "HUMAN_RESHOOT")
        self.assertIsNone(result["aws"]["corrected"])
        self.assertIn((self.bucket, "qa/blurry/result.json"), self.s3.objects)
        self.assertNotIn((self.bucket, "qa/blurry/corrected.png"), self.s3.objects)


if __name__ == "__main__":
    unittest.main()
