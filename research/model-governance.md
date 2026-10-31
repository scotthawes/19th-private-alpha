# Model governance: what a GI actuarial regime demands of a 19th `.tfpb` bundle

**Ticket:** [#16](https://github.com/scotthawes/19th-private-alpha/issues/16) · **Date:** 2026-10-31 · **Status:** research complete

## The answer, before the detail

A 19th bundle is an unusually well-evidenced **implementation** and an unusually poorly-evidenced **development**. It is *re-runnable* — same artifact, same inputs, same outputs — and it is not *retrainable*: nothing shipped lets you reproduce the fit. Every regime below separates those two things, and the bundle lands on opposite sides of the line.

The practical consequence:

| Use | Verdict |
| --- | --- |
| **Challenger / benchmark model** | **Approve.** This is the bundle's natural home, and it is a strong one: independent of the primary model, cheap to run, and reproducible. |
| **Low-materiality primary model (tier 3)** | **Approve with conditions** — local scoring, input-sensitivity analysis, ongoing monitoring, and a documented limitation. |
| **Material primary model for reserves, capital or IFRS 17** | **Not approvable on the shipped evidence.** The one thing a validator is entitled to ask for — how the parameters were estimated — is the one thing the bundle cannot answer. |

That is the whole finding. The rest is the mapping.

---

## 1. What is being assessed

The artifact, as established in [`docs/alpha-findings.md`](../docs/alpha-findings.md) and not re-derived here:

- A `.tfpb` bundle: Apache-2.0 source plus a plain `.npz` of 144 arrays — a 256-wide MLP with Kronecker-factorised layers, a spline quantile head, and per-column category embeddings.
- A signed manifest (`oracle-bundle-manifest.v1.json` + `.sig`) and signing certificate.
- Runtime is numpy-only (`numpy==2.2.6`); no TensorFlow, no runtime dependency on 19th; predicts locally in ~0.005 ms/row.
- The model is **frozen**: you can read and re-run it, you cannot retrain it, and the `.tfpb` writer is not shipped.
- The service returns **no absolute accuracy metric**; users must export and score the bundle themselves.

### 1.1 Re-runnable is not retrainable

This distinction carries most of the analysis, so it is worth stating precisely.

| | **Re-runnable** | **Retrainable** |
| --- | --- | --- |
| Definition | Same artifact + same inputs → same outputs. | Reproduce the fit from data. |
| Does the bundle do it? | **Yes.** Deterministic numpy runtime, pinned version, signed digest. | **No.** No trainer, no writer, no hyperparameters, no seeds, no fit procedure. |
| What it supports | Process verification, audit re-performance, operational resilience, challenger use, portability. | Development documentation, replication of parameter estimation, recalibration, sensitivity to specification. |
| What it cannot tell you | Whether the fit was any good, or whether the parameters remain appropriate. | — |

A signature is not a validation. The manifest and certificate prove the bytes are the vendor's and unaltered; they say nothing about methodology, fitness for purpose, or whether anyone validated the fit.

---

## 2. Which regime actually binds

The ticket names four regimes. They do not all apply to the same firm, and one of them does not apply to insurers at all.

| Firm or use | Binding regime | Does SS1/23 apply? |
| --- | --- | --- |
| UK bank, building society or PRA-designated investment firm with internal-model approval | PRA SS1/23 in full | **Yes** |
| GI insurer using a full or partial internal model for the SCR | Solvency II Directive Arts 120–126 (use test, statistical quality, validation, documentation, external models); Art 48 (actuarial function); Art 45 (ORSA) | **No** — insurers are expressly out of scope |
| GI insurer on the standard formula | Art 48 (actuarial function), Art 45 (ORSA), IFRS 17, TAS 100/200 | **No** |
| Any IFoA member doing in-scope GI technical actuarial work | FRC TAS 100 (all work) + TAS 200 (insurance valuations, capital, ORSA, Lloyd's SAO, the Actuarial Function, and other specified work) | **No** — professional standards, not PRA |
| A model used for IFRS 17 measurement | IFRS 17 paras 32–37 and 117–128 | **No** |
| A model used only as a challenger or benchmark | TAS 100 P5/P6 still apply to the actuary's use; less evidence is needed for the model itself | **No** |

So the first concrete finding is a scope correction: **SS1/23 is a banking standard, and a GI actuary cannot be failed against it.** It remains useful — the PRA says firms outside scope "may find the proposed principles useful", and the five principles are the clearest published statement of what model risk management means — but the binding hooks for a GI insurer are Solvency II, IFRS 17 and TAS 100/200. Where this document cites SS1/23, it is as a benchmark for what a rigorous regime would ask, not as a rule an insurer has breached.

One framing point before the detail: the actuary rarely signs the *model*; they sign an opinion — on technical provisions, capital, or an IFRS 17 measurement — that relies on it. That is why the tests below are tests of **reliance** (understanding, documentation, validation, monitoring), not of authorship. A vendor model is not exempt from them; it just makes them harder to discharge.

> "Credit unions, insurers, and reinsurers are not in scope of the MRM expectations in this supervisory statement."
> — [SS1/23 §1.2](https://www.bankofengland.co.uk/-/media/boe/files/prudential-regulation/supervisory-statement/2023/ss123.pdf)

One caveat on instruments: the Solvency II Directive is cited below as the canonical text. The UK onshored it through the Solvency 2 Regulations 2015 and the PRA Rulebook, and is replacing parts of it under Solvency UK; the numbering differs, but the use-test, validation and documentation obligations are materially the same. Check paragraph references against the current PRA Rulebook before quoting them in a validation report.

---

## 3. PRA SS1/23

### 3.1 What it asks for

SS1/23 is built on five principles ([§3.1](https://www.bankofengland.co.uk/-/media/boe/files/prudential-regulation/supervisory-statement/2023/ss123.pdf)):

1. **Model identification and model risk classification** — a model definition, a model inventory, and risk-based tiering.
2. **Governance** — board responsibility, SMF accountability, policies, roles, internal audit, and third-party vendor models.
3. **Model development, implementation and use** — purpose and design, data, development testing, adjustments and expert judgement, documentation, supporting systems.
4. **Independent model validation** — independent review, process verification, performance monitoring, periodic revalidation.
5. **Model risk mitigants** — post-model adjustments, restrictions on use, exceptions and escalations.

The requirements that bite a frozen vendor artifact are concentrated in Principles 1, 3.5, 4.2, 4.3 and 4.4.

In evidence terms, a firm in scope would hold: an **inventory entry** (purpose and use, operating boundaries, assumptions and limitations, validation findings, owner, validator, tier); a **development document** (data, methodology, performance testing, limitations and expert judgement, detailed enough to replicate parameter estimation); an **independent validation report** (components, conceptual soundness, development evidence, data relevance, judgements, additional testing, sensitivity); and a **monitoring pack** (thresholds, benchmarking, sensitivity, outcomes analysis, revalidation cycle, remediation triggers). The bundle's problem is the second and third of these.

### 3.2 The bundle against the five principles

| Principle | What SS1/23 requires | Bundle verdict | Why |
| --- | --- | --- | --- |
| **P1.2 Model inventory** | Purpose and use, operating boundaries, assumptions and limitations, validation findings, governance details ([P1.2(c)](https://www.bankofengland.co.uk/-/media/boe/files/prudential-regulation/supervisory-statement/2023/ss123.pdf)) | **Partial** | The manifest, digest and `model-interface.json` identify the artifact precisely. Nothing states its purpose, operating boundaries, assumptions or limitations. |
| **P1.3 Model tiering** | Materiality and complexity, including interpretability, explainability and transparency ([P1.3(c)](https://www.bankofengland.co.uk/-/media/boe/files/prudential-regulation/supervisory-statement/2023/ss123.pdf)) | **Partial** | Readable code and weights lower the complexity score. But the PRA treats models whose "results and findings cannot be easily repeated or reproduced" as *higher* risk ([§2.8](https://www.bankofengland.co.uk/-/media/boe/files/prudential-regulation/supervisory-statement/2023/ss123.pdf)), and the fit is not reproducible. Data-quality risk cannot be assessed from the bundle. |
| **P3.2 Data** | Data suitable, representative, unbiased; adjustments and proxies documented and validated | **Partial** | The firm owns the raw training data it uploaded and can run its own quality checks. 19th's preprocessing, exclusions and type inference are undocumented — the alpha found constant columns dropped silently and integer identifiers read as numeric. |
| **P3.3 Development testing** | Performance against design objectives, sensitivity to determine operating boundaries, challenger comparisons ([P3.3(b)](https://www.bankofengland.co.uk/-/media/boe/files/prudential-regulation/supervisory-statement/2023/ss123.pdf)) | **Partial** | Input perturbation and challenger models are possible. Sensitivity to specification and parameterisation is not, because refitting is impossible. |
| **P3.5 Development documentation** | "sufficiently detailed so that an independent third party with the relevant expertise would be able to understand how the model operates, to identify the key model assumptions and limitations, and to **replicate any parameter estimation and model results**" ([P3.5(a)](https://www.bankofengland.co.uk/-/media/boe/files/prudential-regulation/supervisory-statement/2023/ss123.pdf)) | **Fails** | The architecture is readable; the parameter estimation is not replicable. This is the single cleanest statement of the disqualifier. |
| **P4.2 Independent review** | Cover all components, assess conceptual soundness, critically analyse development evidence and data relevance, evaluate qualitative judgements, conduct additional testing and review sensitivity analysis ([P4.2(a)](https://www.bankofengland.co.uk/-/media/boe/files/prudential-regulation/supervisory-statement/2023/ss123.pdf)) | **Partial** | Code, weights and interface are reviewable, and a challenger can be built. The development evidence, data relevance and qualitative judgements are not available. |
| **P4.3 Process verification** | Verify inputs, calculations and reporting outputs are accurate, controlled and auditable ([P4.3(a)](https://www.bankofengland.co.uk/-/media/boe/files/prudential-regulation/supervisory-statement/2023/ss123.pdf)) | **Meets** (implementation) | Deterministic numpy, pinned version, signed digest, no vendor runtime. The code can be read, re-run and audited; the artifact survives the vendor. There is no separate specification to verify conformance against, so this is implementation integrity rather than specification conformance. |
| **P4.4 Monitoring** | Performance against thresholds, benchmarking, sensitivity, outcomes analysis, and a decision on adjustment, recalibration or redevelopment ([P4.4(b)–(c)](https://www.bankofengland.co.uk/-/media/boe/files/prudential-regulation/supervisory-statement/2023/ss123.pdf)) | **Partial** | Scoring against outcomes and benchmarking challengers are straightforward. Recalibration and redevelopment are not possible in-house, and the service supplies no absolute metric to monitor against. |
| **P2.6 Vendor models** | Satisfy yourself the vendor model was validated to the same standard; verify the relevance of vendor data and assumptions; validate your own use and monitor outcomes ([P2.6(b)](https://www.bankofengland.co.uk/-/media/boe/files/prudential-regulation/supervisory-statement/2023/ss123.pdf)) | **Fails** | No vendor validation report, no vendor evidence on data or assumptions. Own-use validation and outcomes analysis are possible, but neither supplies the vendor's validation evidence that (i) asks for, and (ii) cannot be done without the vendor's data and assumptions. |

The pattern is consistent: **P4.3 is met, P3.5 fails, and everything else is partial because the artifact gives you the model but not its provenance.**

---

## 4. Solvency II: the use test, and what it does *not* demand

### 4.1 The use test is about use, not provenance

Article 120 requires the undertaking to "demonstrate that the internal model is widely used in and plays an important role in their system of governance … their risk-management system … and their decision-making processes", and in "economic and solvency capital assessment and allocation processes" ([Art 120](https://www.legislation.gov.uk/eudr/2009/138/article/120)).

That is a test of **embedding**, not of model provenance. A frozen bundle that is actually used to price, reserve or allocate capital can satisfy it in principle — arguably better than an in-house model that sits on a shelf, because the artifact is easy to run and hard to ignore.

But three things follow it:

- **Art 121(2):** the undertaking "shall be able to justify the assumptions underlying their internal model to the supervisory authorities."
- **Art 121(3):** data used for the internal model must be accurate, complete and appropriate, and the data sets updated at least annually.
- **Art 126:** "The use of a model or data obtained from a third party shall not be considered to be a justification for exemption from any of the requirements for the internal model set out in Articles 120 to 125."

So the use test does not demand retrainability. **The provenance demand lives in Arts 121, 124 and 125, and Art 126 removes the "it's the vendor's model" defence.** A 19th bundle embedded in an internal model is held to exactly the same standard as an in-house model, with less evidence. In evidence terms, the firm would need decision papers, capital-allocation records, ORSA material and AMSB minutes showing the model's output was actually used — and, behind them, the Arts 124–125 file that shows the model was understood and validated.

### 4.2 Validation and documentation

Article 124 requires a regular validation cycle: monitoring performance, reviewing the ongoing appropriateness of the specification, testing results against experience, testing sensitivity "to changes in key underlying assumptions", and assessing the accuracy, completeness and appropriateness of the data ([Art 124](https://www.legislation.gov.uk/eudr/2009/138/article/124)).

Article 125 requires documentation of the design and operational details, a "detailed outline of the theory, assumptions, and **mathematical and empirical bases** underlying the internal model", and an indication of "any circumstances under which the internal model does not work effectively" ([Art 125](https://www.legislation.gov.uk/eudr/2009/138/article/125)).

| Requirement | Bundle verdict | Why |
| --- | --- | --- |
| Test results against experience | **Meets** | You can score the frozen model on new data. |
| Sensitivity to key underlying assumptions | **Partial** | You can perturb inputs; you cannot perturb the fitted parameters or the specification. |
| Assessment of data accuracy, completeness, appropriateness | **Partial** | The firm can assess the data it supplied; 19th's preprocessing is opaque. |
| Theory and assumptions | **Partial** | Architecture is readable; the learned assumptions are not stated. |
| Mathematical and empirical bases | **Fails** | The empirical basis is the fit, and the fit cannot be reproduced. |
| Circumstances of ineffectiveness | **Fails** | The only signal is the opaque warning on `high` and `ultra` — *"Additional training limitation recorded; review the data and model suitability before relying on predictions."* — with no code or detail. That is not a documented limitation. |

This is the binding analogue of SS1/23 P3.5(a) for an insurer, and it fails for the same reason.

### 4.3 The actuarial function: the hook that applies even without an internal model

Article 48 is the requirement most GI actuaries actually work under, and it does not depend on internal-model approval. The actuarial function must:

> "(b) ensure the appropriateness of the methodologies and underlying models used as well as the assumptions made in the calculation of technical provisions;
> (c) assess the sufficiency and quality of the data used in the calculation of technical provisions;
> (d) compare best estimates against experience …"
> — [Art 48(1)](https://www.legislation.gov.uk/eudr/2009/138/article/48)

If a 19th bundle is used in the calculation of technical provisions, the actuarial function has to sign off (b) and (c). From the artifact alone it cannot: it can see the code and the weights, but not the estimation of those weights or the vendor's data handling. That is a **fail for a primary reserving use**, and it is why the challenger role is the honest one.

---

## 5. IFRS 17: the estimate is constrained, not the model

IFRS 17 does not prescribe a model class, an algorithm or an estimation technique. It constrains the **properties of the estimate** and the **disclosures around it**. That is good news for a neural network and bad news for a frozen one, in specific ways.

### 5.1 What the standard requires of the estimate

- **Unbiased, probability-weighted mean of the full range of outcomes** — para 33(a): estimates "shall incorporate, in an unbiased way, all reasonable and supportable information available without undue cost or effort … the expected value (ie the probability-weighted mean) of the full range of possible outcomes" ([IFRS 17 para 33](https://www.aasb.gov.au/admin/file/content105/c9/AASB17_07-17.pdf)).
- **Entity's perspective, market-consistent where relevant** — para 33(b).
- **Current** — para 33(c): estimates "shall reflect conditions existing at the measurement date, including assumptions at that date about the future."
- **Explicit risk adjustment, separately estimated** — para 33(d), and para 37: the entity "shall adjust the estimate of the present value of the future cash flows to reflect the compensation that the entity requires for bearing the uncertainty … that arises from non-financial risk."
- **Update each period** — para B54: "An entity shall review the estimates that it made at the end of the previous reporting period and update them", considering whether the updated estimates "faithfully represent the conditions at the end of the reporting period."

The standard is explicitly model-agnostic about technique: para B39 accepts that "relatively simple modelling may give an answer within an acceptable range of precision", while noting that where cash flows are non-linear, "more sophisticated stochastic modelling is likely to be necessary". A 256-wide MLP is admissible. The question is whether it produces the estimate IFRS 17 describes, and whether you can evidence that it does.

### 5.2 Where a frozen model bites

| IFRS 17 requirement | Bundle verdict | Why |
| --- | --- | --- |
| Unbiased, probability-weighted mean (33(a)) | **Partial** | The artifact returns point predictions (and probabilities for classification); it does not present a validated distribution of outcomes. The internal spline quantile head is not documented as a basis for the mean or the risk adjustment. |
| Current (33(c), B54) | **Partial** | Current *inputs* can be fed to a frozen model. Whether the frozen *parameters* still produce a current estimate is an empirical question the bundle cannot answer, and B54 requires the entity to review and update the estimate each period. |
| Entity's perspective (33(b)) | **Partial** | A model trained on the entity's own data reflects the entity's experience. A model trained on synthetic or pooled data — as in the alpha's reserving arm — reflects the generator, not the entity. |
| Explicit risk adjustment (33(d), 37) | **Fails** | A point prediction is not a risk adjustment. The actuary must estimate the risk adjustment separately, and disclose the confidence level or technique (para 119). The bundle does not supply it. |
| Disclosure of methods and inputs (117) | **Partial** | Para 117(a) requires disclosure of "the methods used to measure insurance contracts … and the processes for estimating the inputs to those methods", with quantitative information "unless impracticable". The architecture is readable; the fit process and hyperparameters are not. |
| Sensitivity disclosure (128) | **Partial** | Input sensitivities can be produced; sensitivities to parameterisation cannot. |

So the IFRS 17 answer is: **no constraint on the model family, a real constraint on the evidence that the estimate is current and unbiased.** A frozen model can be an input to an IFRS 17 measurement; it cannot be the whole measurement, and it cannot be signed off as "current" without a parameter-appropriateness assessment that the bundle does not support.

One practical consequence: because B54 requires updating each period, a refit is a *change in method or process* that para 117(b) requires the entity to disclose, with the reason and the contracts affected. With a frozen vendor model, every refit is a new vendor event and a new disclosure — not a routine in-house recalibration.

---

## 6. Peer review: what a reviewer is entitled to ask for

A reviewer's entitlement is not unlimited, but it is specific. Three layers apply.

### 6.1 The regulatory layer

SS1/23 P4.2 entitles the reviewer to:

- all model components, including inputs, calculations and reporting outputs;
- an assessment of the conceptual soundness of the underlying theory and the model's suitability for its intended use;
- a critical analysis of the quality and extent of the development evidence, including the relevance and completeness of the data;
- an evaluation of the qualitative information and judgements used in development;
- additional testing and analysis, including review of the developers' sensitivity analysis and the impact of key assumptions and variable selection.

([SS1/23 P4.2(a)](https://www.bankofengland.co.uk/-/media/boe/files/prudential-regulation/supervisory-statement/2023/ss123.pdf))

For an insurer, Art 124 gives the same shape: monitoring, specification review, testing against experience, sensitivity to key assumptions, data assessment.

### 6.2 The professional layer

TAS 100 P6 requires documentation "sufficient detail to allow technically competent persons responsible for reviewing or providing assurance … to understand the matters involved and assess the judgements made", and P6.1 lists what it must contain: judgements and justifications, data, assumptions, how the model is fit for purpose and what it does (including intended uses and limitations), model governance and controls, and the implications of modelled actions ([TAS 100 v2.0, P6](https://www.frc.org.uk/documents/4287/TAS_100_General_Actuarial_Standards_Version_2.0.pdf)).

TAS 200 adds the insurance-specific hook: for the valuation of insurance contract liabilities, the practitioner should assess whether actual experience differs materially from prior assumptions and "identify the causes of those differences" ([TAS 200 v2.0, P2.1](https://www.frc.org.uk/documents/7708/TAS_200_version_2-0.pdf)).

### 6.3 The third-party layer

For a vendor model, SS1/23 P2.6(b) entitles the firm — and therefore its validator — to satisfy itself that the vendor validated the model to the same standard, and to verify the relevance of the vendor's data and assumptions. The FRC's model guidance is explicit that the user of a third-party model still owns Principle 5 compliance, and may only rely on the provider's evidence "where available" ([TAG Models §2.12](https://www.frc.org.uk/documents/7748/Technical_Actuarial_Guidance_Models_October_2024.pdf)).

### 6.4 The checklist, against the bundle

| What a reviewer can ask for | Source | Bundle supplies? |
| --- | --- | --- |
| Purpose, intended use, limitations | TAS 100 P6.1(d) | **Partial** — interface schema, no limitation statement |
| Data used, quality and relevance | TAS 100 P6.1(b); SS1/23 P3.2 | **Partial** — firm has the raw data; vendor preprocessing opaque |
| Assumptions | TAS 100 P6.1(c) | **No** — learned, not stated |
| Judgements and justifications (model choice, hyperparameters) | TAS 100 P6.1(a); TAG Models §9.49 | **No** |
| Code and parameters | SS1/23 P4.2(a)(i); TAG Models §3 (direct approach) | **Yes** |
| Replication of the fit, seeds, training procedure | SS1/23 P3.5(a); TAG Models §9.49 | **No** |
| Validation findings and sensitivity analysis | SS1/23 P1.2(c)(iii), P4.2(a)(v) | **No** — must be generated |
| Governance, controls and testing | TAS 100 P6.1(e) | **Partial** — signature and runtime tests, no development controls |
| Change log and version history | SII Art 125; SS1/23 P1.2 | **Partial** — manifest version, no history |

The FRC's neural-network case study is directly on point: for a reserving model of this kind, the guidance lists as additional steps recording seeds "to allow a reviewer to reproduce the random processes", documenting the choice of hyperparameters, using a test data set separate from training, and having peer review by both a reserving and a machine-learning subject-matter expert ([TAG Models §9.49, §9.52](https://www.frc.org.uk/documents/7748/Technical_Actuarial_Guidance_Models_October_2024.pdf)). The bundle supplies none of the first three.

One important counterweight: the same guidance says reproducibility in the sense of "sufficient supporting information … to enable an identical model, producing identical outputs, to be trained" is **not required by TAS 100**, and the practitioner may judge it is not required by other applicable regulation ([TAG Models §9.60](https://www.frc.org.uk/documents/7748/Technical_Actuarial_Guidance_Models_October_2024.pdf)). So under the professional standard, retrainability is a *condition*, not an absolute bar — provided the practitioner understands the model (P5.1), tests its stability, and sets retraining or replacement triggers (§9.61). Under SS1/23 P3.5(a) and Solvency II Art 125, it is closer to a bar.

---

## 7. Consolidated verdict

| # | Requirement | Source | Verdict | Why |
| --- | --- | --- | --- | --- |
| 1 | Scope of SS1/23 | [SS1/23 §1.2](https://www.bankofengland.co.uk/-/media/boe/files/prudential-regulation/supervisory-statement/2023/ss123.pdf) | **Not applicable** | Insurers and reinsurers are expressly out of scope. It is a voluntary benchmark for a GI actuary, not a rule. |
| 2 | Model identification and inventory | [SS1/23 P1.2](https://www.bankofengland.co.uk/-/media/boe/files/prudential-regulation/supervisory-statement/2023/ss123.pdf) | **Partial** | Manifest, digest and interface identify the artifact; purpose, operating boundaries, assumptions and limitations are absent. |
| 3 | Development documentation (replicate parameter estimation) | [SS1/23 P3.5(a)](https://www.bankofengland.co.uk/-/media/boe/files/prudential-regulation/supervisory-statement/2023/ss123.pdf) | **Fails** | The fit cannot be replicated: no trainer, no writer, no hyperparameters, no seeds. |
| 4 | Data used | [SS1/23 P3.2](https://www.bankofengland.co.uk/-/media/boe/files/prudential-regulation/supervisory-statement/2023/ss123.pdf) | **Partial** | Firm owns the raw data; vendor preprocessing, exclusions and type inference are undocumented. |
| 5 | Development testing and specification sensitivity | [SS1/23 P3.3(b)](https://www.bankofengland.co.uk/-/media/boe/files/prudential-regulation/supervisory-statement/2023/ss123.pdf) | **Partial** | Input sensitivity and challengers are possible; refit sensitivity is not. |
| 6 | Independent review | [SS1/23 P4.2](https://www.bankofengland.co.uk/-/media/boe/files/prudential-regulation/supervisory-statement/2023/ss123.pdf) | **Partial** | Code and weights are reviewable; development evidence and judgements are not. |
| 7 | Process verification (implementation integrity) | [SS1/23 P4.3](https://www.bankofengland.co.uk/-/media/boe/files/prudential-regulation/supervisory-statement/2023/ss123.pdf) | **Meets** | Deterministic, signed, numpy-only, dependency-free; re-runnable and auditable. No separate specification against which to verify conformance. |
| 8 | Ongoing monitoring | [SS1/23 P4.4](https://www.bankofengland.co.uk/-/media/boe/files/prudential-regulation/supervisory-statement/2023/ss123.pdf) | **Partial** | Outcomes analysis and benchmarking are possible; recalibration and redevelopment are not; no absolute metric from the service. |
| 9 | Vendor model | [SS1/23 P2.6(b)](https://www.bankofengland.co.uk/-/media/boe/files/prudential-regulation/supervisory-statement/2023/ss123.pdf) | **Fails** | No vendor validation report and no vendor evidence on data or assumptions. |
| 10 | Use test | [SII Art 120](https://www.legislation.gov.uk/eudr/2009/138/article/120) | **Partial** | Use in decisions is demonstrable; the provenance demands sit in Arts 121, 124–126, and Art 126 removes the third-party exemption. |
| 11 | Validation and documentation | [SII Arts 124–125](https://www.legislation.gov.uk/eudr/2009/138/article/124) | **Fails** | Results against experience and input sensitivity are possible; the "mathematical and empirical bases" and the circumstances of ineffectiveness are not documented. |
| 12 | Actuarial function (technical provisions) | [SII Art 48(1)(b)–(c)](https://www.legislation.gov.uk/eudr/2009/138/article/48) | **Fails** | Cannot ensure the appropriateness of the underlying model or the sufficiency and quality of the data from the artifact alone. |
| 13 | IFRS 17 measurement | [IFRS 17 paras 33, 37, B54](https://www.aasb.gov.au/admin/file/content105/c9/AASB17_07-17.pdf) | **Partial** | Model-agnostic; a current, unbiased, probability-weighted estimate is achievable with current inputs, but parameter appropriateness and the B54 update duty need evidence the bundle lacks. |
| 14 | IFRS 17 disclosure | [IFRS 17 paras 117, 128](https://www.aasb.gov.au/admin/file/content105/c9/AASB17_07-17.pdf) | **Partial** | Methods and inputs must be disclosed; the architecture is readable, the fit process is not. |
| 15 | Peer review | [TAS 100 P6](https://www.frc.org.uk/documents/4287/TAS_100_General_Actuarial_Standards_Version_2.0.pdf); [TAG Models §4.26](https://www.frc.org.uk/documents/7748/Technical_Actuarial_Guidance_Models_October_2024.pdf) | **Partial** | Code and parameters are reviewable; data, assumptions, judgements, fit and limitations are not. |

**The single most disqualifying requirement:** SS1/23 P3.5(a)'s requirement that an independent expert be able to "replicate any parameter estimation and model results" — and, for an insurer where SS1/23 does not bind, its binding analogue in Solvency II Art 125 ("mathematical and empirical bases") read with Art 126 (third-party status is no exemption).

**The single most favourable requirement:** SS1/23 P4.3 process verification. The signed, deterministic, numpy-only, dependency-free bundle is more auditable than a typical in-house model, and than any hosted vendor model that does not ship its code. It is the artifact's strongest feature.

---

## 8. Can an actuary put this in a validation pack?

Yes — but as an **artifact under validation**, not as **validated evidence**. A validation pack can contain the bundle, its digest and signature, a local re-run log, input-sensitivity and challenger comparisons, the firm's own holdout scoring, and a monitoring plan; that is a strong implementation file. It cannot contain the development record, a replication of the fit, the vendor's validation report, the data lineage, or the circumstances in which the model stops working. On the evidence actually shipped, an actuary can sign a **challenger role**, a **low-materiality primary use**, or an **"approve with conditions"** for a primary use; they cannot sign an **unconditional approval of a material reserve, capital or IFRS 17 number**, because the one question a reviewer is entitled to ask — how were the parameters estimated, and do they remain appropriate? — is the one question the bundle cannot answer. The condition that would change that is not a better signature or a larger `.npz`; it is the fit record: the training pipeline, the hyperparameters and seeds, the vendor's validation report with absolute metrics, and a documented statement of the model's operating boundaries and failure modes.

---

## 9. What would change the answer

In descending order of leverage:

1. **Ship the development record** — training pipeline, architecture search, loss, hyperparameters, seeds, preprocessing and exclusions. This alone converts P3.5 and Art 125 from fail to partial/meet.
2. **Ship a validation report with absolute metrics** — accuracy, calibration, holdout protocol, and the limitations behind the "additional training limitation" warning. This addresses P2.6(b), P4.4 and the "no absolute metric" gap.
3. **Document the operating boundaries and failure modes** — the training data range, the unseen-category behaviour, and the conditions under which predictions should not be used. This addresses P1.2(c), Art 125 and TAS 100 P6.1(d).
4. **Provide a supported recalibration path** — the `.tfpb` writer or a pinned retrain API. This addresses P4.4(b)(iii) and the B54 update duty. Without it, every refit is a new vendor model and a new IFRS 17 method-change disclosure.
5. **Nothing else matters as much.** A longer signature chain, a larger bundle or a faster runtime does not move any of the verdicts above.

---

## Sources

**PRA**
- SS1/23 *Model risk management principles for banks*, May 2023 — [publication page](https://www.bankofengland.co.uk/prudential-regulation/publication/2023/may/model-risk-management-principles-for-banks) · [PDF](https://www.bankofengland.co.uk/-/media/boe/files/prudential-regulation/supervisory-statement/2023/ss123.pdf). Cited: §§1.2, 1.5, 2.8, 2.10, 2.14, 3.1; P1.2, P1.3, P2.6, P3.2, P3.3, P3.5, P4.2, P4.3, P4.4.

**Solvency II**
- Directive 2009/138/EC — [Art 48 (actuarial function)](https://www.legislation.gov.uk/eudr/2009/138/article/48) · [Art 120 (use test)](https://www.legislation.gov.uk/eudr/2009/138/article/120) · [Art 121 (statistical quality)](https://www.legislation.gov.uk/eudr/2009/138/article/121) · [Art 124 (validation)](https://www.legislation.gov.uk/eudr/2009/138/article/124) · [Art 125 (documentation)](https://www.legislation.gov.uk/eudr/2009/138/article/125) · [Art 126 (external models)](https://www.legislation.gov.uk/eudr/2009/138/article/126). EU original: [EUR-Lex](https://eur-lex.europa.eu/eli/dir/2009/138/oj).

**IFRS 17**
- IASB, *IFRS 17 Insurance Contracts* — [standard page](https://www.ifrs.org/issued-standards/list-of-standards/ifrs-17-insurance-contracts/) (full text is subscription-only).
- AASB 17, the Australian adoption with identical paragraph numbering and text for the core standard — [PDF](https://www.aasb.gov.au/admin/file/content105/c9/AASB17_07-17.pdf). Cited: paras 32, 33, 37, 117, 119, 128, B37–B41, B54.

**Professional standards (FRC)**
- TAS 100 *General Actuarial Standards*, v2.0 — [page](https://www.frc.org.uk/library/standards-codes-policy/actuarial/tas-100/) · [PDF](https://www.frc.org.uk/documents/4287/TAS_100_General_Actuarial_Standards_Version_2.0.pdf). Cited: P5.1–P5.4, P6, P6.1.
- TAS 200 *Insurance*, v2.0 — [page](https://www.frc.org.uk/library/standards-codes-policy/actuarial/tas-200/) · [PDF](https://www.frc.org.uk/documents/7708/TAS_200_version_2-0.pdf). Cited: §§1.2, 1.4, 1.8; P2.1.
- *Technical Actuarial Guidance: Models*, October 2024 — [PDF](https://www.frc.org.uk/documents/7748/Technical_Actuarial_Guidance_Models_October_2024.pdf). Cited: §§2.10–2.14, 3.8, 4.26, 9.49, 9.52, 9.60, 9.61.

**19th artifact**
- [`docs/alpha-findings.md`](../docs/alpha-findings.md) — bundle contents, runtime, model internals, the `high`/`ultra` limitation warning, silent constant-column drop, type inference.
- [`docs/19th-alpha-report.md`](../docs/19th-alpha-report.md) — no absolute accuracy metric; export-and-score requirement.
