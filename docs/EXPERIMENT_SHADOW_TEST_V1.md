# EXPERIMENT SHADOW TEST v1

Date: 2026-09-05  
Status: Pre-registered protocol / app-independent  
Branch: `experiment/production-scope-v1`

## 1. 目的

PWAへ全面接続する前に、家庭運営エンジンが実生活で本当に役立つかを**shadow mode**で検証する。

Shadow modeでは、候補生成エンジンは動かすが、利用者はその提案に依存して生活しない。1日の終わりに「実際に必要だったこと」と「エンジンが出すはずだったこと」を照合する。

これにより、UIの使いやすさではなく以下を測る。

- 見落とし
- 不要な提案
- タイミングのズレ
- パートナーから言われないと気づけなかった項目
- 着手したが最後まで閉じなかったループ
- マスターに存在しない家庭運営
- 証拠より強い成果表現

## 2. このフェーズでアプリに依存しない

特に健康・安全・期限項目について、shadow test中はアプリ候補を「正解」として扱わない。

普段どおり、家庭の判断、園・自治体・医療機関等の案内、製品説明書、公的情報を優先する。

健康・安全の異常や相談が必要な状況で、shadow engineの判定を待たない。

## 3. 7日間の基本フロー

### 朝 / 日中

1. その日の既知状態・予定・在庫等をengine入力へ反映する
2. engineは`今見る / 今日の候補 / ルーティン / レビュー`を生成する
3. **生成結果は原則として生活判断に使わず保存だけする**
4. 利用者は通常どおり家庭運営する

### その場で記録するもの

- パートナーから自然に指摘・依頼されたこと
- 自分で途中で気づいたこと
- 園・カレンダー・郵便・在庫・環境変化から発生したこと
- engine masterに無いと感じたこと
- 期限・安全上、早く気づく必要があったこと

パートナーへ追加の監査作業を依頼する必要はない。自然に発生した指摘だけ記録する。

### 夜

engine生成結果を開示し、その日に実際に必要だったことと1件ずつ照合する。

各項目を以下へ分類する。

- 必要で、適切なタイミングで出ていた
- 必要だったが出なかった
- 出ていたが不要だった
- 必要だったが早すぎた / 遅すぎた
- 出た内容は正しいが粒度が細かすぎた / 重複した
- マスター自体に無かった
- 着手したが責任ループを閉じられなかった

## 4. 観測単位

1行 = 「その日に意味のある家庭運営責任または提案」1件。

`data/shadow_observation_schema_v1.json`に準拠する。

マスターに存在しない実際の必要事項も必ず記録可能にする。その場合は`responsibility_id=null`とし、`actual_label`へ内容を書く。

## 5. 主要指標

### Hard gates

以下は率ではなく**1件でも発生したらactive relianceへ進まない**。

- `critical_miss_count`
  - health/safetyまたはhard deadlineで実際に必要だったのに出なかった
- `hard_deadline_miss_count`
  - hard deadlineをengineが見落とした
- `evidence_overclaim_count`
  - 保存した事実より強い「できた / 防げた」等をengineが主張した

### Soft metrics

| Metric | 意味 |
|---|---|
| `management_miss_rate` | 実際に必要だったmanagement責任のうち出なかった割合 |
| `noise_rate` | 出した提案のうち実際には不要だった割合 |
| `timing_error_rate` | 必要かつ表示された項目のうち早すぎ/遅すぎだった割合 |
| `partner_prompt_dependency_count` | パートナーの自然な指摘で初めて認識した必要事項数 |
| `close_loop_failure_count` | 必要だったが最後まで閉じられなかった責任数 |
| `master_gap_count` | 実際には必要だったが293 masterに存在しなかった数 |
| `duplicate_or_granular_count` | 重複または細かすぎる表示数 |

## 6. 閾値を先に捏造しない

第1期7日間では、`noise_rate 10%以下`等の arbitraryな合格線を置かない。

理由:

- 現時点で実生活baselineがない
- 家庭ごとに必要件数が大きく変わる
- 数値目標に合わせて提案を削ると、元の「3件問題」を再発させる

第1期はhard gateとbaseline取得を目的とする。

第1期データを見て、第2期の改善目標を事前登録する。

## 7. 判定

### `BLOCKED`

以下のどれかが1件以上。

- critical miss
- hard deadline miss
- evidence overclaim

### `BASELINE_COMPLETE_WITH_GAPS`

hard gateは0だが、master gap / miss / noise / timing error等があり、改善対象を特定できた状態。

### `READY_FOR_ACTIVE_EXPERIMENT`

第1期では原則この判定を自動で出さない。

第1期baseline後に第2期の受入基準を決め、active experimentで確認する。

## 8. 重要な比較

shadow testでは単に「engineが何件当てたか」を見ない。

最重要の問いは:

> これを使えば、家庭のことをパートナーが指示する前に自分で見つけ、判断し、最後まで閉じられるか。

そのため`partner_prompt_dependency_count`と`close_loop_failure_count`を独立して持つ。

## 9. 実証順序

1. 293 masterのitem-level applicabilityを改善
2. health/safety 42項目のreview blockerを解消
3. shadow mode 7日
4. hard gate / baseline metricsを集計
5. miss / noise / timing / master gapを修正
6. 第2期の数値目標を事前登録
7. その後にPWAへproduction-scope engineを接続

PWAのUI改善が先行しても、この順序は飛ばさない。
