# Alpha test plan

What to exercise, in the order that finds problems fastest. Tick as you go; note the
`run_id` for anything that looks wrong, because that is what 19th will ask for.

## 0. Access

- [x] MCP connects, and `get_capabilities` succeeds for the **invited** email.
- [ ] Training key created at https://app.19th.com/api-keys and saved (shown once).

## 1. First model — tumor diagnosis

### MCP route — done 2026-10-29

- [x] `get_skill`, then `get_capabilities` → connection entitled
- [x] `prep_run(template)` → declaration; `prep_run(create)` → upload slot
- [x] Signed PUT of the exact bytes (124,839 B, digest pinned)
- [x] `prep_run(finalize)` → `csv_receipt`, 0 issues, offered modes all four
- [x] `submit_run` standard → succeeded in 6.1 s
- [x] Fast/Turbo/Warpspeed returned, all delivery-ready
- [x] Fast bundle downloaded: size and SHA-256 matched
- [x] Bundle `predict.py` ran locally on 3 rows → 3/3 matched actual labels

Details and caveats in [`alpha-findings.md`](alpha-findings.md).

### REST route — not yet exercised

The smallest useful loop for `fit.py`, and the one that proves auth + upload + fit + predict:

- [ ] `python3 scripts/make_demo_data.py`
- [ ] `fit.py` with `--output-kind event_probability --positive-label malignant --mode standard`
- [ ] Submission returns `200` immediately, or `202` and polls to `ready`
- [ ] Inline `predict` records come back with probabilities
- [ ] `--download` saves `model.tfpb` and the size/sha256 verify
- [ ] `predict.py --run-dir runs/latest` returns the same answer as the inline prediction

## 2. Prediction types

Each `output_kind` takes a different target shape. One run each, `--mode instant` to keep it
cheap:

- [ ] `binary_label` — tumor diagnosis
- [ ] `multiclass_label` — support intents (77 classes)
- [ ] `numeric_value` — any numeric target
- [ ] `event_probability` with `positive_label`
- [ ] `ordered_class` — needs `order`, lowest to highest
- [ ] `count_value` — nonnegative whole-number target
- [ ] `label_set` — ordered `target_columns`, no `target_column`
- [ ] `ranking_score` — needs `group_column`, optional `candidate_column`

## 3. Training modes

- [x] `standard` and `high` on the same split — 6.1 s vs 12.0 s, identical confusion matrix
- [ ] `instant` on the same dataset — compare against the above
- [ ] `ultra` on one dataset — docs claim 2–3× the time of `high`; verify
- [ ] Same dataset with `--model-variant turbo` / `warpspeed` if the account offers them
      (Warpspeed on `high` scored identically to Fast — see findings)

### Holdout scoring — done 2026-10-29

- [x] Deterministic stratified split (`scripts/split_data.py`, seed 42)
- [x] Train on 456 rows, score on 113 unseen rows (`scripts/score.py`)
- [x] Baseline: 0.9735 accuracy, 0.9987 AUC, 1 false negative in 42 malignancies
- [ ] Repeat on a harder dataset where modes can actually be separated

## 4. Behaviour under interruption

These are the ones the docs warn about, so they are worth proving rather than assuming:

- [ ] Replay a completed request with the **same** `--key` and identical CSV → recovers the
      existing run, does not train a second model
- [ ] Replay with a changed CSV under the same key → expect `409`
- [ ] `wait=false` returns `202`; polling never restarts work
- [ ] Cancel a running fit (`POST /v1/fit/{run_id}/cancel`) → `state` becomes `cancelled`
- [ ] Download URL expiry → re-read the run for a fresh link

## 5. Errors and limits

- [ ] Wrong target column → `400` with a readable `issues` field
- [ ] Target listed as an input → rejected
- [ ] Ungzipped CSV over the upload limit → `413`, and the message states the limit
- [ ] `request` part after `file` → `415` (this is why the scripts pin part order)
- [ ] Bad key → `401`; key without `inference:invoke` → inline `predict` refused
- [ ] Multi-GB / very wide CSV → note where it actually breaks

## 6. Inline predictions and batch inference

- [ ] `predict` with 1, 100, 1,000 records — find the practical ceiling
- [ ] `POST /v1/models/{model}/versions/{version}/batch` with a CSV, `wait: true`
- [ ] Batch with `inline: false` → follow `status_url`, download CSV, verify sha256
- [ ] Confirm the CSV keeps input columns and row order, adds `prediction` +
      `prediction_details`

## 7. Taking the model into a project

- [ ] `GET /v1/model-runtimes`, install a returned SDK
- [ ] Load `model.tfpb` with that SDK and reproduce a hosted prediction locally
- [ ] Request turbo/warpspeed through `/model-options` → `/model-downloads` and compare

## Notes

- Report anything surprising to founders@19th.com with the `run_id` and `request_id`.
- Keep `runs/<key>/request.json` — it is the exact bytes and key needed to rebuild a run.
