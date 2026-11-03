# Fit record: the evidence we require, and the test that confirms it

**Ticket:** [#22](https://github.com/scotthawes/19th-private-alpha/issues/22) · **Date:** 2026-11-03 · **Status:** test run complete — **FAIL** on shipped evidence

## The answer, before the detail

The checklist is written and the test is run. The result is a **fail**, and it fails at the
first step: there is nothing to re-fit *from*. No tool on this connection returns a fit record,
no field in any working endpoint describes how the parameters were estimated, and the bundle as
recorded in the alpha contains no trainer, no writer, no hyperparameters and no seeds.

So the bundle stays what [`model-governance.md`](model-governance.md) calls an unusually
well-evidenced **implementation** and an unusually poorly-evidenced **development**.

---

## 1. The checklist — what a fit record must contain

Seven things, sufficient for a second person to reproduce the fit. Each row names where the
requirement comes from and what "present" would mean in practice.

| # | Must contain | Source | What "present" means |
| --- | --- | --- | --- |
| 1 | Training pipeline, pinned to a version | SS1/23 P3.5(a); SII Art 125 | executable code plus a version, enough to re-run the fit |
| 2 | Architecture search — space, method, winner | TAS 100 P6.1(a); TAG Models §9.49 | what was tried, and why this architecture won |
| 3 | Loss function and any weighting | SS1/23 P3.5(a) | the stated objective |
| 4 | Hyperparameters — the values used | TAS 100 P6.1(a); TAG Models §9.49 | actual values, not merely the search space |
| 5 | Seeds | TAG Models §9.49 | "to allow a reviewer to reproduce the random processes" |
| 6 | Preprocessing and type inference | SS1/23 P3.2; SII Art 121(3) | transforms, schema, and how types were inferred |
| 7 | Exclusions | SS1/23 P3.2 | rows and columns dropped, and why — the alpha saw a constant column dropped silently |

Two of those sources carry different weight. SS1/23 P3.5(a) is the **banking** benchmark — an
independent expert must be able to "replicate any parameter estimation and model results" — and
SS1/23 expressly does not bind insurers. For a GI insurer the binding analogue is **SII Art 125**
("mathematical and empirical bases") read with **Art 126**, which removes the "it is the vendor's
model" exemption.

**The counterweight, stated once so it is not lost:** FRC TAG Models §9.60 says reproducibility in
the sense of "sufficient supporting information … to enable an identical model, producing
identical outputs, to be trained" is **not required by TAS 100**, and a practitioner may judge it
is not required by other applicable regulation either. Under the professional standard,
retrainability is a *condition* — acceptable provided the practitioner understands the model
(P5.1), tests its stability, and sets retraining or replacement triggers (§9.61). Under SS1/23
P3.5(a) and Art 125 it is closer to a bar.

This checklist is therefore **our acceptance evidence for a material primary use**, not an
assertion that TAS 100 has been breached. For a challenger model it is deliberately over-specified.

---

## 2. The test

1. Take a bundle.
2. Attempt a re-fit from the record alone — without asking 19th a question.
3. Compare the reproduced parameters and model results against the shipped ones.

**Pass** = a second person reproduces the reported parameters and model results without asking
19th a question. **Fail** = any of the seven cannot be answered from what ships.

---

## 3. What ships — the evidence

### 3.1 Live, verified 2026-11-03

- **The tool surface has 18 tools.** None returns a fit record:
  `cancel_run`, `create_project`, `get_api_setup`, `get_capabilities`, `get_download`,
  `get_download_options`, `get_model`, `get_project`, `get_results`, `get_runtimes`, `get_skill`,
  `list_projects`, `list_runs`, `list_skills`, `prep_run`, `request_download`, `set_run_project`,
  `submit_run`.
- **`prep_run(action: "template")`** returns `formats` and `templates` — zero fields matching
  hyperparameter, seed, architecture, loss, optimisation, epoch, learning-rate, batch,
  preprocessing or exclusion terms.
- **`get_runtimes`, `get_download_options`, `list_skills`** all respond normally and contain zero
  fit-record fields. `list_skills` offers `training`, `define-prediction` and `training-data` — no
  guide describing a fit record.
- **`get_results` was unavailable for this whole session.** See §3.3.

### 3.2 Bundle contents — recorded from a real download (2026-10-29)

From [`docs/alpha-findings.md`](../docs/alpha-findings.md): the Fast bundle was 1,452,402 bytes,
SHA-256 `5c4a9566…4d5fcbc`, containing `predict.py`, `requirements.txt`, `model-interface.json`
(schema `oracle_inference.v4`), `models/model.npz` + `models/model.tfpb`, the signed manifest
(`oracle-bundle-manifest.v1.json` / `.sig`) and signing certificate, plus a vendored numpy
runtime.

Absent from that inventory, and stated in the same document: no trainer, no writer (the `.tfpb`
writer is not shipped), no hyperparameters, no seeds.

**Caveat:** this line is the alpha's record, not a re-verification today. The outage in §3.3
prevented re-downloading a bundle to re-inventory it on 2026-11-03. The verdict below does not
depend on it — §3.1 alone is decisive — but this row should be re-checked once the endpoint
recovers.

### 3.3 The results endpoint was unavailable

Every `get_results` call on 2026-11-03 failed with `UPSTREAM_ERROR` (`apiserver request failed`,
`retryable: true`), a fresh correlation id on each attempt, across more than fifteen calls and
four run ids — `01a1854d-ec55…`, `01a1854f-fbd4…`, `01a18547-020c…`, `01a18f08-b649…`
(correlation ids included `37f131cffe88fedddbc90b67`, `c3a7eea42cdb1430ed3ebf89`,
`4a996c1ddff95c6539ee3ef2`).

`list_runs` returned all eight runs as `succeeded` at the same moment, and `get_skill`,
`get_capabilities`, `get_runtimes`, `get_download_options`, `list_skills` and
`prep_run(action="template")` all answered normally — so the runs are healthy and the outage is
specific to the results read path.

This matters beyond this ticket: **`get_model` and `request_download` both require a `model_id`
handle that only `get_results` returns**, so the entire download path sits behind this one
endpoint. There is no independent route to a bundle. It also blocks #23's scoring path, which
needs results to score a holdout.

---

## 4. Result

| # | Item | Verdict | Evidence |
| --- | --- | --- | --- |
| 1 | Training pipeline | **Absent** | §3.1, §3.2 |
| 2 | Architecture search | **Absent** | §3.1, §3.2 — the architecture is *readable* in the `.npz`; the *search* is not |
| 3 | Loss function | **Absent** | §3.1, §3.2 |
| 4 | Hyperparameters | **Absent** | §3.1, §3.2 |
| 5 | Seeds | **Absent** | §3.1, §3.2 |
| 6 | Preprocessing / type inference | **Absent** | §3.1, §3.2; the alpha independently found constant columns dropped silently and integer identifiers read as numeric |
| 7 | Exclusions | **Partial** | `excluded_inputs` appears in run output (recorded in the alpha) but not in the bundle, and a dropped designed feature was reported as information rather than a warning |

**Verdict: FAIL.** Six of seven absent, one partial, and nothing to re-fit *from* — the
reproduction attempt cannot be started, which is itself the result. The test fails on the
evidence shipped, without needing to execute a re-fit.

---

## 5. What we do either way

- **If 19th ships the fit record:** run §2 against it and record the outcome here. Item 1 alone
  converts SS1/23 P3.5 and SII Art 125 from fail to partial/meet
  ([`model-governance.md` §9](model-governance.md)).
- **If it does not:** this closes as the finding that the bundle stays a **challenger model**, a
  **low-materiality primary model with conditions**, or **"approve with conditions"** — and that
  this single item is what blocks a material reserve, a capital number or an IFRS 17 measurement.

Either way the ticket closes on our own evidence rather than on 19th delivering.

---

## Sources

- [`model-governance.md`](model-governance.md) — the full mapping of the bundle against SS1/23,
  Solvency II, IFRS 17 and the FRC standards, and its §9 ranking of what would change the answer.
- [`docs/19th-validation-note.md`](../docs/19th-validation-note.md) — the note this ticket acts on.
- [`docs/alpha-findings.md`](../docs/alpha-findings.md) — bundle inventory, silent constant-column
  drop, type inference, `excluded_inputs`.
- PRA SS1/23 §1.2, P3.2, P3.5(a) · Solvency II Arts 121(3), 125, 126 · TAS 100 P5.1, P6.1 ·
  FRC TAG Models §9.49, §9.60, §9.61 — full citations in [`model-governance.md`](model-governance.md).
