# Issue Tracker — GitHub

Repo: `scotthawes/19th-private-alpha`
Configured by `/setup-matt-pocock-skills`.

## Vocabulary (triage labels)

Canonical role -> label string used here:
- bug -> `bug`
- enhancement -> `enhancement`
- needs-triage -> `needs-triage`
- needs-info -> `needs-info`
- ready-for-agent -> `ready-for-agent`
- ready-for-human -> `ready-for-human`
- wontfix -> `wontfix`

Exactly one category label (`bug`/`enhancement`) and one state label on every triaged issue.

## External PR rule

`external` = pull request whose author is NOT `scotthawes` (the repo owner). Internal PRs are
out of scope for triage discovery. An explicitly named PR is always triaged regardless of author.

## Operations

gh exposes these as first-class commands:
- View issue: `gh issue view N -R scotthawes/19th-private-alpha --json number,title,body,comments,labels,state`
- Create issue: `gh issue create -R scotthawes/19th-private-alpha --title ... --body ... --label ...`
- Comment: `gh issue comment N -R scotthawes/19th-private-alpha --body ...`
- Close: `gh issue close N -R scotthawes/19th-private-alpha` / reopen: `gh issue reopen N -R scotthawes/19th-private-alpha`
- List by label: `gh issue list -R scotthawes/19th-private-alpha --label <label> ...`

Sub-issues and blocking relationships have **no** `gh` subcommand (`gh` 2.101); use `gh api`:
- List sub-issues of #N:
  `gh api repos/scotthawes/19th-private-alpha/issues/N/sub_issues`
- Resolve the database id of any issue: `gh issue view N -R scotthawes/19th-private-alpha --json id -q .id` (a large
  number, NOT the issue #N). All write calls below take this database id.
  - **Verified failure in this repo (2026-10-30):** that command returns a GraphQL node ID (`I_kwDOVbM1rc8AAAABaw4oLQ`),
    not an integer. The sub-issue and dependency endpoints reject it with
    `HTTP 422: Invalid property /sub_issue_id: ... is not of type integer`. Use
    `gh api repos/scotthawes/19th-private-alpha/issues/N --jq .id` instead — it returns the numeric database id
    (e.g. `6091056838`).
- Add a sub-issue:
  `gh api repos/scotthawes/19th-private-alpha/issues/N/sub_issues -X POST -F sub_issue_id=<child-db-id>`
- List what blocks #N: `gh api repos/scotthawes/19th-private-alpha/issues/N/dependencies/blocked_by`
- List what #N blocks: `gh api repos/scotthawes/19th-private-alpha/issues/N/dependencies/blocking`
- Add a blocker:
  `gh api repos/scotthawes/19th-private-alpha/issues/N/dependencies/blocked_by -X POST -F issue_id=<blocker-db-id>`
- Remove a blocker:
  `gh api repos/scotthawes/19th-private-alpha/issues/N/dependencies/blocked_by/<blocker-db-id> -X DELETE`

If a call returns a 404, the endpoints may have moved; inspect with
`gh api repos/scotthawes/19th-private-alpha/issues/N --include` and retry against the path the response
nominates. Sub-issue/blocking ids are the child issue's numeric id, not its `#`-number's URL
form.

Issue reference resolution: bare `#N` resolves against `scotthawes/19th-private-alpha` by default.

## Wayfinding operations

- The map is one issue labelled `wayfinder:map`; its tickets are its sub-issues.
- Ticket labels: exactly one `wayfinder:research|prototype|grilling|task`, plus `wayfinder:map`
  on the parent. Wayfinder issues never carry triage labels.
- Child→parent link comes from the sub-issue relationship (not a body field).
- Frontier query (open, unblocked, unclaimed children): open sub-issues of the map whose
  `dependencies/blocked_by` is empty and which have no assignee. An unclaimed ticket is an
  open sub-issue with no assignee.
- Blocking uses the native GH dependency relationship only (see operations above).

## Tracker provenance

Run `gh --version` and record it here on setup:
- gh version: 2.101.0 (2026-09-15)

External-PR rule repeated for triage: external = author != owner.
