# Where 19th adds value for a GI actuary

Our judgement, not a vendor document. The [alpha report](19th-alpha-report.md) is what we sent the 19th team on
2026-10-31; this is what we concluded for ourselves. It supersedes that report *in judgement only* — the report
stays as sent, and remains the record of what the vendor received.

The four axes are ranked by what an actuary signs off, not by what is easy to measure: **accuracy, deployment,
economics, auditability.**

## The verdict

> 19th is a deployment product, not an accuracy product: it adds value where deployment is the binding constraint,
> provided the use sits within what a re-runnable, signed artifact can evidence — with explainability binding for
> underwriting — and not where accuracy is the binding constraint, as in reserving, where a matched control over
> 1,200 cells showed no edge (+0.0015, z = +0.62).

## What the verdict rests on

One controlled comparison, and one set of measured engineering facts. It is worth being precise about which is
which, because the two point in opposite directions.

**The controlled comparison is a negative, and it is the only controlled comparison we have.** A matched TabPFN
control on the same 1,200 cells, same seven columns, same transform:

| | Slope of log error against depth |
| --- | --- |
| 19th | +0.0493 (se 0.0018) |
| TabPFN control | +0.0478 (se 0.0016) |
| Difference | +0.0015 (z = +0.62) |

Indistinguishable. The depth-dependent bias is not a property of the model class, and 19th offers no modelling
edge on this problem.

**The deployment measurements are positive.** The exported bundle scored 1,200 held-out rows in about a second
against minutes for TabPFN through in-context inference; the bundles we measured run from 96 KB to 1.45 MB; the
runtime is numpy-only and Apache-2.0, with no service dependency at inference, at roughly 0.005 ms/row. This is
the strongest thing about the product for our use case, and it is measured, not asserted.

**The two workstreams that say "adds value" rest on neither of these.** They come from a single binary dataset
(0.9735 accuracy, 0.9987 AUC on 113 holdout rows) with no matched control. That is why the overall verdict is
built on the reserving negative and the deployment facts rather than on them.

## The four axes

| Axis | What we found |
| --- | --- |
| **Accuracy** | No edge demonstrated on the measured problem — one separable dataset, one reserving arm, 1,200 cells. |
| **Deployment / portability** | Favourable, and measured: about one second for 1,200 rows, 96 KB–1.45 MB, numpy-only, no runtime dependency on 19th. |
| **Economics** | **Unmeasured.** No cost, pricing, licence or compute analysis exists. It is not a favourable axis and must not be counted as one. |
| **Auditability** | Partial — meets process verification, fails development evidence. See below. |

## The workstreams

Seven rows, ordered by verdict. The basis is *reasoned negatives, measured positives*: architecture reasoning may
disqualify a row, because absence of extrapolation is a provable fact about the artifact, but it may not endorse
one. Every "adds value" verdict rests on measurement; every structural "does not" rests on a property that can be
pointed at. A row we cannot defend is not cut and not silently omitted — it names the test that would settle it.

| Row | Verdict | Basis | What would flip it |
| --- | --- | --- | --- |
| **Conversion / propensity** | Adds value — conditional on deployment | Measured (binary: 0.9735 accuracy, 0.9987 AUC on WDBC) | A harder binary dataset where AUC can actually move, or a deployment claim that fails on the REST route |
| **Underwriting risk selection** | Adds value — conditional on deployment, explainability binding | Measured binary + reasoned caveat | A validated relativities layer would lift the caveat; adverse-action and discrimination constraints may still veto it |
| **Reserving — link ratios, IBNR** | Does not add value | Measured | A mechanism for extrapolating a continuous depth covariate instead of routing it through the unseen-category bucket |
| **Capital modelling** | Does not add value | Reasoned — structural | Nothing plausible: stress extrapolation is the job, and the artifact has no learned response outside the observed range |
| **Experience analysis** | Does not add value | Reasoned — structural | A validated relativities layer — coefficients or monotonicity — without which an actuary cannot read the model |
| **Claims triage** | Unknown | Neither — multiclass untested | The 77-class `support_intents.csv` run, scored against a baseline |
| **Frequency–severity** | Unknown | Neither — unmeasured | A frequency fit with log-exposure as an input column, compared to a GLM on deviance |

## What it can be signed for

The artifact is **re-runnable but not retrainable**. That does not block the model — it fixes which role the model
can hold.

| | Re-runnable | Retrainable |
| --- | --- | --- |
| Definition | Same artifact + same inputs → same outputs | Reproduce the fit from data |
| The bundle | **Yes** — deterministic numpy runtime, pinned version, signed digest | **No** — no trainer, no `.tfpb` writer, no hyperparameters, no seeds |
| Supports | Process verification, audit re-performance, operational resilience, challenger use, portability | Development documentation, replication of parameter estimation, recalibration, specification sensitivity |
| Cannot tell you | Whether the fit was any good, or whether the parameters remain appropriate | — |

So: **auditability is partial.** The bundle meets process verification — signed, deterministic, and re-runnable, so
a reviewer can re-perform it and read every array — and fails development evidence, because the fit cannot be
rebuilt from data and code (SS1/23 P4.3 against P3.5(a)).

An actuary can sign a **challenger role**, a **low-materiality primary use**, or an **"approve with conditions"** for
a primary use. They cannot sign an **unconditional approval of a material reserve, capital or IFRS 17 number**,
because the one question a reviewer is entitled to ask — how were the parameters estimated, and do they remain
appropriate? — is the one question the bundle cannot answer. The standards mapping is in
[`research/model-governance.md`](../research/model-governance.md).

## What would change it

- **Economics** — a cost analysis against TabPFN (licence, compute, integration) would let it be claimed. Until
  then it is a stated gap, not a favourable axis.
- **Reserving** — reopens if the artifact gains a mechanism for extrapolating a continuous depth covariate, instead
  of routing depth through a category it never trained on.
- **Auditability** — shipping the fit record (training pipeline, hyperparameters, seeds, and a validation report
  with absolute metrics) moves SS1/23 P3.5(a) and Solvency II Art 125 without changing the artifact.

## What this does not say

- It does not say 19th has **no accuracy edge**. It says none was demonstrated here: one separable dataset, one
  reserving arm, 1,200 cells.
- It does not endorse 19th for **material reserves, capital or IFRS 17**. Those uses fail development evidence, and
  no amount of signature or bundle size changes that.
- It does not put a figure on **economics**. We have not measured cost, and a claim without measurement would break
  the basis rule the workstream table runs on.
- It does not cover **life and pensions**, or GI workstreams outside the seven rows. Capital and experience analysis
  are reasoned from the architecture, not measured.

No new tests were run for this document. The evidence is in [`alpha-findings.md`](alpha-findings.md) — 15 findings
and 12 open questions, with run IDs.
