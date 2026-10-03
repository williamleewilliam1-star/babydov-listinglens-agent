# Synthetic laboratory

The repository generates its own deterministic catalog-like images, so the core agent can be tested without external assets or copyrighted samples.

Observed local run with OpenCV 5.0.0:

| Case | Initial evidence | Agent action | Final |
| --- | --- | --- | --- |
| good | occupancy ~0.315, centered, sharp | no change | ACCEPT |
| margin | occupancy ~0.085, offset ~0.266 | AUTO_CROP + re-perception | ACCEPT_AFTER_FIX |
| blur | sharpness ~0.2 | request reshoot | HUMAN_RESHOOT |
| dark | luma ~31 | request reshoot | HUMAN_RESHOOT |
| bright | luma ~249 / foreground unresolved | request reshoot | HUMAN_RESHOOT |

For the margin case, the automated crop raised occupancy from ~0.085 to ~0.651 and reduced center offset from ~0.266 to 0.0 before acceptance.

Run it:

```bash
python listinglens.py --synthetic-suite
```

The complete JSON includes every perception, decision, action, and re-perception step.
