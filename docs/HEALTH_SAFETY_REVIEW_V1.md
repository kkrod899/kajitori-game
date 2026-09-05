# HEALTH / SAFETY REVIEW v1

Date: 2026-09-05  
Branch: `experiment/production-scope-v1`  
Status: Manual integrity pass 1 / **not clinical validation**

## Purpose

293項目中、master typeに`S`を含む42項目を別ゲートで確認する。

このレビューは「医療判断を正しいと認定する」ものではない。確認するのは次の4点。

1. 項目自体を実証マスターに置く根拠があるか
2. sourceが項目の内容を直接または境界付きで支えているか
3. アプリが断定してよい範囲を越えていないか
4. 家庭・地域・個人状態が必要な項目を固定ルール化していないか

## Status definitions

- `PASS_DIRECT`: 公的sourceが責任項目を直接支える。個別診断はしない。
- `PASS_WITH_BOUNDARY`: 項目は妥当だが、地域差・個別状態・証拠境界を明示して使う。
- `NEEDS_DIRECT_SOURCE`: 現sourceが広すぎる。より直接的な一次情報が必要。
- `REWRITE_OR_SPLIT`: 1項目に異なる根拠・条件が混在しており、そのまま本番使用しない。

## Review table

| # | ID | 内容 | Status | Source | Boundary / next action |
|---:|---|---|---|---|---|
| 1 | `INF-DIAP-007` | 尿・便のいつもとの差に気づく | PASS_WITH_BOUNDARY | MCH | 観察事実のみ。症状から診断しない |
| 2 | `INF-SLEEP-004` | 安全な寝床環境を確認 | PASS_DIRECT | SLEEP, ACCIDENT | 睡眠環境の確認項目として使用可 |
| 3 | `INF-SLEEP-005` | 顔周辺の窒息要因を確認 | PASS_DIRECT | SLEEP, ACCIDENT | 「事故を防いだ」とは記録しない |
| 4 | `INF-SLEEP-006` | 寝姿勢・寝具を確認 | PASS_DIRECT | SLEEP, ACCIDENT | 個別の睡眠診断はしない |
| 5 | `CHD-MED-001` | 次の予防接種時期を把握 | PASS_WITH_BOUNDARY | VAX | 年齢だけでなく接種歴・自治体運用を入力にする |
| 6 | `CHD-MED-002` | 予防接種を予約 | PASS_WITH_BOUNDARY | VAX | 予約可否・医療機関運用は外部状態 |
| 7 | `CHD-MED-003` | 接種当日の準備・状態確認 | PASS_WITH_BOUNDARY | VAX | 接種可否をアプリが診断しない |
| 8 | `CHD-MED-004` | 接種後の観察と次の予定 | PASS_WITH_BOUNDARY | VAX | 異常判定を自動化しない |
| 9 | `CHD-MED-005` | 乳幼児健診時期を把握 | PASS_WITH_BOUNDARY | CHECKUP | 自治体差があるためlocal config必須 |
| 10 | `CHD-MED-006` | 健診予約・書類を閉じる | PASS_WITH_BOUNDARY | CHECKUP | 実施方法・予約要否は地域依存 |
| 11 | `CHD-MED-008` | 発熱・咳・嘔吐等の変化を観察 | PASS_WITH_BOUNDARY | MCH, CHILD-8000 | 観察＋相談導線。診断・受診要否を確定しない |
| 12 | `CHD-MED-009` | 受診先・休日夜間相談先を把握 | PASS_DIRECT | CHILD-8000, MCH | #8000の利用時間等は地域確認が必要 |
| 13 | `CHD-MED-014` | 発達・動き・食事等の気がかりを記録 | PASS_WITH_BOUNDARY | MCH | 発達診断をしない。相談材料の記録まで |
| 14 | `SAFE-001` | 睡眠中の窒息リスクを確認 | PASS_DIRECT | SLEEP, ACCIDENT | 状態確認と具体的除去行動のみ記録 |
| 15 | `SAFE-002` | 小物・誤飲物を確認 | PASS_DIRECT | ACCIDENT | 年齢・到達範囲の変化で再評価 |
| 16 | `SAFE-003` | ボタン電池・磁石等を管理 | PASS_DIRECT | ACCIDENT | 保管状態の確認まで |
| 17 | `SAFE-004` | 薬・洗剤等を安全に保管 | PASS_DIRECT | ACCIDENT | 製品別注意は別sourceが必要な場合あり |
| 18 | `SAFE-005` | 家具・ベッド・ソファ等の転落リスク | PASS_DIRECT | ACCIDENT | 成長で再評価 |
| 19 | `SAFE-006` | ベビーゲート・柵等を確認 | PASS_DIRECT | ACCIDENT | 製品固有の取付判断は説明書を優先 |
| 20 | `SAFE-007` | コンセント・コード・ひも類を確認 | PASS_DIRECT | ACCIDENT | 家の設備状態を入力にする |
| 21 | `SAFE-008` | やけど要因を確認 | PASS_DIRECT | ACCIDENT | 熱源の個別状態で出す |
| 22 | `SAFE-009` | 浴槽・水まわりの事故要因を確認 | PASS_DIRECT | ACCIDENT | 状態確認のみ。事故防止実績は断定しない |
| 23 | `SAFE-010` | 食品の窒息リスクを確認 | PASS_WITH_BOUNDARY | ACCIDENT, FEED | 年齢・食品・食べ方に依存。固定判定にしない |
| 24 | `SAFE-011` | チャイルドシート安全確認 | PASS_DIRECT | CHILDSEAT | 車利用家庭のみ。取付・着座を状態として持つ |
| 25 | `SAFE-012` | ベビーカーのベルト・ブレーキ等 | PASS_WITH_BOUNDARY | ACCIDENT | 製品固有仕様は取扱説明書を追加する |
| 26 | `SAFE-013` | 自転車幼児座席・ヘルメット | PASS_DIRECT | BICYCLE | 利用家庭のみ |
| 27 | `SAFE-014` | 階段・道路・駐車場等の移動安全 | PASS_WITH_BOUNDARY | ACCIDENT | 文脈依存。常時警告にはしない |
| 28 | `SAFE-015` | 救急用品の場所・不足を把握 | PASS_WITH_BOUNDARY | ACCIDENT | 「救急用品があれば安全」とは断定しない |
| 29 | `SAFE-016` | 緊急連絡先・休日夜間相談先 | PASS_DIRECT | CHILD-8000, ACCIDENT | 地域別相談先・時間を設定する |
| 30 | `SAFE-017` | 成長で新たに届く危険を再確認 | PASS_WITH_BOUNDARY | ACCIDENT | 発達段階を自動診断せず、環境変化トリガーとして使う |
| 31 | `SAFE-018` | 暑さ・寒さの外出リスク | **REWRITE_OR_SPLIT** | HEAT, ACCIDENT | 現sourceは暑熱を直接支えるが寒冷側が不足。現形では本番使用不可 |
| 32 | `FOOD-016` | アレルギー・食事制約を家族で共有 | PASS_WITH_BOUNDARY | FEED, MCH | 個別医学判断を生成しない。既知情報の共有のみ |
| 33 | `EMG-001` | 避難場所・経路を把握 | PASS_DIRECT | DISASTER | 地域ハザードは別途local configが望ましい |
| 34 | `EMG-002` | 飲料水の備蓄・期限を管理 | PASS_DIRECT | DISASTER | 備蓄量は家庭人数等へ合わせる |
| 35 | `EMG-003` | 非常食の備蓄・期限を管理 | PASS_DIRECT | DISASTER | 乳幼児食等は家庭条件で追加 |
| 36 | `EMG-004` | ミルク・オムツ等の乳児備蓄 | PASS_DIRECT | DISASTER | 乳児家庭のみ |
| 37 | `EMG-005` | 電池・照明・充電手段 | PASS_DIRECT | DISASTER | 家庭設備に応じる |
| 38 | `EMG-006` | 救急用品の備蓄・期限 | PASS_WITH_BOUNDARY | DISASTER | 医療処置の代替にはしない |
| 39 | `EMG-007` | 緊急時の家族連絡方法 | PASS_DIRECT | DISASTER | 手段の実在確認を状態として持つ |
| 40 | `EMG-008` | 母子手帳・保険情報等の持出し準備 | PASS_WITH_BOUNDARY | DISASTER, MCH | 個人情報の保存方法はアプリ化時に別設計 |
| 41 | `EMG-009` | 台風・災害前の家庭準備 | PASS_WITH_BOUNDARY | DISASTER | 地域・気象状態が外部入力として必要 |
| 42 | `EMG-010` | 住宅用火災警報器等の作動・維持 | PASS_DIRECT | FIRE, DISASTER | 消防庁sourceを直接紐付ける |

## Pass 1 result

| Status | Count |
|---|---:|
| PASS_DIRECT | 22 |
| PASS_WITH_BOUNDARY | 19 |
| NEEDS_DIRECT_SOURCE | 0 |
| REWRITE_OR_SPLIT | 1 |
| Total | 42 |

### Blocking finding

`SAFE-018`は現状のままproduction-scopeへ昇格させない。

「暑さ」と「寒さ」は別の環境条件・根拠・表示タイミングを持つため、次のitem-level passで少なくとも以下のどちらかを行う。

- `SAFE-018A` 暑熱リスクへ限定し、`SRC-HEAT-001`を直接適用
- 寒冷側を別項目へ分離し、直接sourceを追加してから有効化

## Evidence / claim rules confirmed

全42項目について以下を維持する。

- `state_snapshot`等、実際に保存した事実を超えて成果を断定しない
- `事故を防いだ`、`病気を見つけた`、`受診不要`等を自動生成しない
- health/safety状態を元に独自診断しない
- sourceがあっても地域・個人差を消さない
- `PASS_WITH_BOUNDARY`は境界条件を実装できるまでactive recommendationへ昇格させない

## Next gate

1. `SAFE-018`をsplit/rewrite
2. `PASS_WITH_BOUNDARY` 19項目へ必要なage/context/local-config条件をitem-level metadata化
3. 製品依存の`SAFE-006`・`SAFE-012`等は、実際に使う製品が確定した時に取扱説明書を追加
4. 42項目のmetadataとこの表が一致する自動監査を追加

この4点が終わるまで、健康・安全領域をPWAの自動提案へ全面接続しない。
