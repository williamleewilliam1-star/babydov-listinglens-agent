# AWS deployment

The AWS component is an S3-triggered Lambda container. A new image under `incoming/` is downloaded into Lambda temporary storage, analyzed by OpenCV 5, and passed through the same ListingLens policy used locally.

Outputs are written back to S3 under:

`listinglens-results/<input-stem>/result.json`

If OpenCV evidence triggers a bounded crop, Lambda also writes:

`listinglens-results/<input-stem>/corrected.png`

This is a meaningful cloud component: S3 provides the event/data plane and Lambda executes the perception → decision → action loop.

## Architecture and deployment contract

- Lambda package type: container image.
- Lambda architecture: `arm64`.
- Memory: 2048 MB.
- Timeout: 60 seconds.
- Input prefix: `incoming/`.
- Output prefix: `listinglens-results/`.
- S3 read/write policy is scoped to the one deployment bucket.
- The bucket name is an explicit CloudFormation parameter so the function role does not create a circular dependency on the bucket resource.

## Deploy with AWS SAM

Prerequisites: Docker-compatible daemon, AWS CLI credentials, AWS SAM CLI.

Choose a globally unique lowercase bucket name, then:

```bash
cd aws
sam build

sam deploy \
  --stack-name listinglens-opencv26 \
  --capabilities CAPABILITY_IAM \
  --resolve-image-repos \
  --parameter-overrides CatalogBucketName=<globally-unique-bucket-name> \
  --region <aws-region> \
  --guided
```

The template creates one dedicated S3 bucket plus the Lambda image function and least-scope read/write policies for that bucket.

No AWS resource is created by this repository unless a deploy command is explicitly run.

## Local verification

The test suite uses an in-memory fake S3 implementation, so the cloud contract is tested without AWS credentials:

```bash
python -m unittest discover -s tests -v
```

Infrastructure validation/build:

```bash
sam validate -t aws/template.yaml --lint
sam build -t aws/template.yaml
```

When Docker runs through Colima on macOS, SAM may need the socket explicitly:

```bash
DOCKER_HOST="unix://$HOME/.colima/default/docker.sock" sam build -t aws/template.yaml
```

Verified locally on Apple Silicon: SAM validation passes and the arm64 Lambda container image builds successfully. This is packaging evidence only, not proof of a live AWS stack.

A final competition submission must not claim live AWS deployment until the real stack exists and a deployment/e2e receipt has been recorded.
