# 家事取りゲーム

育休中の家事・育児を、単なる作業消化ではなく「気づく・考える・計画する・最後まで閉じる」家庭運営のゲームとして扱うプロジェクトです。

現在は、v0.2のプロダクト思想と保存形式を維持しながら、iPhone実利用で確認されたUI摩擦を解消するv0.3 UX/UI刷新を実装しています。

## 入口

| 読む順番 | 文書 | 役割 |
|---:|---|---|
| 1 | [HANDOFF.md](HANDOFF.md) | 現在地、未解決事項、次に行う作業 |
| 2 | [docs/PRODUCT_BRIEF.md](docs/PRODUCT_BRIEF.md) | プロダクト思想と守るべき原則 |
| 3 | [docs/COLLABORATION_WORKFLOW.md](docs/COLLABORATION_WORKFLOW.md) | 実装・レビューの進め方 |
| 4 | [docs/DECISIONS.md](docs/DECISIONS.md) | 合意済みの判断と、その理由 |
| 5 | [docs/V0_3_UX_SLICE.md](docs/V0_3_UX_SLICE.md) | 現行v0.3のUX仕様・受入条件 |
| 6 | [reviews/README.md](reviews/README.md) | レビュー記録の書き方 |

AIごとの入口は [AGENTS.md](AGENTS.md) と [CLAUDE.md](CLAUDE.md) です。どちらも共有文書を正本として参照します。

## v0.3の主な変更

- 白〜暖灰 + ブルーグレー `#5F86A4`、イラストなし
- `今日 / この先 / 記録` の3タブ
- 今日の負荷を `0 / 1 / 2 / 3件` から直接選択
- コンパクトなToday一覧
- 通常項目は一覧から1タップ完了
- 状態確認項目はボトムシートで3段階状態を確認して完了
- 理由・終了条件は `判断のヒントを見る` へ格納
- 本文と下部ナビを別レイアウト行へ分離し、重なりを防止
- 朝・昼・夕方以降で候補優先順位を静的に調整
- 達成率、残件数、XP、連続日数による評価はしない

## 現在の成果物

| ファイル | 内容 |
|---|---|
| [kajitori_minimal_pictogram_compact.html](kajitori_minimal_pictogram_compact.html) | v0.3アプリのHTMLシェル |
| [kajitori_v03.css](kajitori_v03.css) | v0.3ブルーグレーUI |
| [kajitori_v03_core.js](kajitori_v03_core.js) | 保存・状態・証拠イベント等の中核ロジック |
| [kajitori_v03_actions.js](kajitori_v03_actions.js) | Today / Forecast / Detailの操作 |
| [kajitori_v03_ui.js](kajitori_v03_ui.js) | ナビ、設定、初回設定、起動 |
| [docs/V0_3_UX_SLICE.md](docs/V0_3_UX_SLICE.md) | v0.3仕様と受入条件 |
| [tests/v03_smoke.mjs](tests/v03_smoke.mjs) | Chromium / WebKitのモバイルスモークテスト |
| [.github/workflows/v03-validate.yml](.github/workflows/v03-validate.yml) | v0.3自動検証 |
| [reviews/2026-09-05-0005-chatgpt-v0-3-ux-post.md](reviews/2026-09-05-0005-chatgpt-v0-3-ux-post.md) | v0.3事後監査 |
| [index.html](index.html) | スマホURLの入口 |
| [manifest.webmanifest](manifest.webmanifest) | ホーム画面追加時のアプリ情報 |
| [sw.js](sw.js) | オフライン読み込み補助 / v3 cache |
| [.github/workflows/pages.yml](.github/workflows/pages.yml) | アプリ用ファイルだけを手動でPagesへ配信 |
| [docs/MOBILE_ACCESS.md](docs/MOBILE_ACCESS.md) | Pagesの公開範囲、ホーム画面追加、保存データの注意点 |

## 保存互換性

v0.3はデータ移行ではなくUX/UI刷新です。

- 保存キー `kajitori_stable_mvp_v2` を維持
- `v02` namespace / version 2を維持
- 旧root `tasksByDate / missedLog / retryQueue` を保持
- 既存profile、日別状態、stateFacts、evidenceEvents等を継続利用

## 検証

GitHub ActionsでJavaScript構文、配信資産、Chromium 390×844、WebKit 390×844の主要フローを検証しています。Run #9までChromium / WebKitともPassし、P0/P1の未解決Findingはありません。

物理iPhone Safariとホーム画面追加版はPages反映後の最終受入ゲートです。

## スマホから使う

公開URLは [https://kkrod899.github.io/kajitori-game/](https://kkrod899.github.io/kajitori-game/) です。iPhoneはSafariの共有メニューから「ホーム画面に追加」できます。

Pagesは手動公開です。mainの更新だけでは自動公開されないため、更新内容を確認した後に `Publish the app to GitHub Pages` workflowを実行します。

## ChatGPTのチャット側で再開する

再開時の依頼文:

> GitHubの `kkrod899/kajitori-game` を正本として参照してください。最初に `HANDOFF.md`、`docs/PRODUCT_BRIEF.md`、`docs/COLLABORATION_WORKFLOW.md`、`docs/DECISIONS.md`、`docs/V0_3_UX_SLICE.md`、`reviews/2026-09-05-0005-chatgpt-v0-3-ux-post.md` を読み、保存キー `kajitori_stable_mvp_v2` と `v02` の互換性を壊さないでください。公開URLや公開範囲を変更する場合は、実行前にユーザーへ確認してください。
