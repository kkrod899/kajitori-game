# Baseline review by Codex

| 項目 | 内容 |
|---|---|
| Reviewer | Codex |
| Date | 2026-07-22 |
| Role | Product and implementation baseline |
| Scope | 現在のHTMLモック全体 |
| Target | `kajitori_minimal_pictogram_compact.html` |
| App changes | None |

## Summary

「見えない家事を先回りする」という企画の芯は強く、在庫、予定、食事判断などを既にタスク化できています。一方、現在のゲームループは大量の固定タスク消化に偏り、家庭の認知負荷を共同で持つという目的を十分に達成できません。

## Findings

### [P1] 明日リトライが翌日に反映されない

| 項目 | 内容 |
|---|---|
| Location | `kajitori_minimal_pictogram_compact.html:1440` |
| Observation | `converted` を `true` にするだけで、`retryQueue` への追加と翌日生成処理がない |
| Impact | 画面上は追加済みでも、翌日タスクに現れない |
| Principle | P-04 |
| Recommendation | 対象日を持つリトライとして保存し、当日生成時に取り込む |
| Evidence | `retryMiss()` と `ensureTodayTasks()` のコード確認 |

### [P1] 今日のクエスト量が現実的でない

| 項目 | 内容 |
|---|---|
| Location | `kajitori_minimal_pictogram_compact.html:1214` |
| Observation | 繰り返し条件に合う全タスクを今日へ追加する |
| Impact | 2026-07-22条件では42件、推定380分となり、100%達成が心理的負担になる |
| Principle | P-04, P-05 |
| Recommendation | due候補と今日選ぶクエストを分離し、余力に応じて3〜7件へ編成する |
| Evidence | 初期データと繰り返し条件から件数・推定時間を集計 |

### [P1] アプリの指示待ちへ置き換わる危険がある

| 項目 | 内容 |
|---|---|
| Location | 現在のゲームループ全体 |
| Observation | アプリが固定タスクを提示し、利用者は完了または取り逃がしを押す構造 |
| Impact | パートナーの指示待ちがアプリの指示待ちへ変わるだけで、観察・判断・計画能力が育たない可能性がある |
| Principle | P-01, P-02, P-09 |
| Recommendation | 担当領域、先読み、判断理由、支援の段階的縮小をゲームの中心にする |
| Evidence | 投稿されたプロダクト思想と現行UI・状態遷移の比較 |

### [P1] 月齢・発達に応じてタスクが切り替わらない

| 項目 | 内容 |
|---|---|
| Location | 初期データと `isDue()` |
| Observation | 新生児タスクに開始・終了月齢や発達トリガーがない |
| Impact | 子どもの成長後も新生児向けタスクが毎日出続ける |
| Principle | P-06, P-08 |
| Recommendation | 月齢範囲、発達トリガー、家庭設定、出典情報をタスクテンプレートへ追加する |
| Evidence | 50件の初期タスクスキーマ確認 |

### [P2] 状態が完了・取り逃がし・未完了に限定される

| 項目 | 内容 |
|---|---|
| Location | タスク状態管理と操作ボタン |
| Observation | Undo、保留、不要、家族が対応済み、共同完了がない |
| Impact | 現実の分担を正しく記録できず、取り逃がしが過度に失敗扱いになる |
| Principle | P-04, P-07 |
| Recommendation | 現実の理由を表現できる状態と、短時間のUndoを追加する |
| Evidence | `taskCard()`、`completeTask()`、`missTask()` の確認 |

### [P2] 保存失敗が利用者へ伝わらない

| 項目 | 内容 |
|---|---|
| Location | `kajitori_minimal_pictogram_compact.html:1208` |
| Observation | localStorage例外を握り潰し、呼び出し側は成功したように表示する |
| Impact | 完了記録が再読み込み後に失われる可能性がある |
| Principle | P-03 |
| Recommendation | 保存結果を返し、失敗時は状態を確定せず利用者へ通知する |
| Evidence | `saveState()` の例外処理確認 |

### [P2] 片手操作と可読性が不足している

| 項目 | 内容 |
|---|---|
| Location | コンパクト表示CSS |
| Observation | 9〜10pxの文字と小さな操作領域が多い |
| Impact | 抱っこ中、疲労時、屋外で読みづらく誤操作しやすい |
| Principle | P-05 |
| Recommendation | 主要操作を44px程度へ広げ、本文を最低12〜14px程度で再評価する |
| Evidence | CSS値の確認。実機視覚テストは未実施 |

## Verified strengths

- 8カテゴリと50タスクが構造化されている。
- タスクには推定時間、XP、優先度、説明、完了条件が含まれている。
- 在庫、予定、食事判断など、見えない家事を既に扱っている。
- HTML単体で試せるため、初期仮説検証の変更コストが低い。

## Claudeへの初回レビュー依頼

トークン節約のため、この文書をClaudeへ全文読ませません。Claudeは `reviews/CLAUDE_REVIEW_PACKET.md` の範囲と出力契約に従ってください。
