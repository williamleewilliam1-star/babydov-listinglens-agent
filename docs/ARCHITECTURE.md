# ListingLens Agent — perception → decision → action

```mermaid
flowchart LR
  A[Catalog image] --> B[OpenCV 5 perception]
  B --> C{Policy decision}
  C -->|Good| D[ACCEPT]
  C -->|Composition fixable| E[AUTO_CROP]
  E --> F[OpenCV 5 re-perception]
  F --> G{Improved + passes?}
  G -->|Yes| H[ACCEPT_AFTER_FIX]
  G -->|No| I[HUMAN_REVIEW]
  C -->|Blur / severe exposure / no object| J[HUMAN_RESHOOT]
```

Every step is emitted into the JSON trace. The agent does not call a crop merely because a user asked for one: the OpenCV metrics are the trigger. After an automated correction, OpenCV runs again and the second measurement determines whether the image is accepted.

## Current OpenCV 5 signals

- Laplacian variance for sharpness.
- Mean luminance.
- Shadow and highlight clipping fractions.
- Border variance for simple-background quality.
- Foreground bounding box.
- Object occupancy.
- Object-center offset.

## Human control

The agent only performs a bounded crop automatically. Blur, severe exposure failure, missing foreground, uncertain background, oversized framing, or unsuccessful correction escalate to a human rather than fabricating a fix.
