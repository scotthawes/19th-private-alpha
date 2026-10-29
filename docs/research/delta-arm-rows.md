# The delta arm: the rows, the target, and how to rebuild them

Research spec for ticket #3 (`scotthawes/19th-private-alpha#3`), written so a model trained
outside `tabpfn-reserving` can be fitted on the *same rows* without reopening the code.

**Source of truth.** `scotthawes/tabpfn-reserving` at commit `247f4ad` (working tree clean
when read). Every claim below carries a `file:line` reference into that repo. Paths are
relative to its root unless stated.

**What "the delta arm" means here.** The *recursive* link-ratio arm with
`target="delta"` — one prediction per development cell, each cell's ratio multiplied into
the running level. It is the arm whose per-step error produced
`results/runs/20260918-023600_depth-bias/FINDINGS.md`. The *direct* arm (#18, one row per
origin) is a different arm and is only documented in §10, to stop it being confused with
this one.

**Scope.** §1–§7 describe the computation. §8 is the file spec. §9 lists the traps. §11
says what could not be determined.

---

## 0. The one-paragraph answer

For every valuation diagonal `anchor = k` in a window of anchors, take every
*observed* one-column transition `C[a,d-1] -> C[a,d]` with `a+d <= k`, compute the link
ratio `C[a,d]/C[a,d-1]`, divide it by Chain Ladder's volume-weighted factor for that same
step, and fit one model per `(triangle, k)`. The eight feature columns are the cell's
origin/development/calendar indices, the origin's level and last ratio *at the anchor*,
and the Chain Ladder factor for the step. The label is therefore a **one-period link
ratio normalised by Chain Ladder's own factor**, where `1.0` reproduces Chain Ladder
exactly. The measured arm fits one model per `(triangle, anchor)` on the anchors
`k = 3 .. n-2`; it predicts by walking diagonals forward and multiplying.

---

## 1. The triangle: what the indices index

`Triangle.values` is an `(n, n)` array of **cumulative** losses, `NaN` above the observed
staircase (`triangle.py:22-33`). All indices are **0-based array positions**, not
`tri.ages` labels:

- `a` — accident period, the row index, `0 .. n-1`.
- `d` — development period, the column index, `0 .. n-1`.
- `C[a,d]` = `tri.values[a,d]`.

A valuation-date staircase (origin `i` observes ages `0 .. n-1-i`, no gaps) is what every
sample has, and the user-CSV loader refuses a file that does not (`triangle.py:97-105`);
`Triangle.load` of the bundled samples does not re-run that check, it inherits the shape.
`tri.ages` (e.g. `12, 24, ... 132` for `abc`) is **never read by any feature builder** —
`dev_idx` is `d`, not `tri.ages[d]`. See §9.1.

Cells "known at the anchor" are defined once, in `Triangle.known(anchor)`
(`triangle.py:244-251`):

```
known[a,d]  <=>  a <= anchor  and  a + d <= anchor  and  isfinite(C[a,d])
```

so the anchor is the *diagonal index* `k = a + d` of the last observed diagonal, and
`anchor = n-1` means "the latest diagonal".

**Triangles used in the recorded depth-bias run** (`depth_bias.py:201`, `results/.../depth_bias.json`):

| name | fixed shape | fingerprint `sha256_16` | anchor window used |
| --- | --- | --- | --- |
| `abc` | 11 x 11 | `bc97a934645b8bb0` | 3..9 |
| `genins` | 10 x 10 | `f5a238fd5403e5a6` | 3..8 |

`fingerprint()` is `triangle.py:175-183` (SHA-256 of the rounded numeric block, not of the
file). `mcl` is not in the recorded depth-bias run; where the fleet code touches it, the
column is named explicitly as `incurred` (`depth_bias.py:216`).

---

## 2. Which cells become training rows

`training_rows(tri, anchor, gf, target="delta", shuffle=False, mode="frozen")`
(`triangle.py:358-392`) is the entire fit-set builder:

```
for a in range(n):                       # triangle.py:373
    for d in range(1, n):                # triangle.py:374
        if not (known[a,d] and known[a,d-1]): continue      # 375
        prev_val, cur = C[a,d-1], C[a,d]                     # 377
        if prev_val <= 0 or not isfinite(cur): continue      # 378
        ratio = cur / prev_val                               # 380
        if target == "delta":
            base, _ = gf_used(d, anchor, gf)                  # 382
            if base <= 0: continue                           # 383-384
            ratio = ratio / base                             # 385
        X.append(features_for(tri, a, d, anchor, gf, C, mode=mode))   # 386
        y.append(ratio)                                      # 387
```

Consequences, all checkable:

- **Only observed transitions.** `known` requires `a+d <= k`, so every fit row has both
  cells observed at the anchor. Nothing is imputed.
- **Origin `a = k` contributes no rows** (it needs `d >= 1`, which breaks `a+d <= k`).
  Hence the per-anchor row count is `k(k+1)/2`, and the row set starts at `a = 0`.
- **Row order is `a` ascending, `d` ascending within `a`** (`373-374`). Fit order does not
  change a TabPFN result, but the spec below keeps it so two people produce the same file.
- `mode` defaults to `"frozen"`; every recorded run uses the default (see §9.6).

---

## 3. The eight feature columns

`FEATURES` is declared once at `triangle.py:296-297`, and the vector is built at
`triangle.py:343`:

| # | name | definition (at row `(a,d)` for anchor `k`) | type |
| --- | --- | --- | --- |
| 0 | `origin_idx` | `a` | integer-valued float |
| 1 | `dev_idx` | `d` (column index, **not** the age label) | integer-valued float |
| 2 | `cal_idx` | `a + d` (the calendar/valuation diagonal of the cell being predicted) | integer-valued float |
| 3 | `latest_cum` | `C[a, min(k-a, n-1)]` = the origin's **anchor-diagonal cell** | float, currency |
| 4 | `log_latest_cum` | `log1p(max(latest_cum, 0.0))` | float |
| 5 | `own_last_ratio` | `C[a,k-a] / C[a,k-a-1]` when `k-a >= 1` and the denominator `> 0`, else `NaN` | float or NaN |
| 6 | `global_factor_prev` | `gf_used(d, k, gf)[0]` — the Chain Ladder factor for step `d-1 -> d` (`triangle.py:342`, `313-321`) | float |
| 7 | `global_factor_available` | `gf_used(d, k, gf)[1]` — `1.0` if the factor existed at the anchor, `0.0` otherwise | 0.0 / 1.0 |

Exact definitions for 3–5 are `triangle.py:337-341`:

```
last_age       = min(anchor - a, n - 1)
latest         = running[a, last_age]
prev           = running[a, last_age - 1]     if last_age >= 1
own_last_ratio = latest / prev                if last_age >= 1 and prev > 0
```

In the **fit set** `running` is `tri.values` (`triangle.py:386`), so `latest` is the
observed anchor-diagonal cell and `own_last_ratio` is the observed ratio *into* the anchor
diagonal — the same value for every row of that origin, and unrelated to the label's own
step. It is `NaN` only when `k-a = 0`; since `a = k` contributes no fit rows, **the fit set
contains no NaN in `own_last_ratio`** for `abc`/`genins` (verified, §8.4).

`gf_used` (`triangle.py:313-321`) is the single shared source of "which factor am I
entitled to see":

```
j = d - 1
if j <= anchor and isfinite(gf[j]):   return (gf[j], 1.0)
else:                                 return (gf[anchor] if finite else 1.0, 0.0)
```

`gf` itself is `Triangle.global_factors(known)` (`triangle.py:253-275`): for each `j`, the
**volume-weighted** factor

```
gf[j] = sum_{a': known[a',j] and known[a',j+1] and C[a',j] > 0} C[a',j+1]
      / sum_{a': same set}                                     C[a',j]
```

then the last finite factor is **carried forward** into every later `j` (`triangle.py:269-274`).
At anchor `k`, `gf[k]` can never be computed (it needs an origin with both `a+k` and
`a+k+1` known, and `a+k <= k` forces `a = 0`, which fails the second condition), so `gf[k]`
is always the carried-forward value of the last genuinely observed factor — normally the
copy of `gf[k-1]`. This matters for prediction (§7) and is one of the traps in §9.3.

**Identifier columns.** `IDENTIFIER_FEATURES = ["origin_idx","dev_idx","cal_idx"]` and
`IDENTIFIER_INDICES = [FEATURES.index(name) for name in IDENTIFIER_FEATURES]` = `[0,1,2]`
(`triangle.py:299-304`). They are positions derived from names, so reordering `FEATURES`
moves them. They are only *declared categorical* when
`make_model(categorical_identifiers=True)` (`arm.py:55-57`) — **no recorded run does
this**; the recorded constructor is bare `arm.make_model("local")` =
`TabPFNRegressor(device="cpu")` (`arm.py:55-60`, `depth_bias.py:250`, and
`results/runs/abc-reserve-delta.json`'s command). In every recorded number the three
identifiers travelled as float columns on a numeric scale.

**Worked example** — `abc`, `k = 3` (all six fit rows, produced from the repo). `gf` at
this anchor is `[2.242734, 1.392810, 1.183506, 1.183506, ...]`:

| a | d | cal | latest_cum | log_latest | own_last_ratio | gf_prev | avail | actual_ratio | **target** |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 1 | 1 | 564040 | 13.2429 | 1.183506 | 2.242734 | 1 | 2.226337 | 0.992689 |
| 0 | 2 | 2 | 564040 | 13.2429 | 1.183506 | 1.392810 | 1 | 1.393317 | 1.000364 |
| 0 | 3 | 3 | 564040 | 13.2429 | 1.183506 | 1.183506 | 1 | 1.183506 | 1.000000 |
| 1 | 1 | 2 | 563842 | 13.2425 | 1.392380 | 2.242734 | 1 | 2.268159 | 1.011336 |
| 1 | 2 | 3 | 563842 | 13.2425 | 1.392380 | 1.392810 | 1 | 1.392381 | 0.999692 |
| 2 | 1 | 3 | 469340 | 13.0591 | 2.233120 | 2.242734 | 1 | 2.233123 | 0.995715 |

Row 1 reads: from age 0 to 1 for origin 0, the observed ratio was 2.226337 and Chain
Ladder's factor was 2.242734, so the delta label is 0.992689 — "0.7% below CL".

---

## 4. The target

**Yes, it is a link ratio — over exactly one development column — divided by Chain
Ladder's factor for that same column.**

```
actual_ratio  = C[a,d] / C[a,d-1]                        # triangle.py:380
target_delta  = actual_ratio / gf[d-1]                   # triangle.py:382-385
```

with `gf[d-1]` computed from the anchor's triangle as in §3 (volume-weighted, ratio of
column sums). Three properties a reimplementation must not lose:

1. **Interval.** The numerator and denominator are adjacent columns, `d-1` and `d`. The
   code never reads calendar time; for `abc`/`genins` the columns are annual
   (`tri.ages = 12..132/120`), so it is a 12-month development factor, but for a monthly
   triangle it is one month. Do not reconstruct the interval from `tri.ages`.
2. **Normalisation is by a factor computed on the same anchor, not on the full triangle.**
   `gf` is built from `tri.global_factors(tri.known(k))` (`depth_bias.py:247`,
   `replicate_depth_bias.py:72`), so a training row at an earlier anchor sees a factor
   built from less data than the same cell at a later anchor.
3. **`target = 1.0` is exactly Chain Ladder.** This is the design intent stated at
   `triangle.py:363-364` and `arm.py:199-203`: the arm predicts a *correction*, and a model
   that outputs 1.0 everywhere reproduces CL. The `--target ratio` arm is the same label
   without the division (`triangle.py:507-508`).

For the fit set, `d-1 <= k-a-1 < k`, so the denominator is always the **observed** factor
branch of `gf_used` — never the carried-forward fallback. The fallback only appears in
prediction rows (§7).

---

## 5. Depth

`depth` is defined in one place, in the trace of the prediction loop
(`arm.py:342`):

```
depth(a, d, k) = (d - 1) - (k - a)
```

Equivalently: **how many development steps the cell sits beyond the origin's last
observed cell at the anchor.** It is per-origin, not a global recursion counter.

| situation | `d` | depth |
| --- | --- | --- |
| fit row (last observed transition for that origin) | `d = k-a` | **-1** |
| fit row, earlier transition | `d < k-a` | `-2, -3, ...` down to `-(k)` for `a=0` |
| first predicted cell for origin `a` | `d = k-a+1` | **0** |
| deepest *scorable* cell at anchor `k` | `d = n-1-a` | `n-2-k` |
| last cell of the production recursion | `d = n-1` | `n-2-k+a` |

So:

- **Every training row has `depth <= -1`.** The FINDINGS phrasing "every training row sits
  at depth <= 0" (`FINDINGS.md:3-4`) is true but loose; the exact statement is `<= -1`, and
  the closest row to the prediction regime is the last observed transition at `-1`.
- **Production starts at depth 0 and, for a 10-origin triangle (genins, n=10), the youngest
  origin at the latest diagonal `k = n-1 = 9` runs depths `0..8` — i.e. "steps 1 through 9"**
  (`FINDINGS.md:4-5`). For `abc` (n=11) it is 10 steps. Nothing in the code measures depth
  by counting loop iterations; it is always `d - 1 - (k - a)`.
- **The anchor window determines the reachable depth.** With anchors `3 .. n-2` the deepest
  scorable cell is `n-2-3 = n-5` (6 for abc, 5 for genins). Anchoring near the ultimate
  (`n-4 .. n-2`) reaches only depth 2 — the "anchoring trap" at `FINDINGS.md:38-46`.
- `mode="running"` reuses the same arithmetic as a feature, `steps = d - 1 - (anchor - a)`
  (`triangle.py:348`), so the two definitions cannot drift.

---

## 6. The anchor window actually used

Recorded run: `results/runs/20260918-023600_depth-bias/`.

- `run.log:4` — `abc: anchors [3, 4, 5, 6, 7, 8, 9] -- deepest step reachable is depth 6`
- `run.log:12` — `genins: anchors [3, 4, 5, 6, 7, 8] -- deepest step reachable is depth 5`

which is `anchors = list(range(3, n - 1))`, i.e. **from `k = 3` to the last-but-one
diagonal `k = n-2`** — never the latest diagonal. The replication harness recovers the
policy explicitly (`replicate_depth_bias.py:3-9`, `:65`, `:69`) and
`results/runs/20260919-depth-bias-replication/run.log` reproduces `n=287`, slope
`+0.03168`.

**Caveat, recorded rather than smoothed:** `run.log:2` says "the last 3 anchors below the
ultimate, per triangle", which contradicts the anchors it then prints. The originating
script default is indeed the last three (`depth_bias.py:203-207`, `:241-242`); the recorded
run must have passed `--anchors-from 3` and did not log it. The anchor list in the log and
the reproduction are the evidence; the literal command line is not recoverable. See §11.1.

For contrast, other entry points use different windows and are **not** this dataset:
`cli.py:155` backtests `range(n//2, n-2)`; `cli.py:90` trains the direct arm on
`range(2, n-1)`. Fit on `3..n-2` or the numbers are not comparable.

---

## 7. Prediction, scoring, and the error definition

The measured run fits one model per anchor and then calls
`arm.reserve(model, tri, k, 0, rng, target="delta", trace=trace)` — zero draws, trace on
(`depth_bias.py:249-255`, `replicate_depth_bias.py:73-77`).

### 7.1 The recursion (`arm.py:302-333`)

```
gf      = tri.global_factors(tri.known(k))      # arm.py:304, computed once
running = tri.values.copy()                     # arm.py:305
for diag in range(k+1, 2n-1):                   # arm.py:311
    coords = [(a, diag-a) for a in range(n) if 1 <= diag-a < n and a <= k]   # 312
    X = [features_for(tri, a, d, k, gf, running, mode=mode) for (a,d) in coords]  # 315
    point = model.predict(X)                    # 317-318
    for (a,d):
        prev = running[a, d-1]                  # 325
        if not (isfinite(prev) and prev > 0): continue      # 326-327
        base, _ = gf_used(d, k, gf)             # 328
        r_hat = point[i] * base                 # 329   (delta rescaling)
        if not (isfinite(r_hat) and r_hat > 0): r_hat = 1.0  # 330-331
        running[a, d] = prev * r_hat            # 332
```

Key points:

- **Predicted raw ratio** = model output × `global_factor_prev`, and that is the *same*
  column the fit target was divided by. This is the only place the rescaling happens; do
  not recompute `gf` from the projected triangle.
- **`gf` is frozen at the anchor** (`arm.py:304`), never mutated as `running` fills in.
- **A skipped cell leaves `NaN`** (`continue` at `327` before any write), so every later
  cell of that origin is skipped too. In the scored triangles this never triggers.
- **A non-positive or non-finite prediction silently becomes 1.0** (`330-331`) — i.e. the
  arm falls back to Chain Ladder for that step. Any comparison must know this can happen.
- In `mode="frozen"` the feature vector for `(a,d)` does **not** depend on `running`'s
  projected cells at all (verified, §8.4): `last_age = min(k-a, n-1) = k-a` is always an
  observed diagonal cell. So a prediction CSV can be built from the observed triangle
  alone.

### 7.2 What the trace records (`arm.py:334-349`)

```
actual        = C[a,d]
actual_ratio  = C[a,d] / C[a,d-1]  if finite and C[a,d-1] > 0 else NaN     # 338-340
log_error     = ln( r_hat / actual_ratio )  if both finite and > 0 else NaN # 341-347
row = {origin, dev, depth, predicted_ratio=r_hat, actual_ratio,
       prev_observed=C[a,d-1], log_error, base_observed=C[a,anchor-a]}
```

- **The error is `ln(predicted raw ratio / actual observed ratio)`**, per step. `r_hat` is
  the rescaled raw ratio, *not* the model's delta output; comparing the delta output to
  `actual_ratio` would be a category error.
- `prev_observed` is the **observed** cell `C[a,d-1]`, not the projection's own previous
  level. For depth > 0 those differ.
- Cells beyond the observed diagonal are still traced, with `actual_ratio` and `log_error`
  `NaN`; the run filters `isfinite(log_error)` before scoring (`depth_bias.py:255`,
  `replicate_depth_bias.py:78`). Only `d <= n-1-a` survive.
- `base_observed = C[a, k-a]`, constant per origin.

### 7.3 Exposure and weighting

- **In the fit: none.** Every row has weight 1; no `sample_weight`, no oversampling.
- **In the diagnostic:** `decompose()` (`scripts/depth_bias.py:124-182`) computes, per depth
  (`:138-161`):
  - exposure `= sum of prev_observed` (`:148`) — i.e. observed currency `C[a,d-1]`;
  - `mean_log_error` — unweighted mean of `log_error`, the number in the FINDINGS table;
  - `exposure-weighted log error` `= Σ prev_observed · log_error / Σ prev_observed`
    (`:152`, `:158-159`) — the "exposure-weighted" column in `FINDINGS.md:10-18`;
  - `currency_residual = Σ prev_observed · (predicted_ratio - actual_ratio)` (`:151`).
- **Per-origin reconstruction** (`:163-181`): starting from `base_observed`, multiply the
  predicted ratios (and separately the actual ratios) along the origin's steps, then
  compare increments. This is where compounding appears; the per-depth table is
  single-step only. `FINDINGS.md:50-61` explains why the two differ.
- Because the per-depth weight uses the *observed* `prev_observed` even at depth > 0, the
  exposure column is a fixed-weight diagnostic, not the exposure the step actually acts on
  inside the projected path. The compounding is carried by the by-origin reconstruction,
  not by the weighted column.

---

## 8. The CSV spec

Two files. Both are derivable from the triangle alone plus the recorded anchor window; no
model is needed to produce them. Column names for the eight features are *exactly* the
`FEATURES` names and must stay in `FEATURES` order so a loader can do `df[FEATURES]`.

### 8.1 `delta_train.csv` — the fit set

One row per observed one-step transition per anchor. Sort: `triangle`, `anchor`,
`origin_idx`, `dev_idx`.

| column | type | meaning |
| --- | --- | --- |
| `triangle` | str | sample name (`abc`, `genins`, …) |
| `column_name` | str | `Triangle.columns[0]` — `"values"` for `abc`/`genins`, `"incurred"` for `mcl` |
| `n` | int | triangle size |
| `anchor` | int | `k` |
| **`origin_idx`** | float (`a`) | feature 0 |
| **`dev_idx`** | float (`d`) | feature 1 |
| **`cal_idx`** | float (`a+d`) | feature 2 |
| **`latest_cum`** | float | feature 3, `C[a, k-a]` |
| **`log_latest_cum`** | float | feature 4, `log1p(max(latest,0))` |
| **`own_last_ratio`** | float | feature 5, `C[a,k-a]/C[a,k-a-1]` (no NaN in these samples) |
| **`global_factor_prev`** | float | feature 6, `gf[d-1]` |
| **`global_factor_available`** | float 0/1 | feature 7, **always 1.0 in the fit set** |
| `depth` | int | `d-1-(k-a)`, always `<= -1` |
| `prev_cum` | float | `C[a,d-1]` — the exposure weight |
| `actual_ratio` | float | `C[a,d]/C[a,d-1]` |
| `target_delta` | float | `actual_ratio / global_factor_prev` |

Fit: `X = df[FEATURES]`, `y = df.target_delta`. **Fit one model per `(triangle, anchor)`**
— that is the recorded unit (`depth_bias.py:245-251`). Pooling anchors or triangles into
one fit is a different experiment: the same cell appears under several anchors with
different `latest_cum`, `own_last_ratio`, `global_factor_prev` and label.

### 8.2 `delta_steps.csv` — the scored cells

One row per projected cell, so predictions can be joined and scored. Emit
`a in 0..k`, `d in k-a+1 .. n-1` (the full recursion), and keep the rows with
`d <= n-1-a` for scoring; the rest are the tail of the reserve path and have no actual.

Same metadata + feature columns as §8.1, plus:

| column | type | meaning |
| --- | --- | --- |
| `depth` | int | `>= 0` for these rows |
| `prev_observed` | float | `C[a,d-1]`; `NaN` once `d-1` itself is unobserved |
| `actual_ratio` | float or NaN | `C[a,d]/C[a,d-1]`; `NaN` when unobserved |
| `base_observed` | float | `C[a,k-a]` |
| `predicted_ratio` | float | **join**: `y_hat_delta × global_factor_prev` |
| `log_error` | float or NaN | **join**: `ln(predicted_ratio / actual_ratio)` |

Notes that make this file exact:

- `own_last_ratio` is `NaN` for the **youngest origin `a = k`** at prediction time
  (`last_age = 0`), e.g. `abc k=3, a=3` has `own_last_ratio = NaN` for every step. Leave it
  `NaN`; do not impute.
- `global_factor_available` is `1.0` iff `depth <= a`, else `0.0` (from `j = d-1 <= k`).
  For `a = 0` it flips to `0.0` at depth 1 and stays there; for larger `a` it stays `1.0`
  for the first `a+1` steps. This is **not** "1 at depth 0, 0 afterwards".
- `global_factor_prev` for `depth > a` is `gf[k]`, the carried-forward last observed
  factor — the same constant for every deep step.
- `predicted_ratio` for the recursion is `running[a,d-1] * (y_hat × global_factor_prev)`;
  the recursion's level and the ratio are separate quantities.

### 8.3 Pseudocode an implementer can follow

```python
C = triangle_values                    # (n, n), NaN above the staircase
for k in range(3, n - 1):              # recorded window, §6
    known = (a <= k) & (a + d <= k) & isfinite(C[a, d])
    gf = [ nan ] * n
    for j in range(n - 1):
        den = sum(C[a, j]     for a if known[a,j] and known[a,j+1] and C[a,j] > 0)
        num = sum(C[a, j + 1] for a if known[a,j] and known[a,j+1] and C[a,j] > 0)
        if den > 0: gf[j] = num / den
    last = nan
    for j in range(n):                 # carry the last finite factor forward
        if isfinite(gf[j]): last = gf[j]
        elif isfinite(last): gf[j] = last

    # features for any (a, d) at this anchor
    def features(a, d):
        age   = k - a
        latest = C[a, age]
        prev   = C[a, age - 1] if age >= 1 else nan
        own    = latest / prev if (age >= 1 and prev and prev > 0) else nan
        j      = d - 1
        if j <= k and isfinite(gf[j]): gprev, avail = gf[j], 1.0
        else:                          gprev, avail = (gf[k] if isfinite(gf[k]) else 1.0), 0.0
        return [a, d, a + d, latest, log1p(max(latest, 0.0)), own, gprev, avail]

    for a in range(n):                 # ---- fit rows
        for d in range(1, n):
            if not (known[a, d] and known[a, d - 1]): continue
            p, c = C[a, d - 1], C[a, d]
            if p <= 0 or not isfinite(c): continue
            gprev = features(a, d)[6]  # the same factor, so label and feature cannot disagree
            if gprev <= 0: continue
            emit_train_row(features(a, d), C[a,d]/p/gprev, depth=d-1-(k-a), prev_cum=p)

    for a in range(k + 1):             # ---- projected cells (for scoring)
        for d in range(k - a + 1, n):
            emit_step_row(features(a, d), depth=d-1-(k-a), prev_observed=C[a,d-1],
                          actual_ratio=(C[a,d]/C[a,d-1] if d <= n-1-a else nan),
                          base_observed=C[a, k-a])
```

### 8.4 Checksums (all verified against the repo in this session)

| check | expected |
| --- | --- |
| train rows `abc`, anchors 3..9 | 161 (`6,10,15,21,28,36,45`) |
| train rows `genins`, anchors 3..8 | 116 (`6,10,15,21,28,36`) |
| scored steps `abc` | 168 (`28,30,30,28,24,18,10`) |
| scored steps `genins` | 119 (`24,25,24,21,16,9`) |
| scored steps, pooled | **287** |
| steps per depth (0..6) | **88, 69, 52, 37, 24, 13, 4** |
| `global_factor_available` in the fit set | all `1.0` |
| `latest_cum` / `own_last_ratio` NaN in the fit set | 0 / 0 |
| fit depth values | `-k .. -1` for each anchor |
| frozen feature rows that change when predicted cells are corrupted | 0 |

The 287 / depth histogram is the same arithmetic that produced `FINDINGS.md:10-18` and
`results/.../depth_bias.json`, reproduced here **without a model** from the triangle and
the anchor window alone.

---

## 9. What a reimplementation will silently get wrong

1. **`dev_idx` is a column index, not an age.** `features_for` writes `d`
   (`triangle.py:343`); `tri.ages` (`12, 24, …`) is never consulted. Feeding ages gives a
   different dataset with the same column names. Same for `origin_idx` (`a`, not the year
   label) and `cal_idx` (`a+d`, not a calendar year).
2. **`global_factor_available` has no variance in the fit set.** It is `1.0` on every fit
   row because training rows satisfy `d-1 < k` (`triangle.py:319`). Its information is
   entirely about the prediction regime, where it flips at `depth = a+1`, not at
   `depth = 1`. A reimplementation that computes "available = depth==0" will match the fit
   set perfectly and be wrong at prediction.
3. **`gf` is volume-weighted and forward-filled, and frozen at the anchor.** Ratio of
   column sums (`triangle.py:261-268`), last finite factor carried forward
   (`269-274`), computed once per anchor (`arm.py:304`) and never updated as the projection
   runs. Any of: averaging per-origin ratios, re-estimating after each projected diagonal,
   or dropping the carry-forward (leaving `NaN`) changes both the label and the rescaling.
4. **The label denominator and the prediction multiplier are the same number.** Fit:
   `target = actual_ratio / global_factor_prev` (`triangle.py:382-385`). Predict:
   `predicted_ratio = y_hat * global_factor_prev` (`arm.py:328-329`). If those two use even
   slightly different `gf` definitions, the model is trained and deployed on different
   quantities and the `1.0 = Chain Ladder` property disappears.
5. **`IDENTIFIER_INDICES = [0,1,2]` is positional and the recorded runs never declare them
   categorical.** `triangle.py:303-304`, `arm.py:55-57`. Treating them as categories is a
   *different* arm (#22), not a faithful reimplementation; treating `cal_idx` as a float
   is what the recorded numbers did.
6. **The prediction is recursive in the level, not in the features (frozen mode).**
   `running[a,d] = running[a,d-1] * r_hat` (`arm.py:332`) compounds the level; but
   `features_for` reads `running[a, min(k-a, n-1)]`, always the observed diagonal, so the
   feature vector is identical at every depth for a given origin apart from
   `dev_idx`/`cal_idx`/`global_factor_available` (`arm.py:338-341`; asserted in
   `tests/test_reserving.py:288-320`, and verified numerically here). A 19th model given
   the same columns therefore sees depth only as a linear ramp on two indices. Feeding the
   projected level back is `mode="running"`, a different arm.
7. **`log_latest_cum` is `log1p`, not `log`.** `np.log1p(max(latest, 0.0))`
   (`triangle.py:343`). At `abc` levels the two differ by about `1.8e-6` absolutely
   (`log1p(564040)` vs `log(564040)`): small, but not zero, and not a rounding detail to
   change silently.
8. **`own_last_ratio` is the ratio *into the anchor diagonal*, not the ratio at the cell
   being predicted.** It is constant for the whole projection of an origin, and it is `NaN`
   for `a = k` at prediction time. A reimplementation that computes "the previous step's
   ratio" from `d-2 -> d-1` will look plausible on the fit set (where it coincides at
   `d = k-a`) and diverge everywhere else.
9. **Filters are part of the dataset.** Skip if either cell not known at the anchor; skip
   if `prev <= 0` or `cur` non-finite; skip the delta row if `gf <= 0`
   (`triangle.py:375-384`). At prediction: skip a cell if the running previous level is
   not finite or `<= 0`, and clamp a non-finite/non-positive `r_hat` to `1.0`
   (`arm.py:325-331`). Dropping either filter changes row counts and can change reserves.
10. **The reserve and the scored steps are not the same set.** The recursion runs to
    `d = n-1` for the reserve (`arm.py:311`, targets `[n-1]*n`, `arm.py:303`,
    `target_ages` at `triangle.py:526-538`), but only `d <= n-1-a` have actuals. Reporting
    "every traced step" as scored inflates the count and inserts NaNs. Conversely,
    `target_ages(n, "backtest")` = `n-1-a` is the *scoring* convention and is what the
    `--backtest` CLI uses (`cli.py:167`); mixing the two is the documented zero-reserve
    bug (`triangle.py:529-533`).
11. **The recorded anchor window is not any CLI default.** `3 .. n-2` is specific to the
    depth-bias harness (§6). `cli.py:155` and `cli.py:90` use other windows.
12. **`training_rows(shuffle=True)` shuffles `y` only** (`triangle.py:390-391`) — it is a
    label-permutation null control, not row shuffling. Never use it for a real fit.

---

## 10. The direct arm, to avoid confusing it with this one

`direct_predict_rows` (`triangle.py:514-523`) belongs to **arm #18**, not the delta arm.
It exists because the ticket asks about it; it is not part of the depth-bias dataset.

- Features are `DIRECT_FEATURES = FEATURES + ["horizon", "log_chainladder_factor"]`
  (`triangle.py:399`), one row per origin, computed at the *first unobserved* cell
  `(a, k-a+1)` with `features_for(..., mode="frozen")` (`triangle.py:422-423`).
- `horizon = max(target_age - (k-a), 0)` and `log_chainladder_factor` is the log of the
  product of `gf[j]` from `k-a` to `target_age-1` (`triangle.py:402-411`, `424-426`).
- `direct_predict_rows` **skips every origin whose target age is not beyond its current
  age** (`triangle.py:518-520`); with production targets (`[n-1]*n`, `triangle.py:534-535`)
  the oldest origin is excluded at the latest diagonal.
- `reserve_direct` un-does the CL normalisation with `cl = exp(X[:,-1])` and
  `factors = point * cl` (`arm.py:225`, `229-236`); the point is a single factor, no
  compounding.
- Its fit set is `direct_training_rows(anchors, target="delta", known_until=..., ...)`
  (`triangle.py:429-511`), which **pools anchors into one fit** (`:477-478`) and, by
  default, keeps only the ceiling target age per origin (`:487`). That is the opposite
  design from the delta arm's one-fit-per-anchor.
- Its depth is a *different quantity*: `t - age`, the span of one whole prediction
  (`depth_bias.py:116`), and the docs say the two slopes are not comparable
  (`depth_bias.py:81-92`).

---

## 11. What I could not determine

1. **The recorded run's literal command line.** `run.log:2` describes a different anchor
   policy ("the last 3 anchors below the ultimate") from the anchors it prints
   (`run.log:4`, `:12`). The `--anchors-from` flag that produced `3..n-2` is not logged;
   the policy is *recovered* from the printed anchors and the replication
   (`replicate_depth_bias.py:3-9`, `:69`), and reproduces the recorded `n=287` and slope
   `+0.03168`. Treat the flag values as inferred, the anchor list as observed.
2. **Exposure is not in the recorded JSON per row.** `FINDINGS.md:65-67` says
   `depth_bias.json` holds "currency exposure" per step, but the rows carry
   `prev_observed` (and `base_observed`) and no `exposure` field. The exposure table in
   `FINDINGS.md:10-18` is recomputed from `prev_observed` by `depth_bias.py:148-159`, and
   the recomputed values match the FINDINGS. The per-row exposure column is absent, not
   wrong.
3. **Whether two `gf` summation orders agree bit-for-bit.** `global_factors` accumulates
   in a Python loop over origins in ascending order (`triangle.py:262-268`). I verified the
   values to the precision printed here but did not test bitwise equality against a
   vectorised `sum()`. If byte-identical CSVs matter, accumulate in the same order.
4. **The production "nine steps" claim is size-dependent.** It is nine for a 10-origin
   triangle and ten for `abc` (11 origins). The FINDINGS states it for the fleet's 10x10
   containers; I could not find a place where the code hard-codes 9.
5. **Which triangles the 19th comparison should use.** The recorded depth-bias run used
   `abc` + `genins` only (`depth_bias.py:201` sets a wider default, but `run.log:1` shows
   these two). The broader fleet (`fleet_eval.py`) uses trimmed containers and additional
   columns; that is a different dataset and is not specified here.

---

## 12. Provenance

**Code read (all line references above):**

- `src/tabpfn_reserving/triangle.py` — triangle, `known`, `global_factors`, `gf_used`,
  `features_for`, `training_rows`, direct-arm builders, `target_ages`.
- `src/tabpfn_reserving/arm.py` — `make_model`, `reserve` (the recursive arm and its
  trace), `reserve_direct`.
- `src/tabpfn_reserving/cli.py` — how a run is invoked and what the recorded defaults are.
- `scripts/depth_bias.py` — the recorded run's harness, anchor policy, and exposure
  decomposition.

**Recorded artefacts:**

- `results/runs/20260918-023600_depth-bias/{run.log,depth_bias.json,FINDINGS.md}` —
  anchors, 287 scored steps, per-depth table, slope `+0.03168 (se 0.00363)`.
- `results/runs/20260919-depth-bias-replication/{replicate_depth_bias.py,run.log,depth_bias.json}`
  — the replication and the recovered anchor policy.
- `results/runs/abc-reserve-delta.json` — the production delta run: `anchor = 10`,
  `features = frozen`, `draws = 300`, `distribution_route = exact`,
  `draws_method = bar-bins`, command `tabpfn_reserving abc --target delta --distribution …`.
- `docs/method.md` — the pre-registered method (no hyperparameter, distribution from the
  same forward pass, features restricted to the valuation date). It does not fix the delta
  target or the anchor window; those live in the code and the run records cited above.

**Verification performed while writing this** (with the repo's `.venv`, `chainladder`
0.10.1): reloaded `abc`/`genins`, reproduced the fingerprints, the 161+116 fit-row counts,
the 168+119=287 scored-step counts and the 88/69/52/37/24/13/4 depth histogram without a
model; confirmed `global_factor_available == 1.0` on every fit row, no NaNs in
`latest_cum`/`own_last_ratio` in the fit set, and that corrupting projected cells leaves
frozen feature rows unchanged.

**Not done, per the ticket:** no comments posted, no issue closed, `tabpfn-reserving`
untouched, no pull request opened.
