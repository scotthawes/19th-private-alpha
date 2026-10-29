# Alpha test plan

What to exercise, in the order that finds problems fastest. Tick as you go; note the
`run_id` for anything that looks wrong, because that is what 19th will ask for.

## 0. Access

- [ ] MCP connects, and `get_capabilities` succeeds for the **invited** email.
- [ ] Training key created at https://app.19th.com/api-keys and saved (shown once).

## 1. First model — tumor diagnosis

The smallest useful loop, and the one that proves auth + upload + fit + predict.

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

- [ ] `instant`, `standard`, `high` on the same dataset — compare wall-clock and quality
- [ ] `ultra` on one dataset — docs claim 2–3× the time of `high`; verify
- [ ] Same dataset with `--model-variant turbo` / `warpspeed` if the account offers them

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
