# Production-scope experiment checkpoint v1

Date: 2026-09-05  
Branch: `experiment/production-scope-v1`

## Current state

The experiment deliberately does **not** change the deployed v0.3 PWA yet.

Completed:

- 293-item household responsibility seed master
- machine-readable metadata generation for all 293
- fixed-three target removed from experiment model
- variable-load synthetic day simulation
- source map for high-impact household/child/safety areas
- 42 health/safety items placed behind a manual review gate
- machine-readable health/safety review coverage
- seven-day shadow-test protocol
- shadow observation data contract
- deterministic shadow-test metric evaluator
- CI for metadata, simulation, health/safety review, and shadow metric evaluator

## Synthetic day result

| Scenario | Now | Today | Routine | Review |
|---|---:|---:|---:|---:|
| Normal weekday | 2 | 18 | 19 | 5 |
| High-load weekday | 7 | 27 | 19 | 6 |
| Low-load weekend | 0 | 11 | 16 | 4 |

The counts are not acceptance targets. They demonstrate that household state, not a fixed UI quota, determines candidate volume.

## Open blockers / gaps

### 1. SAFE-018 source boundary

Current master combines heat and cold outdoor risk. Direct official source coverage is strong for heat but incomplete for the cold half. Status: `REWRITE_OR_SPLIT`.

### 2. Item-level applicability / activation detail

The 293 master is structurally broad. The current synthetic profile is coarsely applicable to 289 items. This high number is **not itself a failure**, because many household responsibilities genuinely exist over a long horizon. The production gap is that feature/lifecycle/local/state conditions are not yet item-level complete.

### 3. Synthetic scenarios are not real-life validation

The scenarios prove deterministic behavior and variable load. They do not prove the recommendations match real household reality.

### 4. No active PWA connection yet

Do not merge this experiment into the deployed app until:

- health/safety blocker is resolved
- applicability/activation rules reach experiment-ready maturity
- shadow protocol can be run without relying on the app
- first shadow baseline is collected and audited

## Next sequence

1. Refine high-impact applicability/activation rules
2. Resolve `SAFE-018`
3. Run the seven-day shadow baseline
4. Calculate miss/noise/timing/partner-prompt/close-loop/master-gap metrics
5. Fix the responsibility model
6. Pre-register second-phase acceptance criteria
7. Only then connect production-scope engine to the PWA
