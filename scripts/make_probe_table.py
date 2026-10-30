#!/usr/bin/env python3
"""Build the flat link-ratio table that 19th is fitted on.

Reproduces the row construction documented in `docs/research/delta-arm-rows.md`, which was
reverse-engineered from `tabpfn-reserving/src/tabpfn_reserving/triangle.py` and `arm.py`.
The eight feature columns and their order match `triangle.FEATURES` exactly, and the three
identifier columns are the first three, matching `IDENTIFIER_INDICES = [0, 1, 2]`.

Target: a one-period link ratio divided by Chain Ladder's own volume-weighted factor for
that step, so **1.0 reproduces Chain Ladder exactly**.

Why it exists: 19th has to be fitted on the same rows TabPFN was fitted on, or the two
cannot be compared. This produces those rows from the synthetic triangle.
"""

from __future__ import annotations

import argparse
import csv
import math
import pathlib

FEATURES = [
    "origin_idx",
    "dev_idx",
    "cal_idx",
    "latest_cum",
    "log_latest_cum",
    "own_last_ratio",
    "global_factor_prev",
    "global_factor_available",
]
IDENTIFIERS = ["origin_idx", "dev_idx", "cal_idx"]
TARGET = "target_delta"


def load(path: pathlib.Path) -> tuple[list[list[float | None]], int]:
    cells: dict[tuple[int, int], float] = {}
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            cells[(int(row["origin"]), int(row["development"]))] = float(row["cumulative_paid"])
    n = max(origin for origin, _ in cells) + 1
    matrix: list[list[float | None]] = [[None] * n for _ in range(n)]
    for (origin, development), value in cells.items():
        matrix[origin][development] = value
    return matrix, n


def known(matrix, n: int, anchor: int) -> list[list[bool]]:
    """Cells known at the anchor — triangle.Triangle.known."""
    return [
        [origin <= anchor and origin + development <= anchor and matrix[origin][development] is not None
         for development in range(n)]
        for origin in range(n)
    ]


def global_factors(matrix, n: int, is_known) -> list[float | None]:
    """Volume-weighted age-to-age factors over matched origins, carried forward — Triangle.global_factors."""
    factors: list[float | None] = [None] * n
    for j in range(n - 1):
        numerator = denominator = 0.0
        for origin in range(n):
            if is_known[origin][j] and is_known[origin][j + 1] and matrix[origin][j] > 0:
                numerator += matrix[origin][j + 1]
                denominator += matrix[origin][j]
        if denominator > 0:
            factors[j] = numerator / denominator
    last = None
    for j in range(n):
        if factors[j] is not None:
            last = factors[j]
        else:
            factors[j] = last
    return factors


def factor_used(factors, development: int, anchor: int) -> tuple[float, float]:
    """The factor this cell is entitled to see, and whether it existed at the anchor — gf_used."""
    j = development - 1
    if j <= anchor and j < len(factors) and factors[j] is not None:
        return float(factors[j]), 1.0
    if anchor < len(factors) and factors[anchor] is not None:
        return float(factors[anchor]), 0.0
    return 1.0, 0.0


def build(matrix, n: int, anchor: int) -> list[dict]:
    is_known = known(matrix, n, anchor)
    factors = global_factors(matrix, n, is_known)

    rows: list[dict] = []
    for origin in range(n):
        for development in range(1, n):
            if not (is_known[origin][development] and is_known[origin][development - 1]):
                continue
            previous, current = matrix[origin][development - 1], matrix[origin][development]
            if previous is None or current is None or previous <= 0:
                continue

            ratio = current / previous
            base, available = factor_used(factors, development, anchor)
            if base <= 0:
                continue
            target = ratio / base

            # Frozen-mode features: the origin's level at the anchor, never the projected one.
            last_age = min(anchor - origin, n - 1)
            latest = matrix[origin][last_age] if last_age >= 0 else None
            before = matrix[origin][last_age - 1] if last_age >= 1 else None
            own_last_ratio = (
                latest / before if (latest is not None and before not in (None, 0) and before > 0) else None
            )

            rows.append(
                {
                    "origin_idx": origin,
                    "dev_idx": development,
                    "cal_idx": origin + development,
                    "latest_cum": latest,
                    "log_latest_cum": math.log1p(max(latest, 0.0)) if latest is not None else None,
                    "own_last_ratio": own_last_ratio,
                    "global_factor_prev": base,
                    "global_factor_available": available,
                    TARGET: target,
                }
            )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("triangle", type=pathlib.Path, help="observed triangle CSV")
    parser.add_argument("--anchor", type=int, required=True, help="valuation diagonal index k")
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()

    matrix, n = load(args.triangle)
    if not 0 <= args.anchor < n:
        raise SystemExit(f"anchor must be in 0..{n - 1}")

    rows = build(matrix, n, args.anchor)
    if not rows:
        raise SystemExit("no rows built — check the anchor")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FEATURES + [TARGET])
        writer.writeheader()
        writer.writerows(rows)

    targets = [row[TARGET] for row in rows]
    identifier_values = {
        name: sorted({row[name] for row in rows}) for name in IDENTIFIERS
    }
    print(f"anchor k={args.anchor}  rows={len(rows)}  -> {args.out}")
    print(f"target_delta: min={min(targets):.4f} max={max(targets):.4f} mean={sum(targets)/len(targets):.4f}")
    for name, values in identifier_values.items():
        print(f"  {name}: {len(values)} distinct — {values}")


if __name__ == "__main__":
    main()
