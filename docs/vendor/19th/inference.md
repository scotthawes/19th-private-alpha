# Inference API

Send records or a CSV and get predictions. Call your model's prediction URL, or download the model and run it in your app with our SDK.

[Create an API key ↗](https://app.19th.com/api-keys)

The link opens **API Keys** in your dashboard after sign-in. If you need an account, choose **Sign up**, complete email verification, then return to the same link. You can reuse the authorized Training key you used for fit when calling its returned model-version prediction URL. For an existing endpoint, select **New Key** under **Inference API** and allow access to that endpoint. Save the secret when it appears; it is shown only once. See [account access](/docs#get-access) if you are new to 19th.

## Endpoint

<span id="authentication"></span>
<span id="make-a-prediction"></span>


```http
POST https://inference.get19th.com/v1/models/{model_id}/versions/{model_version_id}/predictions
Authorization: Bearer YOUR_INFERENCE_API_KEY
Content-Type: application/json
```

Set `PREDICTION_URL` to the exact `model.prediction.url` returned by fit. For an existing hosted endpoint, use `https://inference.get19th.com/v1/endpoints/YOUR_ENDPOINT_UUID/predictions`.

Keep the key in your backend.

Model-version routes accept a model inference key or an account or project training key with `inference:invoke`. Endpoint routes use project inference keys (`19th_inf_...`), which may restrict endpoints. Get keys from your workspace; MCP OAuth is separate.

Check `model.prediction.state`: `ready` → use its URL; `loading` → retry shortly; `unavailable` → hosted prediction is unavailable. Download readiness is separate.

## Request

Save this as `prediction-request.json`:


```json
{
  "input": [
    {
      "account_age_days": 365,
      "monthly_spend": 49.5
    }
  ],
  "metadata": {
    "source": "quickstart"
  }
}
```

<details class="schema-detail">
<summary>Send with curl</summary>

```sh
export INFERENCE_API_KEY="YOUR_AUTHORIZED_PREDICTION_KEY"
export PREDICTION_URL="PREDICTION_URL_RETURNED_BY_19TH"

curl --fail-with-body -sS "$PREDICTION_URL" \
  -H "Authorization: Bearer $INFERENCE_API_KEY" \
  -H "Content-Type: application/json" \
  -H "X-Request-Id: cancellation-example" \
  --data-binary @prediction-request.json
```

</details>

| Field | Required? | Meaning |
| --- | --- | --- |
| `input` | Required | One input object or an array; use the model's raw names and types, without target labels |
| `metadata` | Optional | Echoed string values, not predictor inputs: up to 16 keys, 1–64 UTF-8 bytes each; values up to 512 bytes |
| `model` | Optional | Must match the route's model identifier when supplied |

Unknown top-level fields are rejected. Send raw inputs, not engineered features.




## Response

A response for an event-probability model might look like this. `MODEL_ID` and `MODEL_VERSION_ID` stand for UUIDs returned by the API:


```json
{
  "id": "pred_example",
  "object": "prediction.list",
  "created": 1790000000,
  "model": "MODEL_ID",
  "model_version": "MODEL_VERSION_ID",
  "request_id": "cancellation-example",
  "output": [
    {
      "probability": 0.31
    }
  ],
  "usage": {
    "records": 1,
    "source_rows": 0
  },
  "metadata": {
    "source": "quickstart"
  }
}
```

Answers in `output` depend on the model. Keep class order and typed labels beside probabilities. `request_id` also appears in `X-Request-Id`; retain it for support. `usage` counts records and source rows.


<details class="schema-detail" id="additional-task-outputs">
<summary>Task-specific answers</summary>

These answers appear in JSON predictions, saved fit predictions and CSV batch delivery.

| Output | Main answer | Preserve with it |
| --- | --- | --- |
| Ordered category | `grade` | `label`, `classes`, probabilities, expected grade and supplied `ordinal_values`; grade can differ from the most likely label |
| Count | `prediction` | Supplied ranges and quantiles; expected counts may be fractional |
| Multiple labels | `positive` boolean vector | Ordered `labels` and matching probabilities |
| Ranking | `score` | `rank`, group and optional candidate metadata |

JSON returns task-specific objects in `output`. CSV puts the main answer in `prediction` and the full object in `prediction_details`; a multilabel main answer is a JSON boolean vector in one cell. Do not reorder axes, round counts or recalculate ranks.

Ranking requests include declared group and optional candidate metadata without target labels. Each group is ranked against that group’s candidates supplied in the JSON request. For CSV, keep each group's rows contiguous and small enough for one inference chunk; a group cannot reappear after another group. If a group or tracking limit is refused, reduce candidates or split the file while preserving whole groups.

</details>



## Batch inference

<span id="predict-from-a-csv"></span>

```http
POST https://inference.get19th.com/v1/models/{model_id}/versions/{model_version_id}/batch
Authorization: Bearer YOUR_INFERENCE_API_KEY
Idempotency-Key: YOUR_UNIQUE_REQUEST_KEY
Content-Type: multipart/form-data; boundary=...
```


Use a registered model version. Send `request` JSON first, then CSV `file` with the model's input columns; maximum 64 MiB (67,108,864 bytes).

| Request field | Required? | Meaning |
| --- | --- | --- |
| `wait` | Required | `true`: wait up to 45 seconds from request start, including upload. `false`: return without waiting |
| `inline` | Required | `false`: JSON and a CSV download link. `true`: JSON and CSV bytes in one multipart response when ready |
| `metadata` | Optional | The same echoed string map as JSON predictions |

Save the request as `batch-request.json`:

```json
{
  "wait": true,
  "inline": false
}
```

<details class="schema-detail">
<summary>Upload the CSV with curl</summary>

```sh
export INFERENCE_API_KEY="YOUR_AUTHORIZED_PREDICTION_KEY"
export INFERENCE_ORIGIN="https://inference.get19th.com"
export MODEL_ID="MODEL_UUID_RETURNED_BY_19TH"
export MODEL_VERSION_ID="MODEL_VERSION_UUID_RETURNED_BY_19TH"
BATCH_KEY="$(uuidgen)"

curl --fail-with-body -sS \
  "$INFERENCE_ORIGIN/v1/models/$MODEL_ID/versions/$MODEL_VERSION_ID/batch" \
  -H "Authorization: Bearer $INFERENCE_API_KEY" \
  -H "Idempotency-Key: $BATCH_KEY" \
  -F 'request=<batch-request.json;type=application/json' \
  -F 'file=@prediction-inputs.csv;type=text/csv' > batch.json
```

</details>

A pending response uses HTTP 202. `BATCH_ID` stands for the returned batch UUID:

```json
{
  "request_id": "batch-example",
  "batch_id": "BATCH_ID",
  "state": "processing",
  "status_url": "/v1/models/MODEL_ID/versions/MODEL_VERSION_ID/batch/BATCH_ID"
}
```

Poll the returned path with required `inline` and optional `wait_seconds` (0–45):

```sh
BATCH_STATUS_URL=$(jq -r '.status_url' batch.json)
curl --fail-with-body -sS \
  "$INFERENCE_ORIGIN$BATCH_STATUS_URL?inline=false&wait_seconds=45" \
  -H "Authorization: Bearer $INFERENCE_API_KEY" > batch.json
```

Reads return 200 with `processing`, `ready` or `failed`; a timeout leaves work running. On `ready`, follow `download.url`, verify `size_bytes` and `sha256`, and read status to refresh an expired link. Never send the API bearer to the download URL.

A completed result can look like this. `PREDICTIONS_SHA256` stands for the file’s SHA-256 fingerprint; other values are illustrative:

```json
{
  "request_id": "batch-example",
  "batch_id": "BATCH_ID",
  "state": "ready",
  "status_url": "/v1/models/MODEL_ID/versions/MODEL_VERSION_ID/batch/BATCH_ID",
  "rows": 10,
  "download": {
    "url": "https://download.example/predictions.csv",
    "expires_at": "2026-10-14T00:00:00Z",
    "format": "csv",
    "size_bytes": 2048,
    "sha256": "PREDICTIONS_SHA256"
  }
}
```

With `inline: true`, ready results are multipart: the same JSON in `result`, plus the CSV in `predictions`. Pending and failed outcomes stay JSON. Check Content-Type. Use `inline: false` for large files; the entire request and inline delivery have a 55-second budget.

The CSV keeps input columns and row order, adding `prediction` (the main answer) and `prediction_details` (the full answer as JSON text). Existing names get collision suffixes. Failed batches publish no partial file.


## Errors

Request errors return an HTTP error status and a JSON body with a request ID and actionable details:

```json
{
  "object": "error",
  "request_id": "cancellation-example",
  "error": {
    "type": "invalid_request_error",
    "code": "invalid_request",
    "message": "input is required",
    "param": "input",
    "retryable": false,
    "details": {}
  }
}
```

| Status | What to do |
| --- | --- |
| `400 Bad Request` | Correct the fields described in the error |
| `401 Unauthorized` | Check that your API key is present and valid |
| `403 Forbidden` | Check your key’s permissions, restrictions and project access |
| `404 Not Found` | Check the model/version or endpoint ID and your access |
| `409 Conflict` | The batch key belongs to different work; recover the original request |
| `413 Payload Too Large` | Reduce request size; split oversized CSVs |
| `429 Too Many Requests`, `503 Service Unavailable` | Honor Retry-After and retryable; retry batch submission with the original key and exact bytes |
| `502 Bad Gateway`, `504 Gateway Timeout` | Retain the request ID and use bounded retries for temporary failures |

Batch keys bind model/version, CSV bytes and metadata for seven days; `wait` and `inline` may change. Keep the returned batch handle after key expiry. Terminal status reads do not run prediction again. A saved batch failure can arrive with **200 OK**, so inspect `state` and `error`.

JSON defaults: 4 MiB, 1,000 records or 10,000 source rows, 30-second prediction timeout. Key/deployment limits also apply. Retry temporary failures as instructed; fix malformed inputs first.
