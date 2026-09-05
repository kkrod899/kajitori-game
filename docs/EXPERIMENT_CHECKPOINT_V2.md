# Production-scope experiment checkpoint v2

Date: 2026-09-05  
Branch: `experiment/production-scope-v1`  
Deployment: prohibited; deployed v0.3 remains unchanged

## Current state

The experiment now has a raw-state-driven candidate engine and an executable shadow-test instrument. It is no longer only a large checklist or a scenario router.

Completed:

- 293-item v1 seed retained as history
- audited v2 overlay: `SAFE-018` rewrite + `SAFE-019` addition
- effective catalog: 294
- health/safety: 43 items, 23 direct + 20 boundary, 0 unresolved review blockers
- 84 experiment-ready activation rules
- 173 catalog items referenced by active rules
- 43/43 health/safety rule coverage
- 137-field raw-state registry with privacy/source classification
- complete-loop card aggregation
- five raw-state synthetic scenarios with feature-gate tests
- practical shadow intake contract
- card/atomic shadow observation schema v2
- deterministic rule-gap / input-gap / engine-miss evaluator
- CI coverage for all above

## Synthetic card result

| Scenario | Now | Today | Routine | Review | Atomic responsibilities |
|---|---:|---:|---:|---:|---:|
| Normal weekday | 2 | 12 | 4 | 2 | 69 |
| High-load heat weekday | 8 | 16 | 4 | 2 | 93 |
| Low-load weekend | 0 | 0 | 3 | 0 | 21 |
| Winter disruption | 1 | 4 | 3 | 0 | 34 |
| No-daycare/no-car | 1 | 10 | 2 | 2 | 48 |

Counts are diagnostics, not goals.

## Important corrections made in v2

### 1. Removed circular discovery validation

v1 scenarios explicitly named the responsibilities to activate. v2 scenario input contains raw household state only; responsibility IDs are engine output.

### 2. Separated atomic responsibilities from cards

69–93 atomic responsibilities do not become 69–93 rows in the interface. Complete-loop bundles produce 14–30 management/review cards depending on household state, while preserving atom-level auditability.

### 3. Resolved the heat/cold source blocker

Heat and winter-weather travel are now separate items with separate official sources and activation contexts.

### 4. Diagnosed misses by cause

Shadow v2 distinguishes missing rule, missing input, and faulty engine decision. This prevents the team from responding to every miss by simply adding more prompts or more items.

## Remaining blockers before PWA integration

1. real seven-day shadow baseline not collected
2. active rules cover 173/294 items; lower-priority household/maintenance domains remain incomplete
3. morning intake burden has only synthetic validation
4. card grouping has not been evaluated by the user in real household conditions
5. phase-two pass thresholds are not yet pre-registered because no baseline exists

## Immediate next sequence

1. freeze the v2 rule/catalog/test artifact
2. create a local-only shadow runner or equivalent low-friction capture method
3. collect seven days without relying on the recommendations
4. evaluate hard gates and rule/input/engine gaps
5. refine rules and bundles
6. pre-register phase-two acceptance thresholds
7. connect to PWA only after phase-two acceptance
