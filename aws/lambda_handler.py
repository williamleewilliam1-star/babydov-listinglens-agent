from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import unquote_plus

from src.agent import run_agent


_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_name(key: str) -> str:
    name = Path(key).name or "input.jpg"
    return _SAFE.sub("_", name)[:180]


def _source(event: dict[str, Any]) -> tuple[str, str]:
    if event.get("bucket") and event.get("key"):
        return str(event["bucket"]), str(event["key"])
    records = event.get("Records") or []
    if not records:
        raise ValueError("Expected {bucket,key} or an S3 event record")
    record = records[0]
    return (
        str(record["s3"]["bucket"]["name"]),
        unquote_plus(str(record["s3"]["object"]["key"])),
    )
def process_event(event: dict[str, Any], s3: Any) -> dict[str, Any]:
    bucket, key = _source(event)
    output_bucket = str(event.get("output_bucket") or os.environ.get("OUTPUT_BUCKET") or bucket)
    prefix = str(event.get("output_prefix") or os.environ.get("OUTPUT_PREFIX") or "listinglens-results").strip("/")
    filename = _safe_name(key)
    stem = Path(filename).stem

    with tempfile.TemporaryDirectory(prefix="listinglens-") as td:
        root = Path(td)
        local_input = root / filename
        output_dir = root / "corrected"
        s3.download_file(bucket, key, str(local_input))

        result = run_agent(local_input, output_dir)
        result_key = f"{prefix}/{stem}/result.json"

        corrected_local = result["final"].get("corrected_image")
        corrected_key = None
        if corrected_local:
            corrected_key = f"{prefix}/{stem}/corrected.png"
            s3.upload_file(
                corrected_local,
                output_bucket,
                corrected_key,
                ExtraArgs={"ContentType": "image/png"},
            )
            result["final"]["corrected_image"] = f"s3://{output_bucket}/{corrected_key}"
        result["aws"] = {
            "source": f"s3://{bucket}/{key}",
            "result": f"s3://{output_bucket}/{result_key}",
            "corrected": f"s3://{output_bucket}/{corrected_key}" if corrected_key else None,
        }
        body = json.dumps(result, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        s3.put_object(
            Bucket=output_bucket,
            Key=result_key,
            Body=body,
            ContentType="application/json",
        )

    return result


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    import boto3

    result = process_event(event, boto3.client("s3"))
    return {
        "statusCode": 200,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(
            {
                "decision": result["final"]["decision"],
                "result": result["aws"]["result"],
                "corrected": result["aws"]["corrected"],
            }
        ),
    }
