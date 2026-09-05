# RESPONSIBILITY METADATA SCHEMA v1

Date: 2026-09-05  
Status: Experiment contract / production-scope metadata

## Purpose

`RESPONSIBILITY_MASTER_V1.md` の293項目を、単なるチェックリストではなく「いつ出すか・誰に出すか・どこまで閉じればよいか」を判断できる責任モデルへ変換する。

本フェーズではアプリUIを先に作らない。メタデータと実証シミュレーションを先に成立させる。

## Canonical fields

| Field | Meaning |
|---|---|
| `id` | Master item ID |
| `label` | Human-readable responsibility / routine |
| `type` | `M / R / S / C` combination from master |
| `group` | Master prefix group |
| `domain` | Operational household domain |
| `applicability` | Conditions required for the item to belong to a household |
| `requires_household_config` | Whether household/local settings are required |
| `household_config_fields` | Specific configuration needed before surfacing |
| `trigger_type` | What makes the item relevant now/today |
| `cadence` | Review/execution recurrence |
| `priority_class` | Priority semantics; not a gamification score |
| `surface_rule` | Which layer can show the item |
| `close_condition` | What must be true before the loop is closed |
| `state_inputs` | Facts required to decide |
| `evidence_rule` | What may be claimed from recorded evidence |
| `source_class` | Evidence/source class |
| `source_ids` | Official/household source IDs |
| `default_visibility` | Hidden/collapsed behavior when not due |
| `manual_review_required` | Mandatory human review for health/safety |
| `metadata_maturity` | Current refinement stage |

## Trigger types

- `routine`: every-occurrence execution such as feeding, diaper changing, transport.
- `inventory`: remaining amount / coverage threshold.
- `schedule`: deadline, booking, calendar or event horizon.
- `handoff`: responsibility transition between adults.
- `lifecycle`: growth, season, size-out, equipment change.
- `safety`: hazard/context based.
- `health_state`: observed symptom/development change; no diagnosis.
- `maintenance`: periodic equipment/cleanliness maintenance.
- `state`: state observation and decision.
- `task_state`: general household loop that becomes relevant from state.

## Surface layers

The experiment must not impose a fixed number of tasks.

1. `今見る`
   - safety/health concern
   - deadline within configured horizon
   - essential inventory below threshold
   - state deterioration / blocked household loop

2. `今日の候補`
   - relevant today but not necessarily immediate
   - variable count

3. `ルーティン`
   - repeated execution
   - kept separate so repeated care does not flood `今日の候補`

4. `レビュー`
   - weekly/monthly/seasonal maintenance and lifecycle checks

## Evidence boundary

A record must never claim more than the stored evidence supports.

Examples:

- inventory `少ない` + purchase memo → may claim `少ない段階で気づき、購入アクションを作った`
- inventory `少ない` only → may not claim `補充できた`
- safety check + no hazard → may claim `確認時点で危険要因を記録しなかった`; may not claim `事故を防いだ`
- symptom observation → may claim observed state and consultation action; may not generate a medical diagnosis

## Health / safety gate

Every item whose master type contains `S` must satisfy all of the following before production use:

- at least one `source_id`
- official primary or official guideline source
- `manual_review_required=true`
- no unsupported diagnostic / prevention claim
- age or context applicability explicitly reviewed

The metadata builder fails if an `S` item has no source.

## Local / household configuration gate

Every item whose master type contains `C` must have a household/local configuration dependency. Examples:

- daycare rules
- municipality waste calendar
- feeding policy
- bicycle/car usage
- local vaccination/checkup workflow

A `C` item should not become `今見る` from a guessed default.

## Maturity

`generated_v1` means:

- all 293 items have machine-readable metadata
- generic rule generation and source mapping are complete
- high-impact item-by-item manual review is still required

The experiment must not represent `generated_v1` as fully clinically/operationally validated.

## Build validation

`tools/build_responsibility_metadata.py` must verify:

- exactly 293 unique master items
- exactly 293 metadata rows
- every `S` item has source coverage
- every `C` item has household config fields
- no duplicate IDs
- metadata output is deterministic
