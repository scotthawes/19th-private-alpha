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

## 2026-10-29 — held-out evaluation: `standard` vs `high`

Training on 456 rows, scoring on **113 rows never shown to the model**. Split is
`scripts/split_data.py`, seed 42, stratified (`data/train.csv` / `data/holdout.csv`).
Scoring is `scripts/score.py`; bundles verified by SHA-256 before use.

| Model | Mode | Build | Accuracy | ROC AUC | Log loss | Brier | TP/FP/TN/FN |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Fast | `standard` | 6.1 s | 0.9735 | 0.9987 | 0.0648 | 0.0173 | 41/2/69/1 |
| Fast | `high` | 12.0 s | 0.9735 | 0.9983 | 0.0588 | 0.0160 | 41/2/69/1 |
| Warpspeed | `high` | 12.0 s | 0.9735 | 0.9987 | 0.0631 | 0.0173 | 41/2/69/1 |

Runs `01a1854d-ec55-7986-aa4e-3a11b0e0fb6b` (standard) and
`01a1854d-ef3e-75a7-8b89-3fff2bfab9e9` (high), one shared preparation.

### The model is genuinely good

97.35% accuracy, 0.9987 AUC, 1 false negative in 42 malignancies. So the 0.985
probabilities from the first run were meaningful — 19th produces a usable model on this
data. That question is now settled rather than assumed.

### Escalating the mode bought nothing measurable

`standard` → `high` doubled build time (6.1 s → 12.0 s) and changed **no hard prediction
at all**: identical confusion matrix, identical accuracy, identical precision/recall/F1.
AUC moved from 0.9987 to 0.9983 — noise, and slightly in the wrong direction. Log loss
improved (0.0648 → 0.0588), so `high` is mildly better calibrated even where it classifies
identically.

The models are genuinely different, not the same file twice: 0/113 rows were bit-identical
between them, with a mean probability difference of 0.0076 and a max of 0.077.

### The `quality.difference_points` metric did not predict holdout behaviour

Warpspeed on `high` was reported at **−0.1077 points** versus Fast. On 113 held-out rows it
produced the same confusion matrix, the same accuracy, the same precision/recall/F1, and a
nominally *equal* AUC (0.9987 vs 0.9987); its log loss was actually better than standard
Fast's (0.0631 vs 0.0648). Whatever that penalty measures, it did not surface as worse
classification on this data.

### `high` warned; `standard` did not

The `high` run returned: *"Additional training limitation recorded; review the data and
model suitability before relying on predictions."* The `standard` run on identical bytes
returned no warnings. There is no way to read what the limitation actually was — the field
is prose with no code or detail.

### Caveat on statistical power

113 holdout rows means one flipped prediction moves accuracy by 0.9 points, and WDBC is a
famously separable dataset. Identical confusion matrices are consistent with near-equivalence
between modes, but this test is not powerful enough to prove equivalence. A harder dataset
with more rows would be needed to separate 0.9987 from 0.9983 meaningfully.

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
there is no way to compare `standard` against `high` without exporting models and scoring
them yourself. **Biggest gap found in this session.**

Workaround now in this repo: `scripts/split_data.py` + `scripts/score.py`. Measured baseline
on held-out data: 0.9735 accuracy, 0.9987 AUC. See the evaluation section above.

### 8. `quality.difference_points` is not a predictor of held-out performance

Warpspeed was scored −0.1077 points against Fast and then classified all 113 holdout rows
identically, with equal AUC. Treat the number as a relative hint, not a quality guarantee,
and score the exported bundle before choosing a variant.

### 9. Mode escalation may cost build time for no accuracy gain

`standard` → `high` doubled build time and left the confusion matrix untouched on this
dataset. Worth defaulting to `standard` and only paying for `high`/`ultra` when a scored
holdout says it helps.

### 10. Prediction-time and size metadata look like constants, not measurements

Across two separate runs in two modes, the reported `row_ms` (0.01854 / 0.00968 / 0.00292)
and tfpb sizes (377,408 / 193,536 / 52,992 B) were identical to five decimal places. The
field is labelled `basis: "reference_cpu_estimate"`, so it is honest about being an estimate
— but it does not vary with mode or data, so it cannot be used to compare runs.

### 11. Training-limitation warnings are opaque

`high` returned *"Additional training limitation recorded; review the data and model
suitability before relying on predictions."* on identical bytes that produced no warning at
`standard`. No code, no field, no explanation — nothing actionable.

### 6. Download links expire in ~5 minutes

Every download URL carried `X-Goog-Expires=299`. A link handed to a user and opened a few
minutes later is dead. `get_model(run_id, model_id)` issues a fresh one, so this is
recoverable but easy to trip over when scripting.

### 7. Bundle runtimes are not all verified

`all_bundle_runtimes_ready: false` while `runtimes_available: true`. Reusable SDK runtimes
exist; the full bundle/serving-contract set is not yet verified. Untested here — this run
used the bundle's own `predict.py`, not a standalone SDK.

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
6. What is the "additional training limitation" that `high` warns about, and why does
   `standard` on identical bytes not report it?
7. Why is reported prediction time identical across modes and datasets?
