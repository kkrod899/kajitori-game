# ACTIVATION ENGINE v2 — raw state discovery and complete-loop cards

Date: 2026-09-05  
Status: Experiment engine / synthetic validation complete / not connected to deployed PWA

## 1. Why v2 was required

The v1 simulation accepted a list of responsibility IDs as scenario input. That verified layer routing, but it did **not** verify discovery: the scenario author had already decided which responsibilities should appear.

v2 removes responsibility IDs from scenario input. It accepts only a synthetic household profile and raw household facts such as:

- daycare today/tomorrow, unread notice, deadline horizon
- milk/diaper stock state
- meal plan and shopping state
- open household loops
- caregiver-recorded health/safety changes
- official heat or winter weather context
- periodic review due flags

The engine then evaluates activation rules and derives responsibilities.

## 2. Architecture

```text
v1 responsibility metadata (293)
        + audited amendment overlay
        ↓
effective catalog v2 (294)
        ↓ raw household profile + raw state
experiment-ready activation rules (84)
        ↓ health/safety review + boundary gate
atomic responsibilities
        ↓ complete-loop bundle mapping
user-facing cards
```

The deployed v0.3 app is not part of this flow yet.

## 3. Catalog amendment

`SAFE-018` previously combined heat and cold risk. The evidence sources and activation conditions are different, so v2 applies an auditable overlay:

- `SAFE-018`: heat-risk outing check, supported by the official heat/WBGT source
- `SAFE-019`: heavy-snow/blizzard travel check, supported by official JMA warning and early-warning sources

Effective catalog:

- 294 responsibilities
- 43 health/safety responsibilities
- health/safety review: 23 `PASS_DIRECT`, 20 `PASS_WITH_BOUNDARY`, 0 unresolved blockers

This is an integrity/source review, not clinical validation.

## 4. Health/safety gate

A health/safety responsibility is suppressed when any of the following is true:

- review status is blocking
- required official source is missing
- a `PASS_WITH_BOUNDARY` item lacks required raw context
- profile/feature conditions do not apply

The engine never converts missing health/safety input into an assumed `false` state.

Examples of forbidden automation include:

- inferring vaccination due dates from age alone
- diagnosing symptoms
- assuming #8000 availability without local hours
- inventing product-specific stroller rules
- claiming that a safety check prevented an accident

## 5. Atomic coverage vs user-facing cards

A second issue appeared during v2 development: a production-scope catalog can yield dozens of valid atomic responsibilities in one day. Showing each atom as a separate card would recreate overload.

v2 therefore separates:

- **atomic responsibility**: auditable unit used for coverage, evidence, and misses
- **complete-loop card**: user-facing unit that groups responsibilities which should be closed together

Example:

`daycare.tomorrow_ready` may contain the atomic responsibilities for notice review, bag preparation, clothing stock, designated supplies, handoff, and return-item processing. The card is one household loop; the atoms remain available for audit.

## 6. Synthetic result

| Scenario | Now cards | Today cards | Routine groups | Review cards | Atomic responsibilities |
|---|---:|---:|---:|---:|---:|
| Normal weekday | 2 | 12 | 4 | 2 | 69 |
| High-load heat weekday | 8 | 16 | 4 | 2 | 93 |
| Low-load weekend | 0 | 0 | 3 | 0 | 21 |
| Winter disruption | 1 | 4 | 3 | 0 | 34 |
| No-daycare/no-car feature gate | 1 | 10 | 2 | 2 | 48 |

These counts are not targets or pass criteria. They demonstrate variable load and loop aggregation.

## 7. Coverage

Current experiment-ready rules:

- 84 activation rules
- 173 / 294 catalog items referenced
- 43 / 43 health/safety items referenced
- 137 raw state fields in the generated registry
- 60 fields classified as sensitive/local-only

Uncovered items are not silently treated as finished. The largest remaining rule gaps are home maintenance, supplies, cleaning, administration, laundry, and older-child lifecycle items.

## 8. Feature-gate validation

The synthetic no-daycare/no-car scenario deliberately contains contradictory raw facts. Profile gates must win. The engine suppresses:

- daycare responsibilities
- car/child-seat responsibilities
- bottle sterilization when the household policy does not apply
- older-child responsibilities when no older child is configured

## 9. Practical input burden

137 raw paths do not mean 137 daily questions.

`shadow_intake_spec_v2.json` divides facts into:

- morning confirmation
- event-only changes
- official external data
- periodic review

For the current synthetic profile, the initial contract exposes 20 unconditional morning fields, 16 required. Conditional subquestions appear only when the parent answer makes them relevant. Actual responses must remain local and must never be committed to the public repository.

This is still a burden hypothesis. The shadow test must measure whether capture time and omission rate are acceptable.

## 10. What v2 proves and does not prove

### Proven by deterministic tests

- raw state can derive responsibilities without scenario item IDs
- a fixed three-item quota is unnecessary
- atomic coverage and compact cards can coexist
- feature gates suppress contradictory facts
- unresolved or under-contextualized safety items can be suppressed
- heat and winter weather are separated
- card-level and atomic-level metrics can be generated

### Not proven

- recommendations match a real household
- 173 active item rules are enough
- current card groupings are cognitively optimal
- morning input can reliably be completed in two minutes
- partner-prompt dependency decreases
- the engine is safe for active reliance

## 11. Next gate

1. Run an app-independent seven-day shadow baseline.
2. Reconcile at both card and atomic levels.
3. Separate rule gaps, input gaps, and engine misses.
4. Expand or remove rules based on observed evidence.
5. Pre-register phase-two thresholds.
6. Only then connect the engine to the deployed PWA.
