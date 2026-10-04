# ListingLens Agent — Technical Report

## Problem and users

Small sellers, marketplace operators, studio teams, and product photographers routinely need to decide whether a catalog image is publishable, can be fixed automatically, or must be reshot. A single scalar quality score is not enough: the system must take a bounded action when the evidence supports it and stop when the image failure cannot be repaired safely.

ListingLens turns OpenCV 5 measurements into an observable perception → decision → action loop.

## Architecture

Local/core path:

1. Read a product image.
2. OpenCV 5 measures sharpness, luminance, clipping, border/background variation, foreground extent, occupancy, and centering.
3. A deterministic policy classifies the failure.
4. If the only issue is fixable composition, the agent performs a bounded crop.
5. OpenCV 5 measures the corrected image again.
6. The second measurement decides ACCEPT_AFTER_FIX versus HUMAN_REVIEW.
7. Blur, severe exposure failure, missing foreground, and uncertain background route directly to HUMAN_RESHOOT.

AWS path:

S3 incoming object → Lambda container → same ListingLens core → JSON audit record and optional corrected PNG → S3 result prefix.
## OpenCV 5 implementation

Pinned runtime: `opencv-python-headless==5.0.0.93`.

The MVP deliberately uses transparent classical vision rather than hiding the decision inside an opaque model:

- variance of Laplacian for sharpness;
- grayscale mean for luminance;
- clipped-pixel fractions for shadow/highlight failure;
- border-pixel standard deviation as a simple-background sanity check;
- foreground mask relative to the median border intensity;
- morphological cleanup and contour aggregation;
- bounding-box occupancy and normalized center offset.

The policy is deterministic and committed in `src/agent.py`. Every result includes the exact OpenCV version and an ordered trace.

## Agentic behavior

OpenCV results materially change later actions:

- good frame → ACCEPT;
- excessive margin/off-center → AUTO_CROP;
- AUTO_CROP → OpenCV re-perception → ACCEPT_AFTER_FIX or HUMAN_REVIEW;
- blur / severe exposure / missing foreground / uncertain background → HUMAN_RESHOOT.

The agent cannot override a hard quality failure with prose.
## Evaluation

The deterministic synthetic laboratory creates five catalog-like cases without external assets:

| Case | Expected | Verified |
| --- | --- | --- |
| good | ACCEPT | yes |
| margin + off-center | AUTO_CROP → ACCEPT_AFTER_FIX | yes |
| blur | HUMAN_RESHOOT | yes |
| dark | HUMAN_RESHOOT | yes |
| bright/clipped | HUMAN_RESHOOT | yes |

For the margin case, observed occupancy rises from about 0.085 to about 0.651 and center offset falls from about 0.266 to 0.0 before acceptance.

Local suite: 7/7 tests after the AWS adapter was added. GitHub Actions validates the same behavior on Linux.

Public recorded-evidence demo:
https://williamleewilliam1-star.github.io/babydov-listinglens-agent/

## AWS deployment

The repository contains a deploy-ready AWS SAM image function under `aws/`.

- S3 provides the event and storage plane.
- Lambda executes the OpenCV 5 decision/action loop.
- Results are persisted as `result.json`.
- If a bounded crop is performed, `corrected.png` is persisted beside it.
- The SAM template scopes Lambda read/write permissions to its competition bucket.

The cloud contract is tested locally through a fake S3 client. The SAM template also passes `sam validate --lint`, and the container-image function completes `sam build` against a local arm64 Docker/Colima runtime. These checks prove the deployment package is reproducible locally; they are not a live-cloud claim. A real AWS deployment is still required before final submission and must not be represented as completed until external deployment evidence exists.
## Failure handling and human control

ListingLens is intentionally conservative.

- Blur is not sharpened and claimed as repaired.
- Severe under/over-exposure is not fabricated into a pass.
- No detected object becomes a reshoot request.
- A bounded crop is the only autonomous image mutation in the MVP.
- Every autonomous mutation is measured again.
- A failed post-action evaluation escalates to a human.

This keeps the workflow auditable and limits automation to a correction that can be directly validated by the same vision system that requested it.

## Responsible use

The MVP analyzes image quality and composition only. It does not infer identity, protected traits, demographics, emotion, or individual behavior. It uses synthetic images for its built-in evaluation and accepts local user-supplied product images.

## Judge demonstration

A Remotion judge cut has been rendered from committed evidence assets and published at https://williamleewilliam1-star.github.io/babydov-listinglens-agent/judge-video.html. The verified cut is 80 seconds, 1920×1080, H.264 at 30 fps. It shows the team attribution, the perception → decision → action → re-perception loop, a successful no-change case, the autonomous crop/re-measure case, three human-escalation failures, AWS architecture, and the 5/5 deterministic evaluation summary. The cloud scene intentionally says live AWS deployment is pending until a real receipt exists.

## Limitations

- Foreground extraction assumes a relatively simple catalog background.
- Fixed thresholds need calibration for different product categories and creative styles.
- The current agent does not perform perspective correction, segmentation with a learned model, or color-reference calibration.
- The recorded GitHub Pages demo is reproducible evidence, not a substitute for the required final AWS deployment.
- Real-world evaluation on a licensed product-photo set is still planned.


## Submission receipt

Devpost submission is confirmed at https://devpost.com/software/listinglens-agent. The submission remains editable until the competition deadline; any later AWS evidence must update this same submission rather than creating a duplicate.
