#!/usr/bin/env python3
"""Build a demo dataset so the API can be exercised before you bring real data.

The alpha ships four demo CSVs as attachments on the Notion page, which only the
invited account can download. This reconstructs the tumor-diagnosis one from
scikit-learn's copy of the UCI Breast Cancer Wisconsin (Diagnostic) data, so
`fit.py` has something real to train on immediately.

It is *not* byte-identical to 19th's file. If you want exact parity with the
alpha's demo, download `breast_cancer_diagnostic.csv` from the Notion page into
`data/` — that file wins.
"""

from __future__ import annotations

import argparse
import csv
import json
import pathlib

import common

DEFAULT_OUT = common.DATA_DIR / "breast_cancer_diagnostic.csv"
DEFAULT_SAMPLE_OUT = common.DATA_DIR / "predict-sample.json"
TARGET_COLUMN = "diagnosis"
LABELS = {0: "malignant", 1: "benign"}
SAMPLE_ROWS = 3


def canonical_name(name: str) -> str:
    """Map sklearn's 'mean radius' to the canonical WDBC 'radius_mean'.

    The alpha's own file is not published, but every public copy of this dataset
    uses the radius_mean / radius_se / radius_worst convention, so matching it
    keeps column names familiar and JSON-friendly.
    """
    name = name.strip().lower()
    if name.startswith("mean "):
        return f"{name[5:].replace(' ', '_')}_mean"
    if name.startswith("worst "):
        return f"{name[6:].replace(' ', '_')}_worst"
    if name.endswith(" error"):
        return f"{name[:-6].replace(' ', '_')}_se"
    return name.replace(" ", "_")



def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--sample-out",
        type=pathlib.Path,
        default=DEFAULT_SAMPLE_OUT,
        help="where to write a ready-to-send prediction records file",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite an existing file (default: leave it alone)",
    )
    args = parser.parse_args()

    if args.out.exists() and not args.force:
        common.note(f"{args.out} already exists — leaving it alone. Use --force to rebuild.")
        return

    try:
        from sklearn.datasets import load_breast_cancer
    except ImportError:
        common.die("scikit-learn is required: python3 -m pip install scikit-learn")

    bunch = load_breast_cancer(as_frame=True)
    # sklearn's frame carries its own integer `target` column; the target is
    # re-added below as text labels, which is what the demo predicts.
    frame = bunch.frame.drop(columns=["target"])
    frame.columns = [canonical_name(name) for name in frame.columns]
    frame[TARGET_COLUMN] = [LABELS[value] for value in bunch.target]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    # QUOTE_MINIMAL keeps the file small; the API only needs a header row and
    # one flat table.
    frame.to_csv(args.out, index=False, quoting=csv.QUOTE_MINIMAL)

    rows = len(frame)
    inputs = [name for name in frame.columns if name != TARGET_COLUMN]
    common.note(f"wrote {args.out} ({rows} rows, {len(inputs)} input columns)")

    # A records file with every declared input column, so predict.py works
    # without hand-writing 30 keys. These rows are taken from the training set:
    # they prove the call works, not that the model is any good.
    sample = []
    for _, row in frame.tail(SAMPLE_ROWS).iterrows():
        sample.append({column: common.coerce(row[column]) for column in inputs})
    sample_path = args.sample_out
    sample_path.write_text(json.dumps(sample, indent=2) + "\n")
    common.note(f"wrote {sample_path} ({len(sample)} smoke-test records)")

    common.note(f"target: {TARGET_COLUMN} = {sorted(set(frame[TARGET_COLUMN]))}")
    common.note("provenance: sklearn.datasets.load_breast_cancer (UCI WDBC)")
    common.note()
    common.note("try:")
    common.note(
        f"  python3 scripts/fit.py {args.out} --target {TARGET_COLUMN} \\\n"
        "    --output-kind event_probability --positive-label malignant \\\n"
        "    --mode standard --predict-sample 3 --download"
    )
    common.note(f"  python3 scripts/predict.py --input-file {sample_path}")


if __name__ == "__main__":
    main()
