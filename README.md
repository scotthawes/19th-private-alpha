# 19th — private alpha sandbox

Working repo for the **19th private alpha**. 19th trains a model on a CSV you supply, then
serves predictions from it and hands you a downloadable model file (`.tfpb`) you can run
yourself.

Two entry points, and this repo is set up for both:

| Path | Auth | Start at |
| --- | --- | --- |
| **MCP** | OAuth in your client — no API key | [`docs/vendor/19th/mcp.md`](docs/vendor/19th/mcp.md) |
| **Training API** | `TRAINING_API_KEY` | `scripts/fit.py` below |

## Quickstart — MCP (no key)

```sh
# Codex
codex mcp add 19th --url https://app.19th.com/mcp

# Claude Code
claude mcp add --transport http --scope user 19th https://app.19th.com/mcp

# Cursor: ~/.cursor/mcp.json
# { "mcpServers": { "19th": { "url": "https://app.19th.com/mcp" } } }
```

Sign in when the client prompts (use the **invited email address**), then confirm access
before uploading anything:

1. `get_skill` with no arguments — reads the current workflow guide.
2. `get_capabilities` — verifies access and lists the tasks, formats and training modes
   actually enabled for your account.

## Quickstart — Training API

```sh
cp .env.example .env          # then paste your Training key into it
python3 scripts/make_demo_data.py

python3 scripts/fit.py data/breast_cancer_diagnostic.csv \
  --target diagnosis \
  --output-kind event_probability \
  --positive-label malignant \
  --mode standard \
  --predict-sample 3 \
  --download

python3 scripts/predict.py --input-file data/predict-sample.json
```

`fit.py` writes every artifact needed to replay the request to `runs/<idempotency-key>/`
and points `runs/latest` at the newest run.

## Layout

```
19th-private-alpha/
├── docs/
│   ├── alpha-notes.md        # the invite, kept as the source of truth
│   ├── test-plan.md          # what to exercise, both paths
│   └── vendor/19th/          # official 19th docs, vendored verbatim
├── scripts/
│   ├── fit.py                # submit + poll + optional model download
│   ├── predict.py            # hosted JSON predictions
│   ├── make_demo_data.py     # builds a runnable demo dataset
│   └── common.py             # shared helpers
├── data/                     # CSVs in, see data/README.md
└── runs/                     # per-run artifacts (gitignored)
```

## Scripts

| Script | Does |
| --- | --- |
| `make_demo_data.py` | Writes `data/breast_cancer_diagnostic.csv` (reconstruction — see `data/README.md`) and prints the provenance. |
| `fit.py` | `POST /v1/fit`, polls `status_url` on 202, verifies and saves the model on request. |
| `predict.py` | Calls the model's `prediction.url` from `fit.json`. |

Useful `fit.py` flags: `--mode instant|standard|high|ultra`, `--output-kind` (any of the eight
in `docs/vendor/19th/training.md`), `--predict-sample N`, `--key` to pin an idempotency key,
`--download`, `--max-polls`.

## What the docs will bite you on

Read straight off the API contract — these are the ones that cost you a run:

- **A `202` is not a failure.** Training continues in the background. Poll the returned
  `status_url`; do not resubmit with a fresh key, or you start a second run.
- **`Idempotency-Key` is how you recover, not how you retry blindly.** The same key, the same
  CSV bytes and the same request recover the *same* run for 7 days. Only `wait` and `inline`
  may change. If a response is lost, replay exactly — that is recovery, not a new job.
- **`training_mode` has no default.** `instant`, `standard`, `high`, `ultra` must be chosen
  explicitly. `model_variant` (`fast`/`turbo`/`warpspeed`) is separate and only picks the
  model file used for downloads and predictions.
- **The bearer goes to the API and nowhere else.** Never send `Authorization` to a
  `model.download.url` — the signed link is the auth.
- **`ready` does not mean "everything worked".** `download_state` and `predictions_state`
  settle independently; a ready model can still have an unavailable download or failed
  optional predictions. Check each field.
- **CSV training does not model raw free text.** Text has to be turned into numeric features
  by you, and you must produce the same features at prediction time. This matters for the
  support-ticket demo.
- **`predict` records need exactly the declared `input_columns`** — no target, no extra
  columns. Up to 1,000 records, and it needs a key with `inference:invoke`.
- **A saved failure can arrive as `200 OK`.** Inspect `state` and `error` before trusting a
  response.
- **The CSV part is second.** `request` JSON first, `file` second, and let curl/requests set
  the multipart boundary or you get a `415`.

## Demo datasets

The alpha ships four. Only one is generated here; the rest are Notion attachments, so
download them from the invite page into `data/`:

| Dataset | Predict | Target column |
| --- | --- | --- |
| `breast_cancer_diagnostic.csv` | Malignant vs benign | `diagnosis` |
| `kepler_koi.csv` | Planet vs false positive | see file |
| `support_intents.csv` | 77 banking support categories | see file |
| `machine_failure_binary.csv` | Machine will fail | see file |

## Vendored docs

`docs/vendor/19th/*.md` are the official pages copied verbatim on 2026-10-29 from
`https://19th.com/docs/{mcp,training,inference}.md`. They are the contract this repo codes
against; re-copy if 19th updates them. `mcp.md` includes the full tool schemas.
