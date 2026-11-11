# 19th alpha glossary

This repo is a working notebook for the 19th private alpha: 19th trains a model on a supplied
CSV, and this repo tests it against an actuarial loss-reserving problem. Two vocabularies
therefore meet here — the product's own API terms and the reserving terms the test rows are
built from. The glossary keeps the words the repo deliberately separates (mode from variant,
a bundle from the `.tfpb` inside it) from collapsing into each other.

## Language

### 19th service

**Run**:
One submitted fit, identified by a `run_id`, moving through submission, training and delivery
states.

**Training mode**:
The effort level chosen at submission — `instant`, `standard`, `high` or `ultra` — which has no
default and, on this repo's evidence, moves calibration rather than classification.
_Avoid_: "mode" when you mean `model_variant`.

**Model variant**:
Which exported model file is offered — `fast`, `turbo` or `warpspeed` — kept separate from
training effort and used for downloads and predictions.
_Avoid_: "mode".

**Bundle**:
The downloaded artifact — `predict.py`, the vendored numpy runtime, `models/model.tfpb` and a
signed manifest — which runs locally with no dependency on 19th.
_Avoid_: "`.tfpb`" when you mean the whole bundle; the `.tfpb` is the weights file inside it.

**Idempotency key**:
The caller-supplied key under which the same key, the same CSV bytes and the same request
recover the same run for seven days.

**`quality.difference_points`**:
19th's relative quality score for a variant against Fast, which on this repo's evidence does
not predict held-out classification.
_Avoid_: "accuracy", "quality guarantee".

**Unseen-category bucket**:
The runtime's dedicated bucket (`unseen = len(spec["vocab"]) + 1`) for categorical values that
were absent from the fitted vocabulary.

### Reserving arm

**Loss triangle**:
Origins by development periods with only the upper triangle observed; the missing bottom-right
corner is the reserve being predicted.

**Cell**:
One (origin, development) position in a triangle, and the unit a prediction or error is
counted in — the arm scores 1,200 of them.

**Link ratio**:
The ratio of one development period's cumulative paid losses to the period before; this repo
predicts it divided by Chain Ladder's volume-weighted factor for that step, so 1.0 reproduces
Chain Ladder exactly.
_Avoid_: "development factor" when you mean the observed per-cell ratio — the factor is the
pooled estimate it is divided by.

**Anchor**:
The valuation diagonal `k` at which the triangle is cut: cells with `origin + development <= k`
are known, everything beyond it is a prediction.

**Depth**:
How far a cell sits beyond the anchor, `(development - 1) - (anchor - origin)`, and the x-axis
the arm regresses log error against.

**Arm**:
One experimental track with its own rows and comparison — the `depth arm`, the `pooled arm` or
the `control arm`.

### Governance

**Re-runnable**:
Same artifact plus same inputs gives the same outputs; the signed, numpy-only bundle satisfies
this.

**Retrainable**:
The fit can be reproduced from data; the bundle does not satisfy this, because no trainer,
writer, hyperparameters or seeds ship.
