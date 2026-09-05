# SHADOW TEST v2 — card/atomic reconciliation and miss diagnosis

Date: 2026-09-05  
Status: Pre-registered experiment instrument / app-independent

## 1. Purpose

The first real-life test must answer whether the household model can find useful responsibilities before the user depends on it.

The engine runs in shadow mode. Its output is stored but is not treated as the source of truth during the day. Normal household judgment, partner communication, daycare/local instructions, medical guidance, product manuals, and official information remain primary.

## 2. Why v2 changes the observation model

The v1 evaluator counted surfaced recommendations and missed responsibilities, but it could not distinguish three different failures:

1. **rule gap** — no active rule covered the responsibility
2. **input gap** — a rule existed, but the required real-world fact was not captured or integrated
3. **engine miss** — the rule and required input existed, but the engine still failed to surface it

It also mixed card-level noise with atomic responsibility coverage.

v2 records both:

- user-facing candidate cards
- actual atomic responsibilities contained in those cards

## 3. Observation rows

`data/shadow_observation_schema_v2.json` defines two row scopes.

### `actual_atomic`

One row for each responsibility that actually mattered that day.

It records whether the responsibility surfaced, which card contained it, timing, discovery source, partner prompt, loop closure, rule coverage, and input availability.

### `surfaced_card_only`

One row for a surfaced card that was wholly unnecessary that day.

This prevents a bundled card containing five atoms from being counted as five noisy suggestions.

## 4. Miss classification

For `actual_needed=true` and `surfaced=false`, classification is deterministic:

```text
rule_covered=false
    → rule gap

rule_covered=true
and input_available_at_decision_time=false
    → input gap

rule_covered=true
and input_available_at_decision_time=true
    → engine miss
```

Input gaps are further labelled:

- `not_observed`
- `not_integrated`
- `unknown_feature`

## 5. Hard gates

Any of the following blocks active reliance:

- critical engine miss
- critical input miss
- critical rule gap
- evidence overclaim

A critical miss is a missed health/safety or hard-deadline responsibility.

The categories remain separate because their fixes differ. Adding more rules does not repair missing observations; asking more questions does not repair a faulty rule.

## 6. Soft metrics

| Metric | Unit |
|---|---|
| Management miss rate | atomic responsibilities |
| Rule/input/engine miss counts | atomic responsibilities |
| Card noise rate | unique date + card |
| Timing error rate | actual surfaced responsibilities |
| Partner-prompt dependency | actual responsibilities |
| Close-loop failure | actual responsibilities |
| Master gap | actual responsibilities absent from catalog |
| Duplicate/granular count | observation rows/cards |

Phase one does not invent pass thresholds. It creates the baseline from which phase-two targets will be pre-registered.

## 7. Data handling

- real household responses remain local-only
- no real observation JSONL is committed to the public repository
- public fixtures must be synthetic and clearly marked
- sensitive document images or medical details are not required
- observed symptoms may be recorded as changes, but the engine does not diagnose

## 8. Daily operating flow

### Morning

Use `data/shadow_intake_spec_v2.json` to confirm the minimum known state. Unchanged defaults should be carried forward rather than re-entered.

### During the day

Record only meaningful changes:

- partner prompts
- calendar/daycare/official notices
- stock or household state changes
- health/safety observations
- responsibilities not represented by the engine

### Evening

Reveal the engine cards and reconcile:

1. which cards were useful
2. which cards were wholly unnecessary
3. which atomic responsibilities actually mattered
4. what was missed
5. whether a miss was caused by rule, input, or engine logic
6. whether the loop was closed
7. whether any statement exceeded stored evidence

## 9. Seven-day output

The evaluator produces:

- hard-gate status
- card noise rate
- atomic and management miss rates
- rule/input/engine miss counts
- critical miss diagnosis
- partner prompt dependency
- loop closure failures
- master gaps
- input-gap breakdown

A successful phase-one run is not automatically `READY_FOR_ACTIVE_EXPERIMENT`. It is either blocked or a completed baseline with gaps. Phase-two criteria are set only after reviewing the baseline.
