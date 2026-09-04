# 家事取りゲーム

育休中の家事・育児を、単なる作業消化ではなく「気づく・考える・計画する・最後まで閉じる」家庭運営のゲームとして扱うプロジェクトです。

現在は、状態から次の一手を選ぶv0.2 Slice 01を1ファイルで試せるHTMLモックの段階です。

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
| [kajitori_minimal_pictogram_compact.html](kajitori_minimal_pictogram_compact.html) | v0.2 Slice 01。状態主役カード、余力0〜3件、先読み、証拠イベントを含むHTMLアプリ |
| [docs/V0_2_UX_SPEC.md](docs/V0_2_UX_SPEC.md) | v0.2 UX仕様とSlice 01の受入条件・実装結果 |
| [index.html](index.html) | スマホURLの入口。既存HTMLへ安全に引き継ぐ |
| [manifest.webmanifest](manifest.webmanifest) | ホーム画面追加時のアプリ名・起動先 |
| [sw.js](sw.js) | 一度開いた後の読み込み補助 |
| [.github/workflows/pages.yml](.github/workflows/pages.yml) | アプリ用ファイルだけを手動でPagesへ配信する設定 |
| [docs/MOBILE_ACCESS.md](docs/MOBILE_ACCESS.md) | Pagesの公開範囲、ホーム画面追加、保存データの注意点 |
| [公開URL](https://kkrod899.github.io/kajitori-game/) | スマホから使う現行v0.2の入口 |

## 開発上の基本ルール

- 一度に実装担当とレビュー担当を分ける。
- レビュー中は、明示的に依頼されない限りアプリ本体を変更しない。
- チャットだけで合意を完結させず、決定事項を `docs/DECISIONS.md` に残す。
- 作業完了時は `HANDOFF.md` を更新し、次の担当が会話履歴なしでも再開できる状態にする。
- 家事の量を競わせるのではなく、家庭の認知負荷を減らす設計を優先する。

## スマホから使う

スマホ用の入口とホーム画面追加の設定は正本に含まれています。現在は [公開URL](https://kkrod899.github.io/kajitori-game/) から使えます。URLを開いたあと、iPhoneはSafariの共有メニューから「ホーム画面に追加」、Androidはブラウザメニューから「ホーム画面に追加」を選んでください。公開範囲と保存データの境界は [docs/MOBILE_ACCESS.md](docs/MOBILE_ACCESS.md) に記載しています。

## ChatGPTのチャット側で再開する

このリポジトリは公開です。ChatGPTなどから正本を参照するときは、`kkrod899/kajitori-game` の公開ファイルを読み、既存の保存形式を変更しないでください。

再開時の依頼文:

> GitHubの `kkrod899/kajitori-game` を正本として参照してください。最初に `HANDOFF.md`、`docs/PRODUCT_BRIEF.md`、`docs/COLLABORATION_WORKFLOW.md`、`docs/DECISIONS.md`、`docs/V0_2_UX_SPEC.md`、`docs/V0_2_SLICE_01.md`、`reviews/2026-08-30-0004-chatgpt-v0-2-slice-01-post.md` を読み、現行v0.2の保存形式を壊さないでください。公開URLや公開範囲を変更する場合は、実行前にユーザーへ確認してください。
