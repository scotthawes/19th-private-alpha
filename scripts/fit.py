#!/usr/bin/env python3
"""Train a model through the 19th Training API.

Mirrors https://19th.com/docs/training:

    POST https://training.19th.com/v1/fit
    multipart: `request` JSON first, CSV `file` second

A 202 is normal — the run keeps going in the background and this script polls the
returned `status_url` until it settles. Every artifact needed to replay the exact
request (request JSON, CSV fingerprint, idempotency key, run id) is written to
`runs/<idempotency-key>/`, because replaying the same key with the same bytes
recovers the same run for seven days.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import uuid

import common

OUTPUT_KINDS = (
    "binary_label",
    "multiclass_label",
    "event_probability",
    "numeric_value",
    "ordered_class",
    "count_value",
    "label_set",
    "ranking_score",
)
TRAINING_MODES = ("instant", "standard", "high", "ultra")
MODEL_VARIANTS = ("fast", "turbo", "warpspeed")
POLL_WAIT_SECONDS = 85


def infer_output_kind(rows: list[dict[str, str]], target: str) -> str:
    """Best guess from the target column, so a first run needs fewer flags."""
    values = [row.get(target, "") for row in rows]
    distinct = {value for value in values if str(value).strip() != ""}
    if len(distinct) == 2:
        return "binary_label"
    numeric = all(isinstance(common.coerce(value), (int, float)) for value in distinct)
    if numeric and len(distinct) > 10:
        return "numeric_value"
    if len(distinct) >= 3:
        return "multiclass_label"
    common.die(f"cannot infer an output kind for target '{target}' — pass --output-kind")


def build_predict_rows(
    rows: list[dict[str, str]], inputs: list[str], sample: int
) -> list[dict[str, object]]:
    """Use the first N training rows as predict records.

    Predict records must carry exactly the declared input columns — never the
    target, never anything extra.
    """
    if sample <= 0:
        return []
    picked = []
    for row in rows[:sample]:
        record = {column: common.coerce(row.get(column)) for column in inputs}
        if any(value is None for value in record.values()):
            common.die("sampled predict row has empty input values — pass --predict-sample 0")
        picked.append(record)
    return picked


def build_request(args, csv_path, inputs, predict_rows) -> dict:
    request = {
        "name": args.name,
        "file": {
            "content_length": csv_path.stat().st_size,
            "sha256": common.sha256_of(csv_path),
        },
        "spec": {
            "target_column": args.target,
            "input_columns": inputs,
            "output_kind": args.output_kind,
            "training_mode": args.mode,
        },
        "model_variant": args.model_variant,
        # wait=true lets the API hold the connection for up to 85s before
        # handing back a 202; we poll from there either way.
        "wait": True,
        # inline=true returns model bytes in the multipart body; we take the
        # download link instead so large bundles are not held in memory.
        "inline": False,
    }
    if args.output_kind == "event_probability":
        request["spec"]["positive_label"] = common.coerce(args.positive_label)
    if predict_rows:
        request["predict"] = predict_rows
    return request


def submit(api_key: str, request: dict, csv_path: pathlib.Path, key: str, timeout: float):
    import requests

    payload = json.dumps(request).encode()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Idempotency-Key": key,
    }
    # `request` must be the first part and `file` the second, or the API answers 415.
    with csv_path.open("rb") as handle:
        parts = [
            ("request", ("request.json", payload, "application/json")),
            ("file", (csv_path.name, handle, "text/csv")),
        ]
        return requests.post(
            f"{common.TRAINING_ORIGIN}/v1/fit",
            headers=headers,
            files=parts,
            timeout=timeout,
        )


def poll(api_key: str, status_url: str, timeout: float, max_polls: int) -> dict:
    """Follow status_url until the run settles.

    The poll blocks server-side for up to 85s, so a timeout here does not mean
    the run stopped — it means keep reading the same handle.
    """
    import requests

    url = f"{common.TRAINING_ORIGIN}{status_url}"
    separator = "&" if "?" in url else "?"
    headers = {"Authorization": f"Bearer {api_key}"}
    body: dict = {}

    for attempt in range(1, max_polls + 1):
        response = requests.get(
            f"{url}{separator}wait_seconds={POLL_WAIT_SECONDS}",
            headers=headers,
            timeout=timeout,
        )
        if response.status_code != 200:
            common.check_api_error(response, "status read")
        body = response.json()
        state = body.get("state", "unknown")
        common.note(f"  poll {attempt}/{max_polls}: {state}")
        if state in common.TERMINAL_STATES:
            return body

    common.note("  still running — work continues server-side; read the run again later")
    return body


def report(body: dict, run_dir: pathlib.Path, download: bool, timeout: float) -> None:
    state = body.get("state")
    common.note()
    common.note(f"state:  {state}")
    common.note(f"run_id: {body.get('run_id')}")
    common.note(f"artifacts: {run_dir}")

    if body.get("error"):
        common.note(f"error:  {json.dumps(body['error'], ensure_ascii=False)}")

    model = body.get("model") or {}
    if model.get("model_id"):
        common.note(f"model:  {model.get('model_id')} / {model.get('model_version_id')}")
    prediction = model.get("prediction") or {}
    if prediction.get("url"):
        common.note(f"prediction.url: {prediction['url']} ({prediction.get('state')})")

    predictions = body.get("predictions")
    if predictions:
        common.note()
        common.note(f"predictions ({body.get('predictions_state')}):")
        for item in predictions:
            common.note(f"  {json.dumps(item, ensure_ascii=False)}")
    elif body.get("predictions_error"):
        common.note(f"predictions failed: {body['predictions_error']}")

    download_info = model.get("download") or {}
    download_state = body.get("download_state")
    if download_state and download_state != "ready":
        common.note(f"download_state: {download_state} (model file not ready)")
        return
    if not download or not download_info.get("url"):
        return

    fetch_model(download_info, run_dir / "model.tfpb", timeout)


def fetch_model(download_info: dict, destination: pathlib.Path, timeout: float) -> None:
    """Download the model bundle and verify it against the reported fingerprint.

    The signed URL is its own authorization — sending the API bearer here is
    explicitly wrong, so this uses a bare request rather than the session.
    """
    import requests

    common.note(f"downloading {download_info.get('format')} → {destination}")
    response = requests.get(download_info["url"], timeout=timeout)
    if response.status_code != 200:
        common.die(f"download failed ({response.status_code})")
    destination.write_bytes(response.content)

    expected_size = download_info.get("size_bytes")
    expected_sha = download_info.get("sha256")
    actual_size = len(response.content)
    actual_sha = common.sha256_of(destination)

    if expected_size is not None and actual_size != expected_size:
        common.die(f"size mismatch: expected {expected_size}, got {actual_size}")
    if expected_sha and actual_sha != expected_sha:
        common.die(f"sha256 mismatch: expected {expected_sha}, got {actual_sha}")
    common.note(f"verified {actual_size} bytes, sha256 {actual_sha}")


def main() -> None:
    common.load_env()

    parser = argparse.ArgumentParser(
        description="Train a model with the 19th Training API.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("csv", type=pathlib.Path, help="training CSV with a header row")
    parser.add_argument("--target", required=True, help="column to predict")
    parser.add_argument("--mode", required=True, choices=TRAINING_MODES, help="training effort")
    parser.add_argument("--output-kind", choices=OUTPUT_KINDS, help="defaults to a guess")
    parser.add_argument("--positive-label", help="required for event_probability, exact typed label")
    parser.add_argument("--inputs", help="comma-separated input columns (default: all but target)")
    parser.add_argument("--name", help="2-7 word run name")
    parser.add_argument("--model-variant", choices=MODEL_VARIANTS, default="fast")
    parser.add_argument("--predict-sample", type=int, default=0, metavar="N",
                        help="send the first N training rows as predict records")
    parser.add_argument("--key", help="pin the idempotency key to replay a request")
    parser.add_argument("--no-download", action="store_true", help="skip fetching the model file")
    parser.add_argument("--max-polls", type=int, default=12, help="status reads to attempt")
    parser.add_argument("--timeout", type=float, default=150.0, help="per-request timeout in seconds")
    args = parser.parse_args()

    if not args.csv.exists():
        common.die(f"{args.csv} not found")

    header, rows = common.read_table(args.csv)
    if args.target not in header:
        common.die(f"target '{args.target}' is not a column in {args.csv}; columns: {header}")
    if not rows:
        common.die(f"{args.csv} has no data rows")

    if args.inputs:
        inputs = [name.strip() for name in args.inputs.split(",") if name.strip()]
        missing = [name for name in inputs if name not in header]
        if missing:
            common.die(f"unknown input columns: {missing}")
        if args.target in inputs:
            common.die("the target column cannot also be an input column")
    else:
        inputs = [name for name in header if name != args.target]

    if not args.output_kind:
        args.output_kind = infer_output_kind(rows, args.target)
        common.note(f"inferred --output-kind {args.output_kind}")

    if args.output_kind == "event_probability" and args.positive_label is None:
        common.die("--positive-label is required for event_probability")

    if not args.name:
        args.name = f"Predict {args.target.replace('_', ' ')}"[:80]

    api_key = common.require_env(
        "TRAINING_API_KEY", "Copy .env.example to .env and add your key from app.19th.com/api-keys."
    )

    key = args.key or str(uuid.uuid4())
    run_dir = common.RUNS_DIR / key
    run_dir.mkdir(parents=True, exist_ok=True)

    predict_rows = build_predict_rows(rows, inputs, args.predict_sample)
    request = build_request(args, args.csv, inputs, predict_rows)
    (run_dir / "request.json").write_text(json.dumps(request, indent=2))

    common.note(f"training '{args.name}' on {args.csv} ({len(rows)} rows)")
    common.note(f"  target: {args.target}   inputs: {len(inputs)}   mode: {args.mode}")
    common.note(f"  idempotency key: {key}")

    try:
        response = submit(api_key, request, args.csv, key, args.timeout)
    except OSError as error:
        common.die(
            f"request failed: {error}. The run may exist — replay with --key {key} "
            "and the identical CSV rather than starting a new run."
        )

    if response.status_code not in (200, 202):
        common.check_api_error(response, "fit")
    try:
        body = response.json()
    except ValueError:
        common.die(f"fit returned {response.status_code} with a non-JSON body: {response.text[:400]}")

    common.note(f"submit: HTTP {response.status_code} → {body.get('state')}")
    (run_dir / "fit.json").write_text(json.dumps(body, indent=2))

    if response.status_code == 202 or body.get("state") in common.PENDING_STATES:
        body = poll(api_key, body["status_url"], args.timeout, args.max_polls)
        (run_dir / "fit.json").write_text(json.dumps(body, indent=2))

    common.point_latest(run_dir)
    report(body, run_dir, not args.no_download, args.timeout)

    raise SystemExit(0 if body.get("state") == "ready" else 1)


if __name__ == "__main__":
    main()
