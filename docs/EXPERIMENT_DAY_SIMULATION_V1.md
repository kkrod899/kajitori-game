# EXPERIMENT DAY SIMULATION v1 — Result checkpoint

Date: 2026-09-05  
Branch: `experiment/production-scope-v1`

## 1. 結論

固定の「今日3件」は実証モデルから廃止した。

293項目の責任マスターに対し、架空家庭・架空状態を使って `今見る / 今日の候補 / ルーティン / レビュー` を決定論的に生成したところ、同じ家庭でも日によって件数が大きく変動した。

| シナリオ | 今見る | 今日の候補 | ルーティン | レビュー | 表示対象合計 |
|---|---:|---:|---:|---:|---:|
| 通常の平日 | 2 | 18 | 19 | 5 | 44 |
| 高負荷の平日 | 7 | 27 | 19 | 6 | 59 |
| 低負荷の週末・回復日 | 0 | 11 | 16 | 4 | 31 |

この件数を「正解」「目標件数」とは扱わない。確認できたのは、UI都合の固定上限ではなく家庭状態から表示量を変えられることだけ。

## 2. `今見る`の例

### 通常の平日 — 2件

- `DAYCARE-008` 園の提出書類・締切 — 締切まで6時間
- `INF-FEED-005` ミルク在庫 — 次の通常購入機会まで持たない想定

### 高負荷の平日 — 7件

- `CHD-MED-003` 予防接種当日の準備
- `PLAN-005` 病院予約時刻の共有
- `DAYCARE-008` 園の提出締切
- `INF-FEED-005` ミルク在庫不足
- `INF-DIAP-002` オムツ在庫不足
- `SAFE-018` 暑熱リスクのある外出
- `FAM-004` 夫婦双方の疲労が強く計画再調整が必要

### 低負荷の週末 — 0件

緊急・期限・安全状態の変化を与えていないため、`今見る`は0件となった。

「毎日必ず3件」のような埋め草は行わない。

## 3. ルーティンを分ける理由

授乳、オムツ替え、寝かしつけ、食器洗い、送迎などの反復実行まで`今日の候補`へ混ぜると、家庭運営上の「気づく・判断する・先回りする」が埋もれる。

そのため次を分離する。

- `ルーティン`: その日何度も起きる実行
- `今日の候補`: 状態把握、判断、計画、補充、締切管理、完結ループ

実証時には両方を観測するが、同じ優先リストへ積まない。

## 4. applicability 289 / 293 の解釈

架空家庭プロフィールへ現時点の粗い条件を当てると、293項目中289項目が「長期的にはこの家庭に関係し得る」と判定された。

この98.63%という比率だけを失敗とは扱わない。掃除、洗濯、食事、在庫、予定、行政、災害準備等は一般家庭に長期的に存在し得るため、structural applicabilityは高くなり得る。

一方で、現metadataがgroup-level条件に依存しすぎていることは未解決。

production-scopeでは以下を分ける。

1. `structural applicability` — その家庭に責任が存在し得るか
2. `activation eligibility` — 今・今日・今週に出す根拠があるか

詳細は`docs/APPLICABILITY_REVIEW_V1.md`を正本とする。

現在入っている明示的な除外例:

- 搾乳母乳管理 — 搾乳母乳を使わない設定なら除外
- 搾乳器管理 — 搾乳器を使わない設定なら除外
- 自転車幼児座席安全 — 利用しない家庭では除外
- 離乳食 — 離乳開始前なら除外

今後は年齢・発達段階・設備・園/自治体制度・食事段階・季節・最近の状態等をitem-levelで詰める。

## 5. health / safety gate

42項目をmachine-readable reviewへ載せ、sourceとの整合をCIで確認するところまで進めた。

現在:

- `PASS_DIRECT`: 22
- `PASS_WITH_BOUNDARY`: 19
- `REWRITE_OR_SPLIT`: 1

唯一のblockerは`SAFE-018`。

`SAFE-018`は「暑さ・寒さ」を1項目にまとめているが、現時点の直接sourceは暑熱側を主に支えるため、現形のままproduction recommendationへ昇格させない。

詳細は`docs/HEALTH_SAFETY_REVIEW_V1.md`と`data/health_safety_review_v1.json`を参照。

## 6. shadow testまで準備したもの

synthetic simulationだけでは実生活で使えることを証明できないため、次の実証契約を追加した。

- `docs/EXPERIMENT_SHADOW_TEST_V1.md`
- `data/shadow_observation_schema_v1.json`
- `tools/evaluate_shadow_test.py`
- `tests/test_shadow_evaluator.py`

測るもの:

- management miss
- noise
- timing error
- partner prompt dependency
- close-loop failure
- master gap
- evidence overclaim

health/safetyまたはhard deadlineの見落とし、evidence overclaimは1件でもactive relianceへのblockerとする。

## 7. 自動検証

CIでは以下を確認する。

- Master 293 unique items
- Metadata 293 rows
- 健康・安全42項目にsource coverage
- health/safety manual review 42/42 coverage
- 家庭設定依存37項目にconfig dependency
- 固定3件 / daily limit metadataなし
- 3シナリオの可変表示
- ルーティンの別ストリーム化
- 重複表示なし
- health/safety表示にsource IDあり
- shadow evaluatorのhard gate / soft metric計算

一度、health/safety status集計の不一致をCIが検出した。`CHD-MED-009`は#8000の実施時間等が地域依存であるため`PASS_WITH_BOUNDARY`へ修正し、machine-readable reviewと文書を一致させた。

## 8. この段階で証明していないこと

- 293項目で家庭運営を十分網羅できていること
- 293項目に過剰・重複がないこと
- item-level activation eligibilityが最終品質であること
- `今見る`の優先順位が実生活の人間判断と一致すること
- health/safety 42項目が臨床的に検証されたこと
- 実生活でパートナーからの指示依存が減ること

次工程はPWA実装ではない。item-level activation refinement → `SAFE-018`解消 → 7日shadow baselineの順で進める。
