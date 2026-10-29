# Is the CAS triangle data cleared for upload to 19th?

> **Verdict: NOT CLEARED.**
> The 464-triangle dataset used by `tabpfn-reserving` is the CAS Loss Reserve Database, published by the
> Casualty Actuarial Society. The CAS's own Terms of Use prohibit transmitting its materials to a third
> party, and specifically prohibit using them "for developing or training generative AI tools", without
> prior written permission. No permission exists, and no licence anywhere in the chain grants it.
>
> Ticket: `scotthawes/19th-private-alpha#2`. Researched 2026-10-29 against the repos at
> `/Users/Scott/projects/tabpfn-reserving` (read-only) and `/Users/Scott/projects/19th-private-alpha`.
> The subject repo was not modified.

**The one-line version.** 19th's product is "trains a model on a CSV you supply" — so uploading the
triangles is simultaneously a transmission of CAS-sourced material to a third party *and* a use of that
material to train a model. Those are the two things the CAS terms name explicitly.

---

## 1. What the data is, and where it lives

Not committed, not vendored, not downloaded. It **ships inside the `chainladder` package**, which the repo
pins at `0.10.1` and loads by name:

| Evidence | Detail |
| --- | --- |
| `tabpfn-reserving/scripts/fleet_eval.py:43` | `sample = cl.load_sample("clrd")` — "Every (company, line of business) triangle in the CAS Loss Reserve Database." |
| `.../site-packages/chainladder/utils/data/clrd.csv` | 42,845 rows, accident years **1988–1997**, 376 distinct insurer groups, 6 lines of business |
| SHA-256 of `clrd.csv` | `5785a95d5d24943f601a9c46b83cb313ba5109a374331a71e28a86eb702d9eef` |
| `.gitignore:14` | "`# Data — downloaded at run time by scripts/fetch_data.py, never committed`" |
| `README.md:236–241` | "These ship **inside the `chainladder` package** … so nothing is downloaded and nothing is vendored" |

Two defects worth recording, because both are the kind of thing a reviewer would trip on:

- **`scripts/fetch_data.py` does not exist.** The `.gitignore` comment describes a fetch script that was
  never written; the README's account (ships in the package) is the true one.
- **The repo's own descriptions conflict.** `docs/brief.md:124` says "Data is downloaded at run time, never
  vendored"; `README.md:238` says "nothing is downloaded". Both are right that nothing is committed — a
  `data/` directory is gitignored and absent.

The evaluated slice: `results/fleet/FINDINGS.md` — "`containers scanned 775` / `usable triangles 639` /
`evaluations 464`". Committed results (`results/fleet/clrd-*.jsonl`, `coverage.jsonl`) contain **derived
per-unit figures** — reserve points, intervals, realised outcomes — not raw triangle cells.

## 2. Provenance

The `clrd` dataset is the CAS Loss Reserve Database, compiled from **NAIC Schedule P** statutory filings by
Glenn G. Meyers and Peng Shi, and published by the CAS as six per-line CSVs. The bundled file is that
publication, reshaped: one CSV with a `LOB` column instead of six files with `_B`-suffixed columns. Spot
check against the published source (`casact.org/sites/default/files/2021-04/ppauto_pos.csv`): GRCODE 43,
IDS Property Cas Ins Co, AY 1988, lag 1 → `607, 133, 226, 895`. Identical in `clrd.csv`.

- Source page: <https://www.casact.org/publications-research/research/research-resources/loss-reserving-data-pulled-naic-schedule-p>
- The 1988–1997 vintage corresponds to the page's "**EARLIER DATA SETS** (Updated: September 1, 2011)".
  `chainladder` also bundles `clrd2025.csv` for the 1998–2007 refresh, which the repo does **not** use.

The data is **public and not anonymised**: it names real insurer groups ("Allstate Ins Co Grp"),
but it is public regulatory filing data, not confidential portfolio data. That is the strongest fact in
favour of the data being usable.

## 3. What the licence actually says

**The CAS grants no licence to the data.** The page asks for attribution and nothing more:

> "Researchers who use the data sets below should acknowledge in resulting publications that they accessed
> the files from this CAS web page as compiled for the CAS by S&P."

An acknowledgement request is not a grant of redistribution rights. The site-wide Terms of Use supply the
missing prohibition (<https://www.casact.org/terms-use>, §3):

> **Permitted:** "Anyone who is doing personal, noncommercial research may view, print, and temporarily store
> materials from the websites, provided that CAS's copyright notices are not removed…"

> **Prohibited:** "User agrees not to reproduce, distribute, transmit (via print, fax, electronic, or other
> means), modify, alter, or create derivative works of the materials contained on CAS websites…"

> **Prohibited:** "User may not use materials or any CAS AI Tool(s) for developing or training generative AI
> tools, or for commercial purposes, without prior written permission from the CAS."

"Any use other than as described above requires prior written permission from the CAS" — contact given as
`acs@casact.org`.

**Upstream, `chainladder` is MPL-2.0** (`chainladder-0.10.1.dist-info/METADATA: License: MPL-2.0`). That
licence covers the *software*; the package ships no separate data licence and no provenance note for the
CSVs. The repo relies on MPL-2.0 for the code it installs and says nothing about the data.

**In this repo, `LICENSE` is Apache-2.0 and `README.md:303–305` says "Apache-2.0 — see LICENSE" with no data
carve-out.** `docs/readiness.md:66` records "**3.3 | Rights to everything published | ✅ No third-party
restricted data**". On the evidence above that tick is unsupported: nobody has established that the CAS
places no restriction. That claim should be struck or requalified.

## 4. Has this data already gone to a third party? (the decision-relevant precedent)

**On the record: no.** This is the single most important finding, and it cuts *against* the "we've already
done it" argument.

| Evidence | Detail |
| --- | --- |
| `results/spike/runs/20260918-run1-ratio/MANIFEST.md:15` | "tabpfn 9.0.0 · tabpfn-client 0.6.0 · … **CPU only, no API calls**" |
| `results/spike/runs/20260918-run2-delta/MANIFEST.md:14` | same line |
| `results/spike/runs/*/spike_e0_e1_{ratio,delta}.json` | `"backend": "local"` on both recorded runs |
| `results/runs/*/manifest*.json` | every recorded command omits `--backend`, so it defaults to `local` |

The capability exists — `src/tabpfn_reserving/arm.py:47–54` and `scripts/spike_e0_e1.py:100–103` both build a
`tabpfn_client.TabPFNRegressor` under `backend == "client"`, and that client is not local: it POSTs the
training matrix to Prior Labs' `/tabpfn/fit` and `/tabpfn/predict`
(`tabpfn_client/client.py:800–812`). So *if* the client path had been used on triangles, triangle data would
already have left the machine.

But the only artefact that suggests it was used is a claim, not a record: `results/spike/FINDINGS.md:96–109`
says "Both the local package and the hosted client return, under `output_type='full'`…" and times the hosted
route at 7.3 s. **No run directory, manifest, log or fingerprint backs that row**, and every recorded run
asserts "no API calls". Treat the hosted figure as an unrecorded one-off, not as an established precedent.

So the honest answer to "have we already sent this to a vendor?" is: **not in any committed evidence.**
Anyone arguing the precedent should first find the artifact, or they are arguing from an untracked terminal
session.

## 5. Why 19th is a worse case than the TabPFN client path

Even if the Prior Labs client had been used, 19th differs in kind:

- **19th trains.** Its own docs: "19th trains a model on a CSV you supply" (`README.md:4`), `POST /v1/fit`
  with a training CSV (`docs/vendor/19th/training.md`). Prior Labs' TabPFN is in-context inference — the
  rows are inputs to a forward pass. The CAS terms name *training* explicitly; inference is only covered by
  the general transmission prohibition. 19th hits both.
- **Retention and reuse are unstated.** 19th's public Privacy Policy (`https://19th.com/privacy`, last
  updated 2026-04-29) covers the *website* — beta list, email, analytics — and says nothing about training
  data. `app.19th.com/terms` returns **HTTP 401** to an unauthenticated request (verified 2026-10-29:
  `www-authenticate: Bearer realm="OAuth"`), so the upload terms are not publicly readable at all.

That second point matters for a decision: we cannot currently tell a decision-maker what 19th will do with
the bytes, which is exactly the question a data owner asks before granting permission.

## 6. Verdict

| Question | Answer |
| --- | --- |
| May the raw triangle cells be uploaded to 19th today? | **No — not cleared.** No licence grants it; the CAS ToU prohibits transmission and AI-training use without written permission. |
| Is there a precedent to lean on? | **No.** Recorded runs are local with "no API calls"; the hosted claim in `results/spike/FINDINGS.md` has no artifact. |
| Is the data secret? | **No.** Public NAIC Schedule P data, named insurers, published by the CAS. The blocker is the CAS's terms, not confidentiality. |
| Are the *results* already published? | **Yes** — derived per-unit figures in a public Apache-2.0 repo. That is a smaller act than uploading raw cells to a model trainer, and it is not itself a clearance. |

## 7. What a decision-maker needs to confirm next

1. **Get it in writing from the CAS.** `acs@casact.org` — ask whether the Loss Reserve Database may be (a)
   transmitted to a hosted model-training vendor and (b) used to train a model, and whether attribution
   suffices. This is the only route that turns NOT CLEARED into CLEARED, and it is one email.
2. **Ask 19th what happens to uploaded CSVs** — retention period, whether training data is reused, whether
   it is deletable, and whether their terms contain a rights warranty. `hello@19th.com` or Max/Spencer
   (`docs/alpha-notes.md`). Their answers may independently block the upload even with CAS permission.
3. **Correct the record in `tabpfn-reserving`**: `docs/readiness.md:66` ("No third-party restricted data")
   and the Apache-2.0 grant with no data carve-out should be requalified before anyone cites them as
   clearance.

## 8. What would overturn this verdict

- **A written permission from the CAS** covering transmission to a third-party trainer. Decisive.
- **A legal opinion that the CAS has no enforceable rights here.** The underlying numbers are public
  statutory filings; US copyright does not protect facts, and a compilation of public-domain data needs
  original selection or arrangement (*Feist v. Rural Telephone*, 499 U.S. 340 (1991)). The CAS ToU asserts
  copyright over "the entire contents of its websites", which may or may not survive that analysis for these
  CSVs. This is a lawyer's call, not an engineer's — and note the terms bind *users of the site*, which is a
  contract question independent of copyright.
- **Evidence that the `chainladder` maintainers obtained redistribution rights from the CAS** and that
  MPL-2.0 was intended to cover the bundled CSVs. No such evidence exists in the package or its metadata.
  The absence is why the MPL-2.0 label does not settle it.
- **Evidence the data actually used is not the CAS set** — e.g. a synthetic or user-supplied triangle. The
  repo's CLI accepts a user's own triangle (`git log`: "the CLI reads the user's own triangle"), so a
  capability demo on synthetic data needs no CAS permission at all. That is the cheapest unblocked path.

---

## Evidence index

| Claim | Source |
| --- | --- |
| Data loads from the pinned package | `tabpfn-reserving/scripts/fleet_eval.py:43`; `README.md:236–241` |
| Dataset shape and vintage | `chainladder/utils/data/clrd.csv` (1988–1997, 376 GRNAMEs, 6 LOBs) |
| Values match the CAS publication | `ppauto_pos.csv` (CAS, 2011) vs `clrd.csv`, GRCODE 43 / AY 1988 |
| 775 / 639 / 464 | `tabpfn-reserving/results/fleet/FINDINGS.md` |
| CAS attribution request; no licence | CAS Loss Reserving Data page, §"Please note" |
| Transmission and AI-training prohibitions | <https://www.casact.org/terms-use> §3 |
| `chainladder` is MPL-2.0, no data licence | `chainladder-0.10.1.dist-info/METADATA` |
| Repo licence has no data carve-out | `tabpfn-reserving/LICENSE`; `README.md:303–305` |
| "No third-party restricted data" | `tabpfn-reserving/docs/readiness.md:66` |
| Recorded runs made no API calls | `results/spike/runs/*/MANIFEST.md:14–15`; `"backend": "local"` in both run JSONs |
| Client backend posts to Prior Labs | `tabpfn_client/client.py:800–812`; `arm.py:47–54` |
| Unverified hosted claim | `results/spike/FINDINGS.md:96–109` |
| 19th trains on the CSV | `19th-private-alpha/README.md:4`; `docs/vendor/19th/training.md` |
| 19th terms not public | `GET https://app.19th.com/terms` → 401, 2026-10-29 |
