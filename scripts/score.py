#!/usr/bin/env python3
"""Score predictions against held-out labels.

19th returns no absolute accuracy metric, so this is how you actually judge a model:
predict rows the model never saw and compare with the truth.

Hand-rolled (no numpy/sklearn) so it runs anywhere a bundle does.

  python3 scripts/score.py data/holdout.csv predictions.json --target diagnosis --positive malignant
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib

import common


def load_truth(path: pathlib.Path, target: str, positive: str) -> list[int]:
    _, rows = common.read_table(path)
    truth = []
    for row in rows:
        value = str(row[target]).strip()
        truth.append(1 if value == positive else 0)
    return truth


def load_scores(path: pathlib.Path) -> list[float]:
    payload = json.loads(path.read_text())
    predictions = payload.get("predictions", payload)
    scores = []
    for item in predictions:
        if "event_probability" in item:
            scores.append(float(item["event_probability"]))
        elif item.get("probabilities"):
            scores.append(float(item["probabilities"][-1]))
        else:
            common.die(f"cannot find a probability in {json.dumps(item)[:120]}")
    return scores


def roc_auc(truth: list[int], scores: list[float]) -> float:
    """Rank-based AUC with ties handled by average rank (Mann-Whitney U)."""
    pairs = sorted(zip(scores, truth), key=lambda pair: pair[0])
    ranks = [0.0] * len(pairs)
    index = 0
    while index < len(pairs):
        end = index
        while end + 1 < len(pairs) and pairs[end + 1][0] == pairs[index][0]:
            end += 1
        average = (index + end) / 2 + 1
        for position in range(index, end + 1):
            ranks[position] = average
        index = end + 1

    positives = sum(truth)
    negatives = len(truth) - positives
    if positives == 0 or negatives == 0:
        return float("nan")
    rank_sum = sum(rank for rank, (_, label) in zip(ranks, pairs) if label == 1)
    return (rank_sum - positives * (positives + 1) / 2) / (positives * negatives)


def calibration(truth: list[int], scores: list[float], bins: int = 10):
    buckets = [[] for _ in range(bins)]
    for label, score in zip(truth, scores):
        position = min(int(score * bins), bins - 1)
        buckets[position].append((label, score))
    table = []
    for position, members in enumerate(buckets):
        if not members:
            continue
        mean_score = sum(score for _, score in members) / len(members)
        observed = sum(label for label, _ in members) / len(members)
        table.append((position / bins, (position + 1) / bins, len(members), mean_score, observed))
    return table


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("holdout", type=pathlib.Path, help="held-out CSV with true labels")
    parser.add_argument("predictions", type=pathlib.Path, help="bundle predict.py JSON output")
    parser.add_argument("--target", required=True)
    parser.add_argument("--positive", required=True, help="label counted as the positive class")
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--json-out", type=pathlib.Path)
    args = parser.parse_args()

    truth = load_truth(args.holdout, args.target, args.positive)
    scores = load_scores(args.predictions)

    if len(truth) != len(scores):
        common.die(f"row mismatch: {len(truth)} labels vs {len(scores)} predictions")

    tp = sum(1 for label, score in zip(truth, scores) if label == 1 and score >= args.threshold)
    fp = sum(1 for label, score in zip(truth, scores) if label == 0 and score >= args.threshold)
    tn = sum(1 for label, score in zip(truth, scores) if label == 0 and score < args.threshold)
    fn = sum(1 for label, score in zip(truth, scores) if label == 1 and score < args.threshold)

    total = len(truth)
    accuracy = (tp + tn) / total
    precision = tp / (tp + fp) if tp + fp else float("nan")
    recall = tp / (tp + fn) if tp + fn else float("nan")
    f1 = (2 * precision * recall / (precision + recall)) if precision + recall else float("nan")
    auc = roc_auc(truth, scores)
    brier = sum((score - label) ** 2 for label, score in zip(truth, scores)) / total
    epsilon = 1e-12
    log_loss = -sum(
        label * math.log(max(min(score, 1 - epsilon), epsilon))
        + (1 - label) * math.log(max(min(1 - score, 1 - epsilon), epsilon))
        for label, score in zip(truth, scores)
    ) / total

    common.note(f"rows: {total}  ({sum(truth)} {args.positive}, {total - sum(truth)} other)")
    common.note(f"threshold: {args.threshold}")
    common.note()
    common.note(f"  accuracy   {accuracy:.4f}")
    common.note(f"  roc auc    {auc:.4f}")
    common.note(f"  precision  {precision:.4f}")
    common.note(f"  recall     {recall:.4f}")
    common.note(f"  f1         {f1:.4f}")
    common.note(f"  log loss   {log_loss:.4f}")
    common.note(f"  brier      {brier:.4f}")
    common.note()
    common.note(f"  confusion  tp={tp}  fp={fp}  tn={tn}  fn={fn}")
    common.note()
    common.note("  calibration (predicted vs observed):")
    common.note("    bin            n      predicted   observed")
    for low, high, count, mean_score, observed in calibration(truth, scores):
        common.note(
            f"    {low:.1f}-{high:.1f}   {count:>4}      {mean_score:.3f}       {observed:.3f}"
        )

    if args.json_out:
        args.json_out.write_text(
            json.dumps(
                {
                    "rows": total,
                    "positives": sum(truth),
                    "threshold": args.threshold,
                    "accuracy": accuracy,
                    "roc_auc": auc,
                    "precision": precision,
                    "recall": recall,
                    "f1": f1,
                    "log_loss": log_loss,
                    "brier": brier,
                    "confusion": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
                },
                indent=2,
            )
            + "\n"
        )
        common.note(f"\nwrote {args.json_out}")


if __name__ == "__main__":
    main()
