#!/usr/bin/env python3
"""Call a trained model's hosted prediction URL (19th Inference API).

Reads `runs/<id>/fit.json` for the model's `prediction.url` and the model ids, so
a fresh fit needs no copy-pasting. Falls back to `TRAINING_API_KEY` because a
training key with `inference:invoke` can call model-version routes; set
`INFERENCE_API_KEY` when the endpoint needs its own key.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import uuid

import common


def resolve_url(args) -> tuple[str, dict]:
    if args.url:
        return args.url, {}

    run_dir = args.run_dir
    fit_path = run_dir / "fit.json"
    if not fit_path.exists():
        common.die(f"{fit_path} not found — run scripts/fit.py first, or pass --url")

    fit = json.loads(fit_path.read_text())
    model = fit.get("model") or {}
    prediction = model.get("prediction") or {}
    url = prediction.get("url")
    if not url:
        common.die(
            f"{fit_path} has no model.prediction.url (prediction state: "
            f"{prediction.get('state')!r}). Download readiness and prediction readiness "
            "are independent — ensure hosted prediction is enabled for this model."
        )
    return url, model


def load_records(args) -> list:
    if args.input_json:
        text = args.input_json
        candidate = pathlib.Path(text)
        if candidate.exists():
            text = candidate.read_text()
        try:
            payload = json.loads(text)
        except ValueError as error:
            common.die(f"--input-json is not valid JSON: {error}")
    else:
        payload = json.loads(pathlib.Path(args.input_file).read_text())

    records = payload.get("input") if isinstance(payload, dict) and "input" in payload else payload
    if isinstance(records, dict):
        records = [records]
    if not isinstance(records, list) or not records:
        common.die("expected an object or a non-empty array of input records")
    return records


def main() -> None:
    common.load_env()

    parser = argparse.ArgumentParser(
        description="Get predictions from a trained 19th model.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--run-dir", type=pathlib.Path, default=common.RUNS_DIR / "latest",
                        help="run directory containing fit.json")
    parser.add_argument("--url", help="prediction URL, overriding fit.json")
    parser.add_argument("--input-json", help="inline JSON, or a path to a JSON file")
    parser.add_argument("--input-file", help="path to a JSON file of input records")
    parser.add_argument("--request-id", help="optional X-Request-Id / request_id to trace")
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args()

    if not args.input_json and not args.input_file:
        common.die("pass --input-json or --input-file")

    url, model = resolve_url(args)
    records = load_records(args)
    request_id = args.request_id or f"predict-{uuid.uuid4()}"

    # Resolved after the run artifacts so a missing fit.json is reported as
    # such, rather than as a missing key.
    api_key = os.environ.get("INFERENCE_API_KEY", "").strip() or common.require_env(
        "TRAINING_API_KEY"
    )

    body: dict = {"input": records}
    if model.get("model_id"):
        # Optional, but must match the route when supplied.
        body["model"] = model["model_id"]

    import requests

    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Request-Id": request_id,
        },
        json=body,
        timeout=args.timeout,
    )

    if response.status_code != 200:
        common.check_api_error(response, "prediction")

    result = response.json()
    common.note(json.dumps(result, indent=2, ensure_ascii=False))

    output = result.get("output") or []
    common.note()
    for record, answer in zip(records, output):
        common.note(f"{json.dumps(record)} → {json.dumps(answer)}")
    common.note(f"request_id: {result.get('request_id', request_id)}")


if __name__ == "__main__":
    main()
