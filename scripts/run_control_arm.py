#!/usr/bin/env python3
"""Matched TabPFN control for the 19th depth arm (#14).

Same cells, same seven columns, same transform. The point is to have one number to compare
the 19th slope against that shares corpus and encoding, so a difference can be attributed to
the model rather than to either.

Seven columns, not eight: `global_factor_available` is dropped to match what 19th receives
after it excludes the constant column (#10 decision).

Run with the repository venv, which carries the recorded tabpfn 9.0.0:

    /Users/Scott/projects/tabpfn-reserving/.venv/bin/python \
        scripts/run_control_arm.py --anchor 3
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import run_depth_arm as arm
from make_probe_table import build

FEATURES_7 = [
    "origin_idx",
    "dev_idx",
    "cal_idx",
    "latest_cum",
    "log_latest_cum",
    "own_last_ratio",
    "global_factor_prev",
]
CATEGORICAL_INDICES = [0, 1, 2]


def to_matrix(entries, size=arm.SIZE):
    """arm.load_population gives {(origin, development): value}; build() wants a matrix."""
    matrix = [[None] * size for _ in range(size)]
    for (origin, development), value in entries.items():
        if origin < size and development < size:
            matrix[origin][development] = value
    return matrix


def training_arrays(cells, anchor):
    X, y = [], []
    for triangle in sorted(cells):
        for row in build(to_matrix(cells[triangle]), arm.SIZE, anchor):
            X.append([float(row[name]) for name in FEATURES_7])
            y.append(float(row["target_delta"]))
    return X, y


def prediction_arrays(cells, anchor):
    """The same reachable cells the 19th arm was scored on."""
    X, index = [], []
    for triangle in sorted(cells):
        truth = cells[triangle]
        factors = arm.global_factors(truth, anchor)
        for origin in range(anchor + 1):
            last_age = min(anchor - origin, arm.SIZE - 1)
            latest = truth.get((origin, last_age))
            before = truth.get((origin, last_age - 1)) if last_age >= 1 else None
            if latest is None:
                continue
            own_last_ratio = latest / before if (before and before > 0) else 0.0

            for development in range(1, arm.SIZE):
                if origin + development <= anchor:
                    continue
                if origin + development > arm.SIZE - 1:
                    continue
                previous = truth.get((origin, development - 1))
                actual = truth.get((origin, development))
                if not previous or actual is None:
                    continue
                base, _available = arm.factor_used(factors, development, anchor)
                X.append(
                    [
                        float(origin),
                        float(development),
                        float(origin + development),
                        float(latest),
                        math.log1p(max(latest, 0.0)),
                        float(own_last_ratio),
                        float(base),
                    ]
                )
                index.append(
                    {
                        "triangle_id": triangle,
                        "depth": (development - 1) - (anchor - origin),
                        "actual_ratio": actual / previous,
                        "global_factor": base,
                    }
                )
    return X, index


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--population", type=pathlib.Path,
                        default=pathlib.Path("data/synthetic_population_full.csv"))
    parser.add_argument("--anchor", type=int, default=3)
    parser.add_argument("--json-out", type=pathlib.Path)
    args = parser.parse_args()

    from tabpfn import TabPFNRegressor

    cells = arm.load_population(args.population)
    X_train, y_train = training_arrays(cells, args.anchor)
    X_pred, index = prediction_arrays(cells, args.anchor)

    print(f"control: {len(X_train)} training rows, {len(X_pred)} prediction rows, "
          f"{len(FEATURES_7)} columns, categorical {CATEGORICAL_INDICES}")

    model = TabPFNRegressor(device="cpu", categorical_features_indices=CATEGORICAL_INDICES)
    model.fit(X_train, y_train)
    deltas = model.predict(X_pred)

    errors, depths = [], []
    for entry, delta in zip(index, deltas):
        predicted_ratio = float(delta) * float(entry["global_factor"])
        errors.append(math.log(predicted_ratio / float(entry["actual_ratio"])))
        depths.append(int(entry["depth"]))

    n = len(errors)
    mean_x, mean_y = statistics.mean(depths), statistics.mean(errors)
    sxx = sum((x - mean_x) ** 2 for x in depths)
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(depths, errors)) / sxx
    residuals = [y - (mean_y + slope * (x - mean_x)) for x, y in zip(depths, errors)]
    se = math.sqrt(sum(r * r for r in residuals) / (n - 2) / sxx)

    print(f"\n{'depth':>6} {'steps':>6} {'mean log error':>15} {'x per step':>11}")
    for depth in sorted(set(depths)):
        at = [e for e, d in zip(errors, depths) if d == depth]
        mean = statistics.mean(at)
        print(f"{depth:>6} {len(at):>6} {mean:>15.4f} {math.exp(mean):>11.3f}")

    intercept = mean_y - slope * mean_x
    print(f"\nscored steps {n}   depth {min(depths)}..{max(depths)}")
    print(f"slope {slope:+.4f} per step (se {se:.4f}, t ≈ {slope / se:.1f})")
    print(f"depth-0 intercept {intercept:+.4f} (×{math.exp(intercept):.3f})")

    if args.json_out:
        args.json_out.write_text(
            json.dumps(
                {
                    "arm": "tabpfn-control",
                    "scored_steps": n,
                    "slope": slope,
                    "se": se,
                    "depth0_intercept": intercept,
                    "columns": FEATURES_7,
                },
                indent=2,
            )
            + "\n"
        )


if __name__ == "__main__":
    main()
