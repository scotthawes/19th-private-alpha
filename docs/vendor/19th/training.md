# Training API

Train a model and get predictions in the same call. Bring labeled or unlabeled examples.

[Create a Training API key ↗](https://app.19th.com/api-keys)

The link opens **API Keys** in your dashboard after sign-in. Choose **Sign up** and complete email verification if you need an account, then return to the same link and select **New Key** under **Training API**. Save the secret when it appears; it is shown only once. See [account access](/docs#get-access) if you need help signing in.

## Endpoint

<span id="availability"></span>
<span id="authentication"></span>
<span id="train-a-model"></span>

```http
POST https://training.19th.com/v1/fit
Authorization: Bearer YOUR_TRAINING_API_KEY
Idempotency-Key: YOUR_UNIQUE_REQUEST_KEY
Content-Type: multipart/form-data; boundary=...
```

Use an account or project training API key. Fit needs `training:write`; status and downloads need `training:read`. Optional predictions and the returned model-version prediction URL also require `inference:invoke`. Keep the key in your backend. No project UUID is needed.

Choose your own unique `Idempotency-Key` for each new training request; reuse it when retrying that request. Curl sets the multipart content type and boundary for you.

<details class="schema-detail">
<summary>Scopes and project access</summary>

| Scope | Allows |
| --- | --- |
| `training:write` | Submit fit or training and request cancellation |
| `training:read` | Read fit status, capabilities, runs, results and downloads |
| `data:write` | Create datasets and upload or finalize data in the staged workflow |
| `data:read` | Read datasets and preparation state |
| `models:read` | Discover SDK runtimes |

Project routes use the key's API project UUID. `training:projects` enables account-wide placement where granted; a run's `run_project_id` only groups runs and never grants access. [Hosted inference](/docs/inference) has separate key requirements.

</details>

## Request

Send two parts: `request` JSON first, then CSV `file`. The CSV holds training rows. Optional `predict` records are separate inputs to predict after training.

Use one flat table with a header row and the declared input columns. Keep known labels; use the optional labeling workflow only when the target is absent or empty. Training validates the columns, values and usable rows before fitting. Upload limits depend on the deployment; if a request returns `413`, follow the limit in its error and reduce the file before retrying.

This example labels customer training rows, trains a cancellation model and predicts one new customer. Omit `spec.labeling` when your CSV already has labels; omit `predict` when you only need the model. With labeling, the target column must be absent or empty. Save this as `fit-request.json`; the upload helper replaces `FILE_SHA256` and the sample byte count with the real file values.

```json
{
  "name": "Predict customer cancellation",
  "file": {
    "content_length": 12345,
    "sha256": "FILE_SHA256"
  },
  "spec": {
    "target_column": "churned",
    "input_columns": ["account_age_days", "monthly_spend"],
    "output_kind": "event_probability",
    "positive_label": "yes",
    "training_mode": "standard",
    "labeling": {
      "description": "Predict whether this customer will cancel in the next 30 days",
      "classes": ["no", "yes"]
    }
  },
  "model_variant": "fast",
  "wait": true,
  "inline": false,
  "predict": [
    {
      "account_age_days": 365,
      "monthly_spend": 49.5
    }
  ]
}
```

| Field | Required? | Meaning |
| --- | --- | --- |
| `name` | Required | A 2–7 word title, at most 80 characters |
| `file.content_length` | Required | Exact CSV byte count; calculated by the upload helper |
| `file.sha256` | Required | File fingerprint: 64 lowercase hex characters, without a prefix; calculated by the upload helper |
| `spec.target_column` | Conditional | Column to predict. Required except for `label_set`; see prediction types |
| `spec.input_columns` | Required | Columns available when predicting; exclude target, group and candidate columns |
| `spec.output_kind` | Required | Choose the kind of answer you need: a label, probability or number |
| `spec.positive_label` | Conditional | Required only for `event_probability`; match the label’s exact type |
| `spec.training_mode` | Required | instant, standard, high, or ultra; choose explicitly, no default |
| `spec.labeling` | Optional | Use for classification when your training rows have no labels. Describe what you want to predict and the possible answers; we label a sample, then train your model |
| `model_variant` | Optional | fast (default); turbo or warpspeed when offered by the model menu |
| `wait` | Required | true: wait up to 85 seconds after upload acceptance. false: return without waiting |
| `inline` | Required | false: JSON with a model download link. true: the same JSON plus model bytes when ready |
| `predict` | Optional | Send new inputs alongside your training data to get predictions from the trained model in the same result. Up to 1,000 records; requires a training key with `inference:invoke`. Omit when you only need the model |

`spec.training_mode` controls training effort independently of `model_variant`, which selects the model file used for downloads and predictions.

Ultra is the most accurate model we build. It takes longer than High, about 2–3x on typical tables, and gives the same file sizes and prediction speed as High.

Prediction records use exactly the declared input columns, with scalar or null values. Ranking records also include their declared group and optional candidate fields.

<details class="schema-detail">
<summary>Upload with curl</summary>

Requires `curl`, `jq` and `uuidgen`. Keep the key and request for retries. `sha256` is the file fingerprint: 64 lowercase hex characters, without a `sha256:` prefix. Curl sets multipart headers automatically.

```sh
export TRAINING_ORIGIN="https://training.19th.com"
export TRAINING_API_KEY="YOUR_TRAINING_API_KEY"
export DATASET_FILE="customers.csv"
FIT_KEY="$(uuidgen)"
FILE_BYTES=$(wc -c < "$DATASET_FILE" | tr -d '[:space:]')
FILE_SHA256=$(shasum -a 256 "$DATASET_FILE" | cut -d ' ' -f 1)

jq --argjson bytes "$FILE_BYTES" --arg sha256 "$FILE_SHA256" \
  '.file = {content_length: $bytes, sha256: $sha256}' \
  fit-request.json > request.json

curl --fail-with-body -sS "$TRAINING_ORIGIN/v1/fit" \
  -H "Authorization: Bearer $TRAINING_API_KEY" \
  -H "Idempotency-Key: $FIT_KEY" \
  -F 'request=<request.json;type=application/json' \
  -F "file=@$DATASET_FILE;type=text/csv" > fit.json
```

</details>

<details class="schema-detail" id="unlabeled-examples">
<summary>Train with unlabeled data</summary>

The optional `spec.labeling` object in the request labels the training CSV, not the separate `predict` records. Keep `target_column` and `input_columns` explicit.

| Field | Required? | Meaning |
| --- | --- | --- |
| `spec.labeling.description` | Required | What to predict and what the classes mean; 1–4,000 characters |
| `spec.labeling.classes` | Required | 2–256 distinct, nonblank, non-null values of one scalar type. Include the exact positive_label for probabilities |

Inputs must exist. The target may be absent or entirely empty; any supplied value—including false, 0 or literal NA—refuses labeling. Use two classes for binary outputs, at least three for multiclass. Labeling supports `binary_label`, `multiclass_label` and `event_probability`. Omit it when you already have labels.

We label a sample, then train. `wait: true` covers labeling, training and delivery within the same 85-second limit; unfinished work returns 202 and continues in the background.

</details>

## Prediction types

Choose `spec.output_kind` for the answer you need. Every spec includes `input_columns` and `training_mode`.

<span id="additional-outputs"></span>

| `spec.output_kind` | What it predicts | Target and extra fields |
| --- | --- | --- |
| `binary_label` | One of two labels | `target_column` with exactly two values |
| `multiclass_label` | One of several labels | `target_column` with three or more values |
| `event_probability` | Chance of one outcome | Binary `target_column` and exact typed `positive_label` |
| `numeric_value` | A number | `target_column` with numeric labels |
| `ordered_class` | An ordered category, such as low, medium or high | `target_column` and `order`: 2–256 distinct values of one scalar type, lowest to highest |
| `count_value` | An expected count, such as visits | Nonnegative whole-number `target_column`. Optional `count_target`: auto, raw, log1p or log1p_qmean; predictions can be fractional |
| `label_set` | Several yes/no answers for each row | Ordered binary `target_columns`; omit `target_column` |
| `ranking_score` | Relative relevance within a group | Nonnegative `target_column`, `group_column` and optional `candidate_column` |

Exclude target, group and candidate columns from `input_columns`. For ranking, include the group and any declared candidate field in `predict` records.

<details class="schema-detail">
<summary>Request examples for ordered categories, counts, multiple labels and ranking</summary>

#### ordered_class

```json
{
  "target_column": "priority",
  "order": ["low", "medium", "high"],
  "input_columns": ["age_days", "amount"],
  "output_kind": "ordered_class",
  "training_mode": "standard"
}
```

#### count_value

```json
{
  "target_column": "visits",
  "input_columns": ["age_days", "amount"],
  "output_kind": "count_value",
  "training_mode": "standard"
}
```

#### label_set

```json
{
  "target_columns": ["urgent", "billing"],
  "input_columns": ["age_days", "amount"],
  "output_kind": "label_set",
  "training_mode": "standard"
}
```

#### ranking_score

```json
{
  "target_column": "relevance",
  "group_column": "query_id",
  "input_columns": ["age_days", "amount"],
  "output_kind": "ranking_score",
  "training_mode": "standard"
}
```

</details>

## Response

<span id="results"></span>

Completed work returns **200**. This result includes the model and the optional predictions requested above. Uppercase values stand for returned IDs, file fingerprints and the full hosted prediction URL. IDs are UUIDs; use `PREDICTION_URL` for [hosted predictions](/docs/inference). Values are illustrative:

```json
{
  "request_id": "fit-example",
  "run_id": "RUN_ID",
  "state": "ready",
  "status_url": "/v1/fit/RUN_ID?inline=false",
  "download_state": "ready",
  "model": {
    "model_id": "MODEL_ID",
    "model_version_id": "MODEL_VERSION_ID",
    "download": {
      "url": "https://download.example/model.tfpb",
      "expires_at": "2026-10-14T00:00:00Z",
      "format": "tfpb",
      "size_bytes": 28288,
      "sha256": "MODEL_SHA256"
    },
    "prediction": {
      "state": "ready",
      "url": "PREDICTION_URL"
    }
  },
  "predictions_state": "ready",
  "predictions": [
    {
      "input": {
        "account_age_days": 365,
        "monthly_spend": 49.5
      },
      "prediction": {
        "probability": 0.31
      }
    }
  ]
}
```

| Field | Meaning |
| --- | --- |
| `state` | preparing, training or packaging: work continues. cancelling: cancellation requested. ready, failed or cancelled: automatic work is finished |
| `model` | When a registered version is identified, keep model_id and model_version_id. Registered training is never reported as a failed fit |
| `download_state` | ready: download. pending: keep reading. unavailable: inspect error |
| `predictions_state` | When requested: ready: use predictions. pending: keep reading. failed: inspect predictions_error; the model remains usable |
| `model.prediction` | Hosted prediction readiness and URL, separate from download readiness |

A ready result can still have an unavailable download or failed optional predictions. Check these fields separately. Saved predictions preserve their input records and order.

With `inline: false`, the response is JSON with a download link. With `inline: true`, a ready fit and ready download return multipart: the same JSON in `result`, plus the model file in `model`. Pending and failed outcomes remain JSON. Check Content-Type before parsing; the multipart body itself is not a model file.

### Downloads and SDKs

<span id="models-and-sdks"></span>
<span id="getModelRuntimes"></span>
<span id="getModelDownloadOptions"></span>

Fit returns your selected model as a `.tfpb` file, without an SDK. **Fast** is the default. Once `download_state` is `ready`, use `model.download.url`:

```sh
DOWNLOAD_URL=$(jq -r '.model.download.url' fit.json)
curl --fail-with-body -sS "$DOWNLOAD_URL" -o model.tfpb
wc -c < model.tfpb
shasum -a 256 model.tfpb
```

Compare the byte count and SHA-256 with the response. Send the bearer only to the API, never to the download URL. Read fit again to refresh an expired link.

**SDK setup.** `GET /v1/model-runtimes` lists SDKs and platform requirements. Select a returned `runtime_id` with `GET /v1/model-runtimes?runtime_id=RUNTIME_ID` to get its download and setup instructions. Install a compatible SDK once and reuse it across models.

**Other model versions.** To download Fast, Turbo or Warpspeed, use your fit `run_id` with `GET /v1/training-runs/{run_id}/model-options`, then request your selection through `POST /v1/training-runs/{run_id}/model-downloads`. Use the option IDs returned by the list. This uses the same training run; it does not retrain.

<details class="schema-detail">
<summary>Download request example</summary>

`GET /v1/model-download-options` lists SDKs for custom bundles and returns `catalog_version`. Copy the exact `runtime_id` values and catalog version into the request. These are separate from the model option IDs above; uppercase values below are placeholders for returned values.

```http
POST https://training.19th.com/v1/training-runs/{run_id}/model-downloads
Authorization: Bearer YOUR_TRAINING_API_KEY
Content-Type: application/json
```

```json
{
  "model_ids": ["MODEL_OPTION_ID"],
  "format": "tfpb",
  "delivery": "archive",
  "runtime": {
    "mode": "selected",
    "targets": ["RUNTIME_ID"]
  },
  "catalog_version": "CATALOG_VERSION"
}
```

- `model_ids`: one or more option IDs from the run's model-options response.
- `delivery`: `archive` (default) packages the selected models and SDKs in a ZIP. `raw` returns one model file and requires `runtime.mode: "none"`.
- `runtime.mode`: `none` (default) excludes SDKs; `selected` includes the SDKs in `targets`; `all` includes the newest qualified compatible SDK release for each concrete target of the selected models. Omit `targets` for `none` or `all`.
- `catalog_version`: required for `selected` or `all`; copy it from the download-options response. Omit it for `none`. SDKs must support the selected models.

The response wraps the download in `data`. Keep `data.download_id` and read `GET /v1/training-runs/{run_id}/model-downloads/{download_id}` until `data.state` is `ready` or `failed`. When ready, `data.download` includes `url`, `bytes` and `sha256`; verify the downloaded file against them. If preparation fails, inspect `data.failure_code` and `data.retryable`. Repeat the same POST selection to retry a retryable failure. Status reads never restart preparation.

</details>

## Retrieve the result

<span id="api-reference"></span>
<span id="projectlessGetTrainingCapabilities"></span>

<span id="follow-the-result"></span>

Fresh `wait: false` submissions, or requests still running after 85 seconds, return **202**. Work continues; do not submit a new training job.

```json
{
  "request_id": "fit-example",
  "run_id": "RUN_ID",
  "state": "training",
  "status_url": "/v1/fit/RUN_ID?inline=false"
}
```

Poll the returned `status_url` on the same origin. It already includes required `inline`. Optional `wait_seconds` accepts 0–85:

```sh
STATUS_URL=$(jq -r '.status_url' fit.json)
curl --fail-with-body -sS "$TRAINING_ORIGIN$STATUS_URL&wait_seconds=85" \
  -H "Authorization: Bearer $TRAINING_API_KEY" > fit.json
```

Status reads and terminal submission replays return 200, including saved failures. Check state and error. A read timeout leaves the run running.

To cancel, POST `https://training.19th.com/v1/fit/{run_id}/cancel` with your bearer and an idempotency key, then read status to confirm. Registered models are unaffected.

<details class="schema-detail" id="other-training-workflows">
<summary>Staged uploads and training</summary>

`GET /v1/training-capabilities` lists the supported workflows:

| Workflow | Request and continuation |
| --- | --- |
| Upload and train | `POST /v1/projects/{project}/training-runs/upload`: multipart `spec` JSON first, CSV `file` second; required `Idempotency-Key`. Spec contains `file`, explicit `prediction`, `training_mode`, `run_name`, and optional `run_project_id`. Read the returned run after 202. |
| Stage preparation | Create a dataset with `prepared_training`; request its version upload slot; transfer bytes using returned method and headers; finalize; read until preparation is `ready`; submit `prep_id`, `run_name` and an offered `training_mode` to `POST /v1/training-runs/prepared`. |
| Resume or cancel | List with `intake=prepared`; read or cancel with `view=prepared` where declared. Use returned run handles, cursors and poll guidance. |

Project-free routes choose placement for eligible account keys and retain a project key's pin. Upload slots use top-level `version` and `upload`; most resources use `data`. Fit uses the result above. Other resource errors use their declared `error` envelope.

</details>

## Errors

Request errors return an HTTP error status and JSON with `code`, `message`, `retryable` and optional field `issues`. A saved training failure can arrive with **200 OK**; check `state` and `error`.

| Status | What to do |
| --- | --- |
| `400 Bad Request` | Correct the fields or data described in message and issues |
| `401 Unauthorized` | Check that your API key is present and valid |
| `403 Forbidden` | Check your key’s permissions and project access |
| `404 Not Found` | Check the resource ID and whether your key can access it |
| `409 Conflict` | This key belongs to a different request. Recover the original request, or use a new key for new work |
| `413 Payload Too Large` | Reduce the CSV size |
| `415 Unsupported Media Type` | Send multipart form data with request JSON first and CSV file second; let curl set the multipart headers |
| `429 Too Many Requests` | Honor Retry-After before retrying with the same request, bytes and key |
| `500 Internal Server Error`, `503 Service Unavailable` | Follow retryable and Retry-After when supplied; retain the request ID and retry the existing request |

For a saved <code class="error-code">TRAINING_FAILED</code> result, read message for the cause before submitting new work. For <code class="error-code">DOWNLOAD_UNAVAILABLE</code>, replay the original POST/key only when retryable to retry packaging; GET only reads status. Otherwise use hosted prediction if available, without retraining. <code class="error-code">MODEL_REVOKED</code> means the model can no longer be downloaded or invoked.

Keep the request JSON, CSV bytes, `Idempotency-Key` and `run_id`. The same key recovers the same run for seven days; only `wait` and `inline` may change. After expiry, read the saved run instead of resubmitting. If the submission response is lost, replay the exact request with the same bytes and key. Retrying recovers existing work; it does not mean starting a new training job.
