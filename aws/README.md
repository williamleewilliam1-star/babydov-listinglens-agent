# AWS deployment

The AWS component is an S3-triggered Lambda container. A new image under `incoming/` is downloaded into Lambda temporary storage, analyzed by OpenCV 5, and passed through the same ListingLens policy used locally.

Outputs are written back to S3 under:

`listinglens-results/<input-stem>/result.json`

If OpenCV evidence triggers a bounded crop, Lambda also writes:

`listinglens-results/<input-stem>/corrected.png`

This is a meaningful cloud component: S3 provides the event/data plane and Lambda executes the perception → decision → action loop.

## Deploy with AWS SAM

Prerequisites: Docker, AWS CLI credentials, AWS SAM CLI.

```bash
cd aws
sam build
sam deploy --guided
```

The template creates a dedicated S3 bucket and least-scope read/write policies for that bucket. No AWS resource is created by this repository unless the deploy command is explicitly run.

## Local verification

The test suite uses an in-memory fake S3 implementation, so the cloud contract is tested without AWS credentials:

```bash
python -m unittest discover -s tests -v
```
