# Devpost Submission Draft

## Project name
ListingLens Agent

## Tagline
An OpenCV 5 catalog-photo QA agent that measures, acts, re-measures, and knows when to ask a human.

## What it does
ListingLens analyzes product/catalog images with OpenCV 5 and turns visual evidence into a bounded operational decision. Good images are accepted. Composition problems can trigger a safe auto-crop. The corrected image is analyzed again before acceptance. Blur, severe exposure failure, uncertain background, or failed correction routes to human review/reshoot.

## Why agentic vision
The OpenCV result changes the next action. The system exposes the full perception → decision → action → re-perception trace instead of using vision only as context for a chatbot.

## Built with
- OpenCV 5.0.0
- Python / NumPy
- AWS Lambda container + S3 event/data plane (SAM validate/build verified locally; live AWS deployment evidence pending)
- GitHub Actions
- GitHub Pages evidence demo
- Remotion judge-video source with a verified 80-second 1080p H.264 render, published at https://williamleewilliam1-star.github.io/babydov-listinglens-agent/judge-video.html

## Links
- Source: https://github.com/williamleewilliam1-star/babydov-listinglens-agent
- Recorded evidence demo: https://williamleewilliam1-star.github.io/babydov-listinglens-agent/
- Architecture: repository docs/ARCHITECTURE.md
- Technical report: repository docs/TECHNICAL_REPORT.md

## Evaluation
Five deterministic synthetic cases cover success, an autonomous recoverable composition fault, and three failure/escalation modes. The margin/off-center case improves from about 0.085 object occupancy and 0.266 center offset to about 0.651 occupancy and 0.0 offset after the OpenCV-triggered crop.

## Agentic Vision Award
Yes — intended target.

## Submission status
- Devpost submission confirmed: https://devpost.com/software/listinglens-agent
- judge video: https://youtu.be/AuP5tELYp_U

## Honest pending items
- real AWS deployment evidence (AWS CLI is not currently authenticated on the preparation Mac)
- after AWS deployment, update the cloud scene and re-render/replace the published judge cut
- edit the existing Devpost submission with verified AWS evidence; do not create a second submission
