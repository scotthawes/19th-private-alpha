#!/usr/bin/env python3
"""Drive the 19th depth arm: emit prediction rows, then score the per-step errors.

Two phases, because the prediction step happens in the downloaded 19th bundle:

    python3 scripts/run_depth_arm.py emit  --anchor 3 --out <rows.json> --index <index.csv>
    # run the bundle: python predict.py --format tfpb <rows.json> > <predictions.json>
    python3 scripts/run_depth_arm.py score --index <index.csv> --predictions <predictions.json>

Frozen-mode features, per the row spec: `latest_cum` and `own_last_ratio` are read from the
origin's cell **at the anchor**, never from a projected level. That makes every cell's
prediction independent of the walk, so one batch of rows covers the whole projection — the
recursion only matters when the error is defined on levels rather than ratios.

Depth is `(d-1) - (k-a)`, as in arm.py:342. Reachable cells are `a <= k` and `a + d > k`.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import statistics

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
PREFIXES = {"origin_idx": "o", "dev_idx": "d", "cal_idx": "cal"}
SIZE = 10


def load_population(path):
    cells = {}
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            cells.setdefault(int(row["triangle_id"]), {})[
                (int(row["origin"]), int(row["development"]))
            ] = float(row["cumulative_paid"])
    return cells


def global_factors(truth, anchor):
    """Volume-weighted age-to-age factors over matched origins, carried forward."""
    factors = [None] * SIZE
    for j in range(SIZE - 1):
        num = den = 0.0
        for origin in range(SIZE):
            a_j = truth.get((origin, j))
            a_j1 = truth.get((origin, j + 1))
            if a_j and a_j1 is not None and origin + j <= anchor and origin + j + 1 <= anchor:
                num += a_j1
                den += a_j
        if den > 0:
            factors[j] = num / den
    last = None
    for j in range(SIZE):
        if factors[j] is not None:
            last = factors[j]
        else:
            factors[j] = last
    return factors


def factor_used(factors, development, anchor):
    j = development - 1
    if j <= anchor and j < len(factors) and factors[j] is not None:
        return float(factors[j]), 1.0
    if factors[anchor] is not None:
        return float(factors[anchor]), 0.0
    return 1.0, 0.0


def emit(population, anchor, out_path, index_path):
    cells = load_population(population)
    rows, index = [], []
    for triangle in sorted(cells):
        truth = cells[triangle]
        factors = global_factors(truth, anchor)

        for origin in range(anchor + 1):
            last_age = min(anchor - origin, SIZE - 1)
            latest = truth.get((origin, last_age))
            before = truth.get((origin, last_age - 1)) if last_age >= 1 else None
            if latest is None:
                continue
            own_last_ratio = latest / before if (before and before > 0) else None

            for development in range(1, SIZE):
                if origin + development <= anchor:
                    continue  # known at the anchor, not a prediction
                if origin + development > SIZE - 1:
                    continue  # outside the triangle: the square's far corner does not exist
                previous = truth.get((origin, development - 1))
                actual = truth.get((origin, development))
                if not previous or actual is None:
                    continue

                base, available = factor_used(factors, development, anchor)
                rows.append(
                    {
                        "origin_idx": f"o{origin}",
                        "dev_idx": f"d{development}",
                        "cal_idx": f"cal{origin + development}",
                        "latest_cum": round(latest, 6),
                        "log_latest_cum": math.log1p(max(latest, 0.0)),
                        "own_last_ratio": own_last_ratio,
                        "global_factor_prev": base,
                        "global_factor_available": available,
                    }
                )
                index.append(
                    {
                        "row": len(rows) - 1,
                        "triangle_id": triangle,
                        "origin": origin,
                        "development": development,
                        "depth": (development - 1) - (anchor - origin),
                        "actual_ratio": actual / previous,
                        "global_factor": base,
                    }
                )

    pathlib.Path(out_path).write_text(json.dumps(rows, indent=2) + "\n")
    with pathlib.Path(index_path).open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(index[0]))
        writer.writeheader()
        writer.writerows(index)
    print(f"emitted {len(rows)} rows -> {out_path}")
    print(f"index -> {index_path}")
    print(f"depths: {min(i['depth'] for i in index)}..{max(i['depth'] for i in index)}")


def score(index_path, predictions_path, json_out=None):
    index = list(csv.DictReader(open(index_path)))
    payload = json.loads(pathlib.Path(predictions_path).read_text())
    predictions = payload["predictions"] if isinstance(payload, dict) else payload
    if len(predictions) != len(index):
        raise SystemExit(f"row mismatch: {len(index)} index rows vs {len(predictions)} predictions")

    errors, depths = [], []
    for entry, prediction in zip(index, predictions):
        # The model returns a delta (ratio normalised by Chain Ladder); recover the ratio.
        delta = prediction.get("prediction", prediction)
        if isinstance(delta, dict):
            delta = delta.get("prediction", delta.get("value"))
        predicted_ratio = float(delta) * float(entry["global_factor"])
        errors.append(math.log(predicted_ratio / float(entry["actual_ratio"])))
        depths.append(int(entry["depth"]))

    n = len(errors)
    mean_x, mean_y = statistics.mean(depths), statistics.mean(errors)
    sxx = sum((x - mean_x) ** 2 for x in depths)
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(depths, errors)) / sxx
    residuals = [y - (mean_y + slope * (x - mean_x)) for x, y in zip(depths, errors)]
    se = math.sqrt(sum(r * r for r in residuals) / (n - 2) / sxx)

    print(f"scored steps: {n}   depth {min(depths)}..{max(depths)}")
    print(f"{'depth':>6} {'steps':>6} {'mean log error':>15} {'x per step':>11}")
    for depth in sorted(set(depths)):
        at = [e for e, d in zip(errors, depths) if d == depth]
        mean = statistics.mean(at)
        print(f"{depth:>6} {len(at):>6} {mean:>15.4f} {math.exp(mean):>11.3f}")

    slope_se = f"{se:.4f}" if se else "n/a"
    print(f"\nslope {slope:+.4f} per step (se {slope_se}, t ≈ {slope / se:.1f})")
    print(f"compounds to x{math.exp(slope * max(depths)):.2f} over {max(depths)} steps")

    # Pre-registered bars from issue #4.
    if se and slope - 1.96 * se <= 0 <= slope + 1.96 * se:
        verdict = "FAILS: slope CI includes zero"
    elif 0.016 <= slope <= 0.064:
        verdict = "REPRODUCES: slope within +0.016..+0.064"
    else:
        verdict = f"OUTSIDE the pre-registered band ({slope:+.4f})"
    print(f"verdict: {verdict}")
    print("note: the band was registered against a CAS-measured slope and needs a matched control (#4).")

    if json_out:
        pathlib.Path(json_out).write_text(
            json.dumps(
                {"scored_steps": n, "slope": slope, "se": se, "verdict": verdict}, indent=2
            )
            + "\n"
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="phase", required=True)

    emit_p = sub.add_parser("emit")
    emit_p.add_argument("--population", type=pathlib.Path,
                        default=pathlib.Path("data/synthetic_population_full.csv"))
    emit_p.add_argument("--anchor", type=int, default=3)
    emit_p.add_argument("--out", required=True)
    emit_p.add_argument("--index", required=True)

    score_p = sub.add_parser("score")
    score_p.add_argument("--index", required=True)
    score_p.add_argument("--predictions", required=True)
    score_p.add_argument("--json-out")

    args = parser.parse_args()
    if args.phase == "emit":
        emit(args.population, args.anchor, args.out, args.index)
    else:
        score(args.index, args.predictions, args.json_out)


if __name__ == "__main__":
    main()
