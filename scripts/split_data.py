#!/usr/bin/env python3
"""Deterministic stratified split into a training set and a holdout set.

The split is a pure function of (file contents, seed, holdout fraction), so it can be
rebuilt exactly and nothing derived needs committing.

Writes three files:
  train.csv         labelled rows to train on
  holdout.csv       labelled rows never shown to training
  holdout-rows.json input-only records, in holdout order, ready for a bundle's predict.py
"""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
import random

import common


def stratified_split(rows: list[dict], target: str, holdout_frac: float, seed: int):
    by_class: dict[str, list[dict]] = {}
    for row in rows:
        by_class.setdefault(row[target], []).append(row)

    rng = random.Random(seed)
    train, holdout = [], []
    for label in sorted(by_class):
        members = by_class[label][:]
        rng.shuffle(members)
        cut = max(1, round(len(members) * holdout_frac))
        holdout.extend(members[:cut])
        train.extend(members[cut:])

    # Keep each output in a stable order so runs are comparable.
    rng.shuffle(train)
    rng.shuffle(holdout)
    return train, holdout


def write_csv(path: pathlib.Path, rows: list[dict], columns: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=pathlib.Path, help="fully labelled source CSV")
    parser.add_argument("--target", required=True)
    parser.add_argument("--holdout-frac", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out-dir", type=pathlib.Path, default=common.DATA_DIR)
    parser.add_argument("--force", action="store_true", help="overwrite existing splits")
    args = parser.parse_args()

    if not 0 < args.holdout_frac < 1:
        common.die("--holdout-frac must be between 0 and 1")

    header, rows = common.read_table(args.csv)
    if args.target not in header:
        common.die(f"target '{args.target}' is not a column in {args.csv}")

    labelled = [row for row in rows if str(row.get(args.target, "")).strip() != ""]
    if len(labelled) != len(rows):
        common.note(f"note: dropped {len(rows) - len(labelled)} rows with an empty target")

    train, holdout = stratified_split(labelled, args.target, args.holdout_frac, args.seed)
    if not train or not holdout:
        common.die("split produced an empty side — check the label counts")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    train_path = args.out_dir / "train.csv"
    holdout_path = args.out_dir / "holdout.csv"
    rows_path = args.out_dir / "holdout-rows.json"

    for path in (train_path, holdout_path, rows_path):
        if path.exists() and not args.force:
            common.die(f"{path} exists — pass --force to rebuild the split")

    write_csv(train_path, train, header)
    write_csv(holdout_path, holdout, header)

    inputs = [column for column in header if column != args.target]
    records = [{column: common.coerce(row[column]) for column in inputs} for row in holdout]
    rows_path.write_text(json.dumps(records, indent=2) + "\n")

    def balance(subset):
        counts: dict[str, int] = {}
        for row in subset:
            counts[row[args.target]] = counts.get(row[args.target], 0) + 1
        return ", ".join(f"{label}={n}" for label, n in sorted(counts.items()))

    common.note(f"seed={args.seed} holdout_frac={args.holdout_frac}")
    common.note(f"train:   {train_path} ({len(train)} rows — {balance(train)})")
    common.note(f"holdout: {holdout_path} ({len(holdout)} rows — {balance(holdout)})")
    common.note(f"records: {rows_path} ({len(records)} input-only rows)")


if __name__ == "__main__":
    main()
