# ListingLens judge video

Remotion source for the OpenCV AI Competition 2026 judge video.

## Render

```bash
cd video
npm ci
npm run render
```

Expected output:

```
video/out/listinglens-judge-draft.mp4
```

Current verified render characteristics:

- 1920×1080
- H.264
- 30 fps
- 80 seconds
- generated from the same committed synthetic evidence images used by the ListingLens agent

The current cut deliberately labels live AWS deployment as pending. After a real AWS receipt exists, update only the cloud-delivery scene and render the final judge cut. Do not present local SAM validation/build as a live AWS deployment.

## QA

Representative frames can be extracted locally from the rendered MP4. Rendered outputs and QA frames are ignored by Git and are not source-of-truth artifacts.
