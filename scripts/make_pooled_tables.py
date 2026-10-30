#!/usr/bin/env python3
"""Assemble one pooled CSV per anchor, across the whole synthetic population.

Reuses the row construction that passed the capability probe (`make_probe_table.py`), so the
features and the target are identical to what 19th already accepted:

    origin_idx, dev_idx, cal_idx, latest_cum, log_latest_cum,
    own_last_ratio, global_factor_prev, global_factor_available

Two departures from the single-triangle probe, both decided in issue #10:

* rows are pooled across all 50 triangles at a given anchor;
* the three identifier columns are written as **text** (`"o3"`, `"d1"`, `"cal4"`), because 19th
  infers column types from the data and only infers `categorical` for text values.

Each pooled CSV carries exactly the eight features plus the target — the shape 19th accepted —
so an extra column cannot upset validation. Row provenance goes in a separate index file.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import pathlib

from make_probe_table import FEATURES, IDENTIFIERS, TARGET, build

IDENTIFIER_PREFIXES = {"origin_idx": "o", "dev_idx": "d", "cal_idx": "cal"}


def load_population(path: pathlib.Path) -> dict[int, list[list[float | None]]]:
    """Group the population CSV into one cumulative matrix per triangle."""
    cells: dict[int, dict[tuple[int, int], float]] = {}
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            triangle_id = int(row["triangle_id"])
            cells.setdefault(triangle_id, {})[(int(row["origin"]), int(row["development"]))] = float(
                row["cumulative_paid"]
            )

    matrices = {}
    for triangle_id, entries in cells.items():
        size = max(origin for origin, _ in entries) + 1
        matrix: list[list[float | None]] = [[None] * size for _ in range(size)]
        for (origin, development), value in entries.items():
            matrix[origin][development] = value
        matrices[triangle_id] = matrix
    return matrices


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("population", type=pathlib.Path)
    parser.add_argument("--anchors", type=int, nargs="+", default=[3, 4, 5, 6, 7, 8])
    parser.add_argument("--out-dir", type=pathlib.Path, default=pathlib.Path("data"))
    args = parser.parse_args()

    matrices = load_population(args.population)
    triangle_ids = sorted(matrices)
    summary = {}

    for anchor in args.anchors:
        pooled: list[dict] = []
        index: list[dict] = []

        for triangle_id in triangle_ids:
            matrix = matrices[triangle_id]
            for row in build(matrix, len(matrix), anchor):
                record = dict(row)
                for column, prefix in IDENTIFIER_PREFIXES.items():
                    record[column] = f"{prefix}{record[column]}"
                pooled.append(record)
                index.append(
                    {
                        "row": len(pooled) - 1,
                        "triangle_id": triangle_id,
                        "origin_idx": row["origin_idx"],
                        "dev_idx": row["dev_idx"],
                        "cal_idx": row["cal_idx"],
                        "target_delta": row[TARGET],
                    }
                )

        pooled_path = args.out_dir / f"pooled_anchor{anchor}.csv"
        index_path = args.out_dir / f"pooled_anchor{anchor}_index.csv"

        with pooled_path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FEATURES + [TARGET])
            writer.writeheader()
            writer.writerows(pooled)
        with index_path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(index[0]))
            writer.writeheader()
            writer.writerows(index)

        targets = [row[TARGET] for row in pooled]
        summary[anchor] = {
            "rows": len(pooled),
            "triangles": len(triangle_ids),
            "sha256": hashlib.sha256(pooled_path.read_bytes()).hexdigest(),
            "target_min": min(targets),
            "target_max": max(targets),
            "target_mean": sum(targets) / len(targets),
        }
        print(
            f"k={anchor}: {len(pooled):>5} rows  {len(triangle_ids)} triangles  "
            f"target mean {summary[anchor]['target_mean']:.4f}  "
            f"range [{min(targets):.3f}, {max(targets):.3f}]"
        )

    (args.out_dir / "pooled_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(f"wrote {args.out_dir}/pooled_summary.json")


if __name__ == "__main__":
    main()
