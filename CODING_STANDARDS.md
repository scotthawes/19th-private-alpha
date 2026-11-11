# Coding Standards

Judgement calls only. Mechanical rules (formatting, banned APIs, import shapes) belong to a
check (linter/formatter/CI), not this file. A rule earns its place here when review raises the
same judgement call repeatedly.

## Verification

There is no test suite, CI workflow, linter or build config in this repo — no
`.github/workflows`, `pyproject.toml`, `Makefile` or `justfile`. Verification is re-running the
generator and checking the digests it writes:

- `python3 scripts/make_triangle.py` — regenerates `data/synthetic_triangle_*.csv`; a re-run
  must be byte-identical and match the SHA-256s in `synthetic_triangle_params.json`.
- `python3 scripts/make_triangle_population.py` — regenerates the 50-triangle population and
  its recorded seeds and digests.
- `python3 scripts/make_pooled_tables.py data/synthetic_population_observed.csv --anchors 3 5 8`
  — rebuilds the pooled tables and `pooled_summary.json`.
- `python3 scripts/split_data.py data/breast_cancer_diagnostic.csv --target diagnosis --force`
  then `python3 scripts/score.py data/holdout.csv predictions.json --target diagnosis
  --positive malignant` — the holdout split and the scoring used to judge a model.

## Evidence and claims

### Date the claim and name the run

Every observation in `docs/alpha-findings.md` is dated and names what was run, because a claim
that cannot be rechecked is not evidence and 19th asks for a `run_id` when anything is
reported. A new finding gets a date, the `run_id` and the artifact it came from.

### State which basis a verdict rests on

Verdicts follow a "reasoned negatives, measured positives" rule: architecture reasoning may
disqualify a row, because absence of extrapolation is a provable fact about the artifact, but
it may not endorse one. An "adds value" verdict needs a measurement behind it; anything else
names the test that would settle it.

### Leave an unmeasured axis unmeasured

Economics has no cost, pricing, licence or compute analysis, so it is recorded as *unmeasured*
and must not be counted as a favourable axis. Do not put a figure on an axis the repo has not
measured.

### Keep the record as sent

`docs/19th-alpha-report.md` stays as the record of what the vendor received; later judgement
goes in a separate document, and a wrong figure is corrected explicitly rather than by quietly
editing the sent report.

## Data

### Generate committed data, never transcribe it

Any CSV committed here is produced by a script that re-runs byte-for-byte, with its seed and
digests stored beside it in a params JSON. `make_triangle.py` and
`make_triangle_population.py` are the pattern: the generator and the data it produces are
committed together so a measured result can always be rebuilt.

### Never train on the full table

`*_full.csv` contains the unobserved corner and exists for scoring only. Training on it turns
the prediction target into an input and invalidates every number derived from it.

### One prediction moment

Every input column must be knowable at the point a prediction will actually be made. A column
filled in after the outcome happened is leakage, and it will make the model look far better
than it is.

### Keep real data out of git history

This repo is private, but data still does not belong in git history. Add real CSVs to
`.gitignore` before the first commit that would contain them.

## 19th API use

### Replay the key; do not retry with a new one

`Idempotency-Key` is how a lost response is recovered, not how a request is retried blindly.
The same key, the same CSV bytes and the same request recover the same run for 7 days;
resubmitting with a fresh key starts a second run. Keep `runs/<key>/request.json`, which holds
the exact bytes and key needed to replay.

### Never send the bearer to a download URL

The signed `model.download.url` is its own authorisation. An `Authorization` header on that URL
is both unnecessary and a leak.

### Reproduce column typing on every prediction row

No request field declares a column categorical — 19th infers it from the serialisation, reading
integers as numeric and the same values written as text as categorical. When identifiers are
meant to be categorical, write them as text at fit time and on every prediction row, or the
model sees a feature type it never trained on.

### Score the exported bundle before choosing a variant

`quality.difference_points` did not track held-out behaviour: Warpspeed scored −0.1077 points
against Fast and then classified every one of 113 holdout rows identically. Export the bundle,
score it on the holdout, and choose on that.

## Scripts

### Stdlib first

`common.py`, `score.py` and the data generators are deliberately dependency-light, and
`score.py` is hand-rolled with no numpy or sklearn so it runs anywhere a bundle does. Add a
dependency only when it is already needed to talk to the API, and say why in the docstring.
