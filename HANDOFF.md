# Handoff

最終更新: 2026-08-30 / Codex

## 現在地

| 項目 | 状態 |
|---|---|
| プロダクト | 家事取りゲーム HTMLモック |
| 実装 | `kajitori_minimal_pictogram_compact.html` 1ファイル |
| 初期データ | 8カテゴリ、50タスク |
| 保存 | ブラウザのlocalStorage |
| Git | 非公開リポジトリ `kkrod899/kajitori-game` の `main` へ初回push済み |
| 共有思想 | `docs/PRODUCT_BRIEF.md` に整理済み |
| 相互レビュー | Claude・Codex用の共通手順を作成済み |
| Claude省トークン化 | 専用レビュー・パケットを作成済み |
| Claude初回レビュー | `reviews/2026-07-22-0001-claude-product-ux.md` 完了、Codex応答追記済み |
| ユーザー判断 | D-009〜D-011をAcceptedとして確定 |
| v0.2 UX仕様 | `docs/V0_2_UX_SPEC.md` を承認済み二層コンセプトへ改訂 |
| Claude第2レビュー | `reviews/2026-07-22-0002-claude-v0-2-ux.md` 完了、Codex応答追記済み |
| 第2レビュー対応 | 5 Findingsと追加提案をすべてAccepted。P0表記1件は定義上P1へ補正しつつ実装ブロッカーとして解消 |
| Claude UI案 | `prototypes/claude_v0_2_ui_concept.html` 作成済み。二層コンセプト反映前の案として今回は未変更 |
| 二層コンセプト | 状態主役の判断層と、見えない仕事の目撃者となる尊厳層をユーザー承認済み |
| 新規Decision | D-016〜D-018をAccepted、名称変更のD-019をProposedで追記 |
| Claude事後レビュー | `reviews/CLAUDE_REVIEW_PACKET_V0_2_R2.md` を作成。レビュー実行待ち |
| 本体変更 | 今回は未実施 |

## GitHub・ChatGPT共有

| 項目 | 状態 |
|---|---|
| GitHub | `https://github.com/kkrod899/kajitori-game`（Private） |
| ローカル | `main` が `origin/main` を追跡 |
| 機密情報チェック | 代表的なトークン・秘密鍵・APIキー形式の一致なし |
| ChatGPTのGitHubアクセス | ChatGPT Codex Connectorへ個別許可済み。リポジトリ検索と`HANDOFF.md`の読み取りを確認済み |

ChatGPT側で再開するときは、接続済みのGitHub Appからこのリポジトリを参照し、次の順で正本を読む。

1. `HANDOFF.md`
2. `docs/PRODUCT_BRIEF.md`
3. `docs/COLLABORATION_WORKFLOW.md`
4. `docs/DECISIONS.md`
5. `reviews/CLAUDE_REVIEW_PACKET_V0_2_R2.md`

アプリ本体の変更はまだ始めず、最初にR2事後レビューを完了する。

## 確認済みの主な問題

| Severity | 問題 | 状態 |
|---|---|---|
| P1 | 「明日リトライ」が表示だけで、翌日タスクへ追加されない | Open |
| P1 | 条件に合う全タスクを今日へ投入し、例として42件・380分になる | Open |
| P1 | アプリの指示を消化するだけでは、認知負荷を担う能力が育たない | Open |
| P1 | 新生児タスクが月齢・発達に応じて切り替わらない | Open |
| P2 | 完了Undo、保留、不要、もう済んでいた等の状態がない | Open |
| P2 | localStorage保存失敗が利用者へ伝わらない | Open |
| P2 | 小さい文字・ボタンが多く、片手操作への配慮が不足している | Open |

詳細は `reviews/0000-baseline-codex.md` を参照してください。

## 次の推奨作業

ChatGPTの新しいチャットで、二層コンセプト反映後の文書を事後レビューする。アプリ本体と既存プロトタイプはまだ変更しない。

Claudeへ渡す文面:

> `reviews/CLAUDE_REVIEW_PACKET_V0_2_R2.md` に従い、v0.2二層コンセプト改訂を事後レビューしてください。

期待する成果物は`reviews/2026-07-23-0003-claude-v0-2-r2.md`です。受領後、Codexが各FindingへAccepted / Rejected / Deferredで応答し、実装前ブロッカーがない状態にします。

その後に推奨する最初のSlice:

| 対象 | 内容 |
|---|---|
| 今日画面 | 余力0〜3件、状態事実を最上位にしたカード、利用者が選ぶ現在の一手、守る日0件 |
| 操作 | 状態3段階、任意の1日1問、完了・あとで・今日は見送る・もう済んでいた、Undo |
| 記録 | 因果の確認できる「この家で起きなかった困りごと」、自分で気づけたこと |
| 状態 | 旧localStorageを壊さない移行、翌日へ残す状態、表示根拠を判定できる記録範囲 |
| 今回の非対象 | 担当領域の工程別詳細、成長の個別集計・能力バッジ、ゲーム成長表現の再設計 |

「明日リトライ」の既存P1は、旧処理へ場当たり的に追加せず、このSliceの`あとで`・翌日状態へ統合して直す。

## 未決定事項

| 論点 | 選択肢例 |
|---|---|
| プロダクト名 | 現行名を維持 / 「見えない半分」系へ変更（D-019 Proposed） |
| 対象期間 | 新生児期中心 / 0〜1歳 / 復職後まで |
| 初期提供形態 | ローカルWebアプリ / PWA / iOS・Android |
| 家族共有 | 初期はなし / 同一端末 / アカウント同期 |
| ゲーム成長表現 | 能力・担当領域のバッジ / マップ / 非数値レベル |

名称を含め、これらはv0.2の核を検証した後でも判断できます。今回の文書改訂や事後レビューのブロッカーにはしません。
