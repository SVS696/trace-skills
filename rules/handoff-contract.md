# Handoff contract

Use when a result moves to another participant, role or project system: an analysis,
specification, design, implementation or infrastructure observation. This contract
adds no stage and requires no area directory layout. Use the project's existing
format; when links already reconstruct the input, supply only missing fields.

## Project ownership

Establish applicable sources of truth, templates, decision owners, artifact locations,
publication authority and required checks from project instructions. Name the owner
of each rule. For example, a tracker owns execution status, a specification approved
behavior, design the agreed interaction artifact, and code/live systems implementation
facts. Resolve conflicts by the project's declared precedence; these examples do not
override its canon. Inspect versions before relying on derived mirrors.

A portable instruction catalog can provide stable IDs and versioned reads. Read the
applicable route and compare contract version plus content digest before mixing rules.
A catalog distributes instructions and does not itself inspect or mutate live state.
Preserve provenance when adapting a method; credentials and personal journals stay local.

## Minimum transfer

Identify sender, recipient and next action, then provide:

1. Goal, current boundaries and observable exit criteria.
2. Authoritative contract, sources and exact versions or content hashes.
3. Result artifacts, accepted decisions and rationale/authorization source.
4. Criterion → actual check → evidence → uncovered portion and residual risk.
5. Unknowns/conflicts, owner, impact and condition for starting dependent work.

Keep recommendations distinct from accepted decisions. Shared context must let the
recipient recover why an option was chosen without the author's private memory.
A known owner does not resolve a missing requirement.

## Evidence by result

| Transfer | Evidence and boundary |
|---|---|
| Analysis → decision owner | Question, coverage, alternatives, recommendation, limits and actual review; delivery does not approve the choice |
| Analysis → specification | Verified framing, preliminary stories/criteria, decisions and unknowns; the existing preanalysis approval route remains required |
| Analysis ↔ Design | Rules, criteria and constraints; checked states/transitions and exact nodes return to Analysis; new behavior needs a recorded decision |
| Analysis → Dev / QA | Approved requirements/version, criteria and risks; Dev owns implementation and QA the testing method |
| Dev → verifier / QA | MR/commit, build, environment, dependencies, data, developer checks and all affected component versions |
| QA → release | Executed scenarios/regressions on a stated version, uncovered checks and risk; QA does not establish merge or deployment |
| Infrastructure → next owner | Dated live observation, authorized change, rollback and client-path validation; a target diagram or old inventory is not current state |

For interface work, cover applicable loading, empty, no-match, error, cancel, retry
and recovery behavior. Check input/context preservation and keyboard/focus behavior
where relevant. Use the project's design system and accessibility rules; adopting a
method does not import another project's colors or components.

## Several repositories

Tie each component to its repository, MR, exact SHA and contract version. Before
claiming integrated readiness, record and exercise the joint build/environment,
old/new provider and consumer compatibility where mixed versions are possible,
migrations, feature flags and merge/deployment order with rollback.

Every MR retains its own review and developer checks. Independent behavioral evidence
covers the joint set of SHAs. A changed component invalidates evidence for its affected
combination: repeat those checks and approval/readiness checks on the new version.
If the joint build cannot be exercised, report the gap instead of inferring integrated
verification from separate green checks.

After merge inspect actual main commits and pipelines. If deployment is part of the
result, compare deployed version with the checked set and validate the client path.
Report approval, review, testing, merge, deployment and acceptance as separate facts;
authorized external writes require exact read-back.
