# Alpha findings

Dated, evidence-backed observations from actually using 19th. Each entry names what was
run, so a claim can be rechecked rather than taken on trust. Report anything here to
founders@19th.com with the run ID.

---

## 2026-10-29 — first end-to-end run (MCP route)

**Connection.** `opencode mcp list` → `19th connected`. `get_capabilities` →
`available: true`. Account was empty (0 runs, 0 projects) before this run.

**Run.** "Predict malignant tumor diagnosis" · `run_id` `01a18547-020c-7ef0-b800-51f5775af602`
· dataset = `data/breast_cancer_diagnostic.csv` (569 rows, 30 numeric inputs)
· `task: binary`, `output_kind: event_probability`, `positive_label: malignant`
· `training_mode: standard`.

### What worked

| Fact | Value |
| --- | --- |
| Validation | 569 rows, 569 labelled / 0 unlabelled, 30 effective inputs, 0 excluded, 0 warnings |
| Build time | 6.1 s (`started_at` 01:29:48.56 → `finished_at` 01:29:54.66); 8.8 s submit-to-done |
| Models returned | Fast, Turbo, Warpspeed — all `delivery_state: ready` |
| Export sizes (tfpb) | Fast 377,408 B · Turbo 193,536 B · Warpspeed 52,992 B |
| Quality vs Fast | Turbo −0.0049 pts · Warpspeed −0.0163 pts |
| Prediction time (1 row) | Fast 0.0185 ms · Turbo 0.0097 ms · Warpspeed 0.0029 ms |
| Prediction time (1,000 rows) | Fast 1.57 ms · Turbo 0.88 ms · Warpspeed 0.39 ms |
| Hosted prediction | `inference_state: ready` for all three |

The whole MCP loop — `prep_run(create)` → signed PUT → `prep_run(finalize)` →
`submit_run` → `get_results` — completed with no retries and no manual polling hacks.

### Local bundle verified

Downloaded the Fast bundle and checked it rather than trusting the handoff:

- 1,452,402 bytes, SHA-256 `5c4a9566…4d5fcbc` — matched the reported size and digest exactly.
- Bundle contents: `predict.py`, `requirements.txt`, `model-interface.json` (schema
  `oracle_inference.v4`), `models/model.npz` + `models/model.tfpb`, signed manifest
  (`oracle-bundle-manifest.v1.json` / `.sig`) and signing cert, plus a vendored runtime.
- Runtime `oracle_numpy.v1`, `runtime_api tfp-runtime-0.9`. `requirements.txt` is just
  `numpy==2.2.6` — no TensorFlow, despite the `.tfpb` extension.
- Ran `predict.py --format tfpb` on 3 rows in a dedicated venv (local numpy is 1.26.4;
  the bundle pins 2.2.6 exactly). Output shape:
  `{classes, labels, ordinal_values, diagnostics, runtime_api, predictions[]}` with
  per-row `label`, `probabilities`, `event_probability`.
- The 3 predictions matched the actual labels 3/3, at 0.985 / 0.9999 / 0.994 confidence.

---

## 2026-10-29 — held-out evaluation: the full effort curve

Training on 456 rows, scoring on **113 rows never shown to the model**. Split is
`scripts/split_data.py`, seed 42, stratified (`data/train.csv` / `data/holdout.csv`).
Scoring is `scripts/score.py`; every bundle SHA-256 verified before use. All four modes ran
off one shared preparation, so data, target and declaration are identical and only effort
changes.

| Mode | Build | tfpb bytes | Accuracy | ROC AUC | Log loss | Brier | TP/FP/TN/FN |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `instant` | 4.1 s | 96,320 | 0.9735 | 0.9983 | 0.0770 | 0.0216 | 41/2/69/1 |
| `standard` | 6.1 s | 377,408 | 0.9735 | 0.9987 | 0.0648 | 0.0173 | 41/2/69/1 |
| `high` | 12.0 s | 377,408 | 0.9735 | 0.9983 | 0.0588 | 0.0160 | 41/2/69/1 |
| `ultra` | 22.0 s | 377,408 | 0.9735 | 0.9983 | 0.0551 | 0.0149 | 41/2/69/1 |

Warpspeed at `high` for comparison: 0.9735 accuracy, 0.9987 AUC, log loss 0.0631,
Brier 0.0173 — same confusion matrix again.

Runs: `01a1854f-fbd4-73d9-a109-710514edd9cf` (instant),
`01a1854d-ec55-7986-aa4e-3a11b0e0fb6b` (standard),
`01a1854d-ef3e-75a7-8b89-3fff2bfab9e9` (high),
`01a1854f-ffa9-75ec-ab43-58e0119e6664` (ultra).

### The model is genuinely good

97.35% accuracy, ~0.9985 AUC, 1 false negative in 42 malignancies, at every effort level. So
the 0.985 probabilities from the first run were meaningful — 19th produces a usable model on
this data. That question is settled rather than assumed.

### Training effort changes calibration, never classification

Across four modes spanning 5× the build time, the confusion matrix never moved: 41 true
positives, 2 false positives, 69 true negatives, 1 false negative, every time. Accuracy,
precision, recall and F1 are identical to four decimals.

What does improve is calibration, monotonically:

| Step | Log loss | Δ | Brier | Δ | Build cost |
| --- | --- | --- | --- | --- | --- |
| `instant` → `standard` | 0.0770 → 0.0648 | −0.0122 | 0.0216 → 0.0173 | −0.0043 | 4.1 s → 6.1 s |
| `standard` → `high` | 0.0648 → 0.0588 | −0.0060 | 0.0173 → 0.0160 | −0.0013 | 6.1 s → 12.0 s |
| `high` → `ultra` | 0.0588 → 0.0551 | −0.0037 | 0.0160 → 0.0149 | −0.0011 | 12.0 s → 22.0 s |

Half the calibration gain is bought by the first step, then the returns halve again each
time while build time keeps climbing. AUC is flat noise across all four (0.9983–0.9987), not
monotonic, so it is useless for choosing a mode.

**Practical read:** use `standard` unless calibrated probabilities are the product — risk
scores, cost-sensitive thresholds, anything where 0.06 vs 0.05 log loss changes a decision.
If you only need labels, `instant` is a quarter of `standard`'s build time and file size for
the same predictions.

### `instant` uses a smaller architecture

Its Fast model exports at 96,320 bytes against 377,408 for the other three, and predicts
in ~0.005 ms/row versus ~0.019 ms. `standard`, `high` and `ultra` share one compact-network
family and therefore identical file sizes and prediction times — consistent with the
capability descriptions, which say `high` and `ultra` reuse Standard's compact networks.

### The `quality.difference_points` metric did not predict holdout behaviour

Warpspeed on `high` was reported at **−0.1077 points** versus Fast. On 113 held-out rows it
produced the same confusion matrix, the same accuracy, the same precision/recall/F1, and a
nominally *equal* AUC (0.9987 vs 0.9987); its log loss was better than standard Fast's
(0.0631 vs 0.0648). Whatever that penalty measures, it did not surface as worse
classification on this data.

### `high` and `ultra` warned; `instant` and `standard` did not

Both `high` and `ultra` returned: *"Additional training limitation recorded; review the data
and model suitability before relying on predictions."* The `instant` and `standard` runs on
identical bytes returned no warnings. There is no way to read what the limitation was — the
field is prose with no code or detail — and it fires on the modes you are told to prefer for
accuracy.

### Caveat on statistical power

113 holdout rows means one flipped prediction moves accuracy by 0.9 points, and WDBC is a
famously separable dataset. Identical confusion matrices are consistent with near-equivalence
between modes, but this test is not powerful enough to prove equivalence. The calibration
ordering, by contrast, is monotonic across four independent runs, which is harder to dismiss
as noise — though it is still one dataset. A harder problem with more rows (Kepler KOI, say)
would test both claims properly.

---

## 2026-10-30 — the reserving arm, and what the model file gives away

19th was tested against a real actuarial problem: fill the unknown corner of a loss triangle. The full record
lives in the wayfinder map (`#1` and its children); this section keeps only what is about 19th as a product.

**Headline:** 19th can model a loss triangle, and on matched cells it reproduces the same depth-dependent bias
as TabPFN — slope `+0.0493` (se `0.0018`) against the control's `+0.0478` (se `0.0016`), difference `+0.0015`,
`z = +0.62`. The bias is not a property of the model class, and 19th offers no modelling edge here.

Two representation limits showed up that no amount of fitting repairs:

- **A column cannot be declared categorical.** `prep_run` offers `column_types` only for embeddings and infers
  everything else physically. Integer identifiers are read as `numeric`; the same values written as text
  (`"d1"`) are read as `categorical`. So the typing is carried by the serialisation, not by the schema, and must
  be maintained on every prediction row as well as every fit.
- **A constant column is dropped without a warning in the run output.** `global_factor_available` was excluded —
  *"one value only in the labelled rows"* — so the model trains on 7 inputs where the arm has 8, and the flag that
  literally encodes "this factor was unobservable / I am extrapolating" is gone.

## 2026-10-31 — model internals are readable

The bundle is Apache-2.0 source plus a plain `.npz`. In the arm's `fast` model:

- **144 arrays.** `hidden0.weight` (256, 44), `hidden1.weight` (256, 256), `hidden2.kron_a` / `kron_b` (1, 16, 16),
  a spline/knots quantile head, and per-column category embeddings.
- **A compact 256-wide MLP** with Kronecker-factorised layers and a spline output head — `LAYER_KINDS = ("dense",
  "kron")`, `PBLD` piecewise-linear number encoding. Not a foundation model.
- **An explicit unseen-category bucket** per categorical column: `unseen = len(spec["vocab"]) + 1`
  (`runtime/tfp/predict.py:340`), assigned to any value absent from the vocabulary.

That last line explains a result that otherwise looks mysterious: at anchor 3 every one of the 1,200 prediction
rows carried an unseen development category (`unseen_category_counts: {dev_idx: 900, cal_idx: 1200}`), because
the training rows only contain `dev_idx` 1..3. Depth is encoded in a categorical column, so depth extrapolation
happens **through that unseen bucket**, not through any learned depth response.

You can inspect and port the model; you cannot retrain it, and the `.tfpb` writer is not shipped.

---

## 2026-11-03 — results endpoint unavailable

`get_results` failed with `UPSTREAM_ERROR` (*apiserver request failed*, `retryable: true`) on
every attempt in this session: more than fifteen calls across four run ids
(`01a1854d-ec55…`, `01a1854f-fbd4…`, `01a18547-020c…`, `01a18f08-b649…`), a fresh correlation id
each time (`37f131cffe88fedddbc90b67`, `c3a7eea42cdb1430ed3ebf89`, `4a996c1ddff95c6539ee3ef2`).

`list_runs` still returned all eight runs as `succeeded`, and `get_skill`, `get_capabilities`,
`get_runtimes`, `get_download_options`, `list_skills` and `prep_run(action="template")` all
responded normally. So the runs were healthy and the outage was specific to the results read path,
not to the account or the connection.

It blocked more than it looked: no bundle could be re-downloaded to re-verify its contents, which
is why [`research/fit-record.md`](../research/fit-record.md) §3.2 rests on the alpha's 2026-10-29
record rather than a fresh check. Recoverable by retrying, but there is no fallback — see
finding 16.

---

## Findings

### 1. A single target comes back as `target_columns`

Send `target_column: "diagnosis"`, and `csv_receipt.prediction` returns
`target_columns: ["diagnosis"]`. Anything that reads the receipt expecting
`target_column` will see `undefined`. Cost: one blocked submission in this session, caught
by a pre-submit guard. **Client code should read `target_columns` on the explicit CSV route.**

### 2. Zero-label assistance is advertised but unreachable from the CSV route

`get_capabilities` reports `zero_label_assistance_available: true`, while the same payload
says it is *"not part of the direct CSV route"* and *"a separate legacy capability"*. The
alpha invite and the REST docs both advertise `spec.labeling` ("we label a sample, then
train"). On the route this connection actually offers, **at least two labelled rows are
required** and registration measured 569/569 labelled. Unlabelled data is not the easy
start the docs imply.

### 3. `class_label` on MCP, `binary_label`/`multiclass_label` on REST

Live capability outcomes are `class_label` (with `task: binary | multiclass`). The REST
Training API docs use `binary_label` and `multiclass_label` as distinct `output_kind`
values. Same product, two vocabularies — a direct source of client bugs.

### 4. `integer_tfpb` is advertised but off

`get_capabilities` lists export format `integer_tfpb`, and every model reported it as
`state: "off"` with `failure_code: "EXPORT_UNAVAILABLE"`. The capability list describes an
export that does not actually produce files.

### 5. No accuracy metric is returned

Results give `quality.difference_points` — relative to Fast, on this dataset — but no
absolute score. There is no accuracy, precision, recall, AUC or confusion matrix anywhere in
`get_results`. So "0.985 probability" cannot be judged good or bad from the API alone, and
there is no way to compare training modes without exporting models and scoring them
yourself. **Biggest gap found in this session.**

Workaround now in this repo: `scripts/split_data.py` + `scripts/score.py`. Measured baseline
on held-out data: 0.9735 accuracy, 0.9987 AUC. See the evaluation section above.

### 6. Download links expire in ~5 minutes

Every download URL carried `X-Goog-Expires=299`. A link handed to a user and opened a few
minutes later is dead. `get_model(run_id, model_id)` issues a fresh one, so this is
recoverable but easy to trip over when scripting.

### 7. Bundle runtimes are not all verified

`all_bundle_runtimes_ready: false` while `runtimes_available: true`. Reusable SDK runtimes
exist; the full bundle/serving-contract set is not yet verified. Untested here — these runs
used each bundle's own `predict.py`, not a standalone SDK.

### 8. `quality.difference_points` is not a predictor of held-out performance

Warpspeed was scored −0.1077 points against Fast and then classified all 113 holdout rows
identically, with equal AUC. Treat the number as a relative hint, not a quality guarantee,
and score the exported bundle before choosing a variant.

### 9. Mode buys calibration, not accuracy

Across `instant`, `standard`, `high` and `ultra` — a 5× build-time span — the confusion
matrix never moved (41/2/69/1). Only calibration improved, monotonically (log loss 0.0770 →
0.0648 → 0.0588 → 0.0551), with the gain halving at each step. Default to `standard`; pay for
`high`/`ultra` only when calibrated probabilities are the actual product. `instant` is a
quarter of the size and build time for identical labels.

### 10. Prediction-time and size metadata are per-variant constants, not measurements

The reported `row_ms` and tfpb sizes are identical to five decimal places across every run
that shares an architecture family — 0.01854 / 0.00968 / 0.00292 ms and 377,408 / 193,536 /
52,992 B for `standard`, `high` and `ultra`; 0.00501 / 0.00292 / 0.00188 ms and 96,320 /
52,992 / 31,360 B for `instant`. They vary between families but never between runs or
datasets, so they describe the variant, not the run. The field is labelled
`basis: "reference_cpu_estimate"`, which is honest, but it means the numbers cannot be used
to compare two runs of the same mode or to check a real latency claim.

### 11. Training-limitation warnings are opaque and fire on the recommended modes

`high` and `ultra` both returned *"Additional training limitation recorded; review the data
and model suitability before relying on predictions."* on identical bytes that produced no
warning at `instant` or `standard`. No code, no field, no explanation — nothing actionable,
and it appears precisely on the modes sold as more accurate.

### 12. Concurrent upload slots are capped, and the message reads like a hard failure

Creating several preparations at once is refused:

```
CONFLICT: the requested operation conflicts with current resource state
(reason=UPLOAD_SLOT_QUOTA)
```

The reason is named but the limit is not, and `retryable: false` reads permanent. It is not:
draining the create-upload-finalize cycle one at a time works, and replaying a refused create
with the **same idempotency key** recovers the existing preparation instead of allocating
another. Any multi-fit campaign must serialise the cycle.

### 13. A constant column is dropped silently

`global_factor_available` was excluded from training with *"one value only in the labelled
rows"*, reported in `excluded_inputs` rather than as a warning. In a designed feature set this
removes signal without an alarm, and the model's input count becomes 7 where the caller
declared 8.

### 14. Column typing is carried by the serialisation, not the schema

No request field declares a column categorical. Integer identifiers are typed `numeric`; the
same values written as text are typed `categorical`. A schema-level decision has to be
smuggled through the data format, and the same typing must be reproduced on every prediction
row or the model sees a numeric feature it never trained on.

### 15. Depth extrapolation runs through an unseen-category bucket

With categorical identifiers, every prediction row carried a development level absent from
the fit rows (`unseen_category_counts: {dev_idx: 900, cal_idx: 1200}` of 1,200). The runtime
assigns those to a dedicated bucket, `unseen = len(spec["vocab"]) + 1`. Depth-dependent
behaviour therefore comes from the model's response to an unknown category, not from any
learned depth response — worth knowing before reading anything into a depth-based metric.

### 16. The download path sits behind `get_results`, with no fallback

`get_model` and `request_download` both take a `model_id` handle, and the only tool that returns
one is `get_results`. So while the results read path is down, **nothing can be downloaded at
all** — not a bundle, not an option list, not a renewal of an expired link. `list_runs` keeps
reporting the runs as `succeeded`, which makes the failure look like a dead run rather than an
unreachable endpoint.

There is no independent route: no "list my models" call, no model id derivable from the run id.
Scripting around it means retrying `get_results` until it recovers, so any campaign that
downloads bundles should treat a results outage as a hard stop with retries, not as a per-run
failure to be worked around by starting another run — starting another run would allocate an
upload slot (finding 12) and still end at the same endpoint.

---

## Open questions for 19th

1. Is there any absolute quality signal planned (holdout accuracy/AUC), or should users
   always export and score themselves?
2. Should `integer_tfpb` be listed as available when every export is `EXPORT_UNAVAILABLE`?
3. Can `target_column` and `target_columns` be made consistent across the REST and MCP
   routes?
4. Is the labelling workflow reachable at all for a private-alpha CSV user, or only via
   the legacy capability?
5. What does `quality.difference_points` actually measure? Warpspeed at −0.1077 classified
   every holdout row identically to Fast at 0 points.
6. What is the "additional training limitation" that `high` and `ultra` warn about, and why
   do `instant` and `standard` on identical bytes not report it?
7. Why is reported prediction time identical across runs within a mode, and independent of
   the data?
8. Should the docs say plainly that training mode moves calibration but not classification?
   The mode descriptions promise accuracy differences this test did not find.
9. Is there any way to declare a column categorical, or is text encoding the intended path?
   If text encoding is intended, it should be documented as the contract.
10. Should `excluded_inputs` raise a warning rather than an informational field? A dropped
    designed feature is a correctness event, not a note.
11. What is the intended limit on concurrent upload slots, and can the error say so?
12. Is the unseen-category bucket intended to carry extrapolation, or is depth-as-a-category
    a representation the team expects callers to avoid?
