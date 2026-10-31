# 19th — what an actuary would need before signing

To the 19th team, following our alpha report of 2026-10-31.

The report covered what we found using 19th on a reserving problem. This note covers a different question, which
we were asked internally and could not answer from it: if a general-insurance actuary wanted to use this in a model
they sign off, what would stand in the way?

## A correction first

The report quoted "4.2 MB" for the export. The bundles we actually measured were 96 KB (Fast), 377 KB (the standard
export) and 1.45 MB (one larger bundle). The point stands — it is small, dependency-free and inspectable, and it is
still the strongest thing about the product for our use case — but the figure was ours and it was wrong.

## The question a validator gets to ask

A peer reviewer or an independent validator is entitled to ask how the parameters were estimated, and whether they
remain appropriate. In our own regimes that is not a procedural nicety: the standard a PRA supervisor uses as a
benchmark asks that an independent expert be able to "replicate any parameter estimation and model results"
(SS1/23 P3.5(a)), and for an insurer the binding version is Solvency II Art 125 read with Art 126 — the third-party
status of the model is not an exemption.

## What the artifact already does well

More than most. It is **re-runnable**: a deterministic numpy runtime, a pinned version, a signed manifest and
digest, so the same artifact and the same inputs give the same outputs. It is **legible**: 144 arrays in a plain
`.npz`, readable and portable. For process verification and audit re-performance — can we reproduce the numbers we
were given? — that is better than a typical in-house model, and better than any hosted model that does not ship its
code. We would sign that part.

## Where it stops

It is not **retrainable**. There is no trainer, no writer for the format, no hyperparameters and no seeds, so the
fit cannot be rebuilt from data and code. That distinction — re-runnable versus retrainable — is the whole of it:
everything about running the model is auditable, and nothing about fitting it is.

Today, on the evidence shipped, an actuary can sign this as a **challenger model**, as a **low-materiality primary
model with conditions**, or **"approve with conditions"** for a primary use. They cannot sign it as the sole support
for a material reserve, a capital number or an IFRS 17 measurement.

## What would move it, in order of leverage

1. **Ship the fit record** — training pipeline, architecture search, loss, hyperparameters, seeds, preprocessing and
   exclusions. Nothing else moves as much.
2. **Ship a validation report with absolute metrics** — accuracy, calibration, the holdout protocol, and the
   limitations behind the "additional training limitation" warning. Right now users must export and score the model
   themselves to learn whether it is any good.
3. **Document the operating boundaries and failure modes** — the training range, the unseen-category behaviour, and
   the conditions under which predictions should not be used.
4. **Provide a supported recalibration path** — the writer, or a pinned retrain API. Without it every refit is a new
   vendor model and, under IFRS 17, a new method-change disclosure.

We are not your validator and we are not asking for any of this to be public. But if your target is regulated
general-insurance work rather than a demo, items 1–3 are the cheapest real progress available, and all three are
documentation rather than modelling.
