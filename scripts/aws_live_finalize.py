from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "artifacts" / "aws-live-receipt.json"
STACK_NAME = "listinglens-opencv26"


def run(cmd: list[str], *, check: bool = True, capture: bool = True, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        cmd,
        cwd=ROOT,
        check=check,
        text=True,
        capture_output=capture,
        env=merged,
    )


def require_tool(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f"required tool missing: {name}")


def aws_json(args: list[str], region: str) -> dict:
    cp = run(["aws", *args, "--region", region, "--output", "json"])
    return json.loads(cp.stdout or "{}")


def account_identity(region: str) -> tuple[str, dict]:
    try:
        ident = aws_json(["sts", "get-caller-identity"], region)
    except Exception as exc:
        raise RuntimeError("AWS_AUTH_REQUIRED: aws sts get-caller-identity failed") from exc
    account = str(ident.get("Account") or "")
    if not account:
        raise RuntimeError("AWS_AUTH_REQUIRED: AWS account id missing")
    return account, ident


def bucket_name(account: str, region: str) -> str:
    digest = hashlib.sha256(account.encode()).hexdigest()[:12]
    safe_region = region.lower().replace("_", "-")
    return f"listinglens-opencv26-{digest}-{safe_region}"[:63].rstrip("-")


def generate_inputs(root: Path) -> dict[str, dict]:
    sys.path.insert(0, str(ROOT))
    import cv2
    from src.synthetic import product_frame

    cases = {
        "good": (product_frame(object_scale=0.62), "ACCEPT"),
        "margin": (product_frame(object_scale=0.32, center=(0.37, 0.47)), "ACCEPT_AFTER_FIX"),
        "blur": (product_frame(object_scale=0.62, blur_sigma=9.0), "HUMAN_RESHOOT"),
    }
    out: dict[str, dict] = {}
    root.mkdir(parents=True, exist_ok=True)
    for name, (img, expected) in cases.items():
        path = root / f"{name}.png"
        ok = cv2.imwrite(str(path), img)
        if not ok:
            raise RuntimeError(f"failed to write {path}")
        out[name] = {"path": path, "expected": expected}
    return out


def wait_for_result(bucket: str, name: str, region: str, timeout: int = 120) -> dict:
    key = f"listinglens-results/{name}/result.json"
    deadline = time.time() + timeout
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        dst = Path(tmp.name)
    try:
        while time.time() < deadline:
            cp = run(
                ["aws", "s3api", "head-object", "--bucket", bucket, "--key", key, "--region", region],
                check=False,
            )
            if cp.returncode == 0:
                run(["aws", "s3", "cp", f"s3://{bucket}/{key}", str(dst), "--region", region])
                return json.loads(dst.read_text())
            time.sleep(3)
    finally:
        dst.unlink(missing_ok=True)
    raise RuntimeError(f"timed out waiting for {key}")


def redact_uri(value: str | None, bucket: str) -> str | None:
    if not value:
        return value
    return value.replace(bucket, "<CATALOG_BUCKET>")


def make_receipt(*, account: str, region: str, bucket: str, stack: dict, function: dict, cases: dict[str, dict]) -> dict:
    return {
        "schema": "listinglens.aws_live_receipt.v1",
        "service": "AWS",
        "region": region,
        "stack_name": STACK_NAME,
        "stack_status": stack.get("StackStatus"),
        "account_sha256": hashlib.sha256(account.encode()).hexdigest(),
        "catalog_bucket_sha256": hashlib.sha256(bucket.encode()).hexdigest(),
        "lambda": {
            "architecture": (function.get("Architectures") or [None])[0],
            "memory_mb": function.get("MemorySize"),
            "timeout_seconds": function.get("Timeout"),
            "package_type": function.get("PackageType"),
            "state": function.get("State"),
            "last_update_status": function.get("LastUpdateStatus"),
        },
        "e2e": cases,
        "security": {
            "raw_account_id_committed": False,
            "raw_bucket_name_committed": False,
            "credentials_committed": False,
        },
        "verified_at_unix": int(time.time()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy and verify ListingLens on AWS.")
    parser.add_argument("--region", default=os.environ.get("AWS_REGION") or "us-east-1")
    parser.add_argument("--execute", action="store_true", help="Actually deploy and run the live AWS e2e.")
    parser.add_argument("--allow-overwrite-receipt", action="store_true")
    args = parser.parse_args()

    for tool in ("aws", "sam", "docker"):
        require_tool(tool)

    account, _ = account_identity(args.region)
    bucket = bucket_name(account, args.region)

    print(json.dumps({
        "auth": "ok",
        "region": args.region,
        "stack": STACK_NAME,
        "bucket_fingerprint": hashlib.sha256(bucket.encode()).hexdigest()[:16],
        "execute": args.execute,
    }, indent=2))

    if not args.execute:
        print("DRY_RUN_ONLY: authenticated, no AWS resources changed.")
        return 0

    if RECEIPT.exists() and not args.allow_overwrite_receipt:
        raise RuntimeError(f"receipt exists: {RECEIPT}; refusing overwrite")

    docker_host = os.environ.get("DOCKER_HOST")
    colima = Path.home() / ".colima/default/docker.sock"
    env = {}
    if not docker_host and colima.exists():
        env["DOCKER_HOST"] = f"unix://{colima}"

    run(["sam", "validate", "-t", "aws/template.yaml", "--lint"], env=env)
    run(["sam", "build", "-t", "aws/template.yaml"], env=env)

    deploy = [
        "sam", "deploy",
        "--template-file", ".aws-sam/build/template.yaml",
        "--stack-name", STACK_NAME,
        "--capabilities", "CAPABILITY_IAM",
        "--resolve-image-repos",
        "--parameter-overrides", f"CatalogBucketName={bucket}",
        "--region", args.region,
        "--no-confirm-changeset",
        "--no-fail-on-empty-changeset",
    ]
    cp = run(deploy, capture=True, env=env)
    print(cp.stdout[-4000:] if cp.stdout else "sam deploy completed")

    stacks = aws_json(["cloudformation", "describe-stacks", "--stack-name", STACK_NAME], args.region).get("Stacks") or []
    if len(stacks) != 1:
        raise RuntimeError("expected exactly one deployed stack")
    stack = stacks[0]
    if stack.get("StackStatus") not in {"CREATE_COMPLETE", "UPDATE_COMPLETE"}:
        raise RuntimeError(f"unexpected stack status: {stack.get('StackStatus')}")

    outputs = {x.get("OutputKey"): x.get("OutputValue") for x in stack.get("Outputs") or []}
    live_bucket = str(outputs.get("CatalogBucketName") or "")
    fn_name = str(outputs.get("ListingLensFunctionName") or "")
    if live_bucket != bucket or not fn_name:
        raise RuntimeError("stack outputs do not match expected deployment")

    fn = aws_json(["lambda", "get-function-configuration", "--function-name", fn_name], args.region)
    if (fn.get("Architectures") or [None])[0] != "arm64":
        raise RuntimeError("live Lambda is not arm64")
    if fn.get("State") not in {"Active", None}:
        raise RuntimeError(f"Lambda state not Active: {fn.get('State')}")
    if fn.get("LastUpdateStatus") not in {"Successful", None}:
        raise RuntimeError(f"Lambda update status not Successful: {fn.get('LastUpdateStatus')}")

    with tempfile.TemporaryDirectory(prefix="listinglens-aws-live-") as td:
        inputs = generate_inputs(Path(td))
        verified: dict[str, dict] = {}
        for name, spec in inputs.items():
            key = f"incoming/{name}.png"
            run(["aws", "s3", "cp", str(spec["path"]), f"s3://{bucket}/{key}", "--region", args.region])
            result = wait_for_result(bucket, name, args.region)
            actual = result.get("final", {}).get("decision")
            if actual != spec["expected"]:
                raise RuntimeError(f"{name}: expected {spec['expected']}, got {actual}")
            if result.get("opencv_version") != "5.0.0":
                raise RuntimeError(f"{name}: wrong OpenCV version {result.get('opencv_version')}")
            corrected = result.get("aws", {}).get("corrected")
            if name == "margin" and not corrected:
                raise RuntimeError("margin: corrected artifact missing")
            if name != "margin" and corrected:
                raise RuntimeError(f"{name}: unexpected corrected artifact")
            verified[name] = {
                "expected": spec["expected"],
                "actual": actual,
                "opencv_version": result.get("opencv_version"),
                "source": redact_uri(result.get("aws", {}).get("source"), bucket),
                "result": redact_uri(result.get("aws", {}).get("result"), bucket),
                "corrected": redact_uri(corrected, bucket),
            }

    receipt = make_receipt(account=account, region=args.region, bucket=bucket, stack=stack, function=fn, cases=verified)
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"LIVE_AWS_OK: wrote redacted receipt to {RECEIPT}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FINALIZE_AWS_BLOCKED: {exc}", file=sys.stderr)
        raise SystemExit(2)
