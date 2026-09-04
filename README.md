# 家事取りゲーム

育休中の家事・育児を、単なる作業消化ではなく「気づく・考える・計画する・最後まで閉じる」家庭運営のゲームとして扱うプロジェクトです。

現在は、スマートフォン風UIを1ファイルで試せるHTMLモックの段階です。

## 入口

| 読む順番 | 文書 | 役割 |
|---:|---|---|
| 1 | [HANDOFF.md](HANDOFF.md) | 現在地、未解決事項、次に行う作業 |
| 2 | [docs/PRODUCT_BRIEF.md](docs/PRODUCT_BRIEF.md) | プロダクト思想と守るべき原則 |
| 3 | [docs/COLLABORATION_WORKFLOW.md](docs/COLLABORATION_WORKFLOW.md) | Claude・Codex間の相互レビュー手順 |
| 4 | [docs/DECISIONS.md](docs/DECISIONS.md) | 合意済みの判断と、その理由 |
| 5 | [reviews/README.md](reviews/README.md) | レビュー記録の書き方 |

AIごとの入口は [AGENTS.md](AGENTS.md) と [CLAUDE.md](CLAUDE.md) です。どちらも、上記の共有文書を正本として参照します。

## 現在の成果物

| ファイル | 内容 |
|---|---|
| [kajitori_minimal_pictogram_compact.html](kajitori_minimal_pictogram_compact.html) | 50件の初期タスク、XP、レベル、取り逃がしログを含むHTMLモック |
| [docs/V0_2_UX_SPEC.md](docs/V0_2_UX_SPEC.md) | 合意済みの3点とClaude第2レビューを反映したv0.2 UX仕様 |
| [index.html](index.html) | スマホURLの入口。既存HTMLへ安全に引き継ぐ |
| [docs/MOBILE_ACCESS.md](docs/MOBILE_ACCESS.md) | Pagesの公開範囲、ホーム画面追加、保存データの注意点 |

## 開発上の基本ルール

- 一度に実装担当とレビュー担当を分ける。
- レビュー中は、明示的に依頼されない限りアプリ本体を変更しない。
- チャットだけで合意を完結させず、決定事項を `docs/DECISIONS.md` に残す。
- 作業完了時は `HANDOFF.md` を更新し、次の担当が会話履歴なしでも再開できる状態にする。
- 家事の量を競わせるのではなく、家庭の認知負荷を減らす設計を優先する。

## スマホから使う

スマホ用の入口とホーム画面追加の設定は正本に含まれています。GitHub Pagesは自動公開ではなく、公開範囲を確認してから一度だけ手動実行する設計です。個人アカウントの非公開リポジトリでもサイトが非公開アプリになるとは限らないため、先に [docs/MOBILE_ACCESS.md](docs/MOBILE_ACCESS.md) を確認してください。

## ChatGPTのチャット側で再開する

このリポジトリは非公開のため、ChatGPTの「設定 → アプリ → GitHub」で `kkrod899/kajitori-game` へのアクセスを許可してから使います。新しく許可したリポジトリが表示されるまで数分かかることがあります。

再開時の依頼文:

> GitHubの `kkrod899/kajitori-game` を正本として参照してください。最初に `HANDOFF.md`、`docs/PRODUCT_BRIEF.md`、`docs/COLLABORATION_WORKFLOW.md`、`docs/DECISIONS.md` を読み、次に `reviews/CLAUDE_REVIEW_PACKET_V0_2_R2.md` の契約どおり事後レビューだけを行ってください。今回はアプリ本体を変更しないでください。
