# 19th alpha — feedback from a loss-reserving use case

Written for the 19th team. Our own working notes are longer and more methodological; this page is what we think
you can act on.

## What we tested

We predicted **link ratios** on loss triangles — the ratio of one development period's cumulative paid losses to
the period before. That is the object classical reserving methods (Chain Ladder, Mack) are built from.

The framing that worked: predict the ratio **divided by Chain Ladder's own volume-weighted factor** for that step.
Then **1.0 reproduces Chain Ladder exactly**, and the model learns a correction to a number an actuary already
trusts. This is a much better entry point for a reserving demo than predicting losses directly.

Data: 50 synthetic triangles, 10 origins by 10 development periods, pooled by anchor into 300–1,800 row tables.
We used synthetic data deliberately — real triangle corpora usually carry licence terms that prohibit upload.

## What worked well

- **It modelled the problem.** 300 pooled rows, trained in seconds, all four modes offered.
- **The export is genuinely good.** 4.2 MB bundle, numpy-only, Apache-2.0, no runtime dependency on 19th. It scored
  1,200 held-out rows in about **one second**. That is the strongest thing about the product for our use case.
- **Text identifiers are inferred as categorical.** Sending `"d1"` rather than `1` is read correctly.

## One structural thing worth knowing

**Depth ends up encoded in a categorical column.** With `dev_idx` categorical, at anchor 3 every one of our 1,200
prediction rows carried a development level absent from the training rows:

```
unseen_category_counts: { origin_idx: 300, dev_idx: 900, cal_idx: 1200 }
```

Training rows only span `dev_idx` 1..3, so depth extrapolation happens entirely through the model's
**unseen-category bucket** (`unseen = len(spec["vocab"]) + 1`). That is not a reserving quirk: it applies to any
panel or time-series table where "how far ahead am I" is a categorical input. If you have a view on how the unseen
bucket should behave for that case, we would like to hear it.

## Findings, ranked by what we think you would act on

| # | Finding | Detail |
| --- | --- | --- |
| 1 | **No accuracy metric is returned** | `get_results` gives relative `quality.difference_points` and nothing absolute. Users must export the model and score it themselves to know if it is any good. |
| 2 | **`quality.difference_points` did not track held-out performance** | Warpspeed was scored **−0.1077 points** against Fast and then classified **every one of 113 held-out rows identically**, with equal AUC. Whatever the number measures, it did not surface as worse classification. |
| 3 | **Constant columns are dropped silently** | `global_factor_available` was excluded with *"one value only in the labelled rows"*, reported in `excluded_inputs` rather than as a warning. A designed feature disappeared and the model trained on 7 inputs where we declared 8. |
| 4 | **A column cannot be declared categorical** | `column_types` is embeddings-only; everything else is inferred physically. Integer identifiers read as `numeric`, the same values as text read as `categorical`. The typing is carried by the serialisation and must be reproduced on every prediction row. |
| 5 | **`UPLOAD_SLOT_QUOTA` reports `retryable: false`** | It reads as a permanent failure and it is not — draining the create/upload/finalize cycle one at a time works. The limit is never named. Replaying with the same idempotency key recovers the existing preparation, which is good, but we only found that by trying. |
| 6 | **Training mode moved calibration, not classification** | `instant` → `standard` → `high` → `ultra` gave an identical confusion matrix at every level on our data (4.1 s → 22.0 s build). Log loss improved monotonically (0.0770 → 0.0648 → 0.0588 → 0.0551) with the gain halving each step. The mode descriptions promise accuracy differences. |

Smaller ones: download links expire in about five minutes (`X-Goog-Expires=299`), which is easy to trip over when
scripting; `integer_tfpb` is listed as an export format but every model reports `EXPORT_UNAVAILABLE`; and the
"additional training limitation" warning fires on `high` and `ultra` with no code or detail.

## The honest benchmark

We ran a matched TabPFN control on the same 1,200 cells, same seven columns, same transform:

| | Slope of log error against depth |
| --- | --- |
| 19th | +0.0493 (se 0.0018) |
| TabPFN control | +0.0478 (se 0.0016) |
| Difference | +0.0015 (z = +0.62) |

No modelling edge either way on this problem. **That is not the interesting comparison for your product** — the
difference we did measure was deployment: one second versus minutes for 1,200 rows, a 4 MB portable artifact
against a large library, and no service dependency at inference.

## An offer

We have a **deterministic synthetic loss-triangle generator** — 10×10, realistic development factors, verified
recoverable to within ~1% — with no licence encumbrance, committed alongside the data it produces.

Your four demo datasets are tumour, exoplanet, support tickets and machine failure. **None is actuarial.** We would
be glad to contribute this one as a claims-triangle demo, together with the ratio-over-Chain-Ladder framing above,
if it is useful to you.
