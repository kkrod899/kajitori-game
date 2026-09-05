# スマホから使うための入口

このリポジトリでは、HTMLアプリをURLから開けるようにするため、次を用意しています。

- `index.html`: リポジトリのURLを開いたときの入口
- `manifest.webmanifest`: ホーム画面追加時のアプリ名・色・起動先
- `sw.js`: 同じ端末で一度開いた後の読み込み補助
- `icons/`: ホーム画面用アイコン
- `.github/workflows/pages.yml`: GitHub Pagesを手動で公開するための設定

## 現在の公開状態（2026-09-05）

ユーザーの許可に沿って、リポジトリはPublic、GitHub PagesはGitHub Actions方式で公開済みです。

- 公開URL: [https://kkrod899.github.io/kajitori-game/](https://kkrod899.github.io/kajitori-game/)
- 現行アプリ: `家事取りゲーム v0.3`
- v0.3 Pages deployment: [Publish the app to GitHub Pages #2](https://github.com/kkrod899/kajitori-game/actions/runs/33934672855) — Success
- deployment artifact: `9959749555`
- 配信artifact内で `kajitori_v03.css`、`kajitori_v03_core.js`、`kajitori_v03_actions.js`、`kajitori_v03_ui.js`、manifest、service workerを確認済み
- app / index / manifest theme color: `#5F86A4`

v0.3配信のために一時的に`main` pushをPages triggerへ追加してdeployment #2を実行し、成功後すぐに`workflow_dispatch`のみへ戻しました。現在の正本は再び**手動公開のみ**です。

リポジトリのソース・文書・レビュー・案件状態も公開範囲です。非公開サイトが必要な場合、この方式は使わず、認証付きホスティングを選んでください。

## 重要な公開範囲

このアプリは入力内容を独自サーバーへ送らず、ブラウザのlocalStorageへ保存します。ただし、URLから配信するページとページのソースは公開範囲の影響を受けます。

この正本のPagesワークフローは自動実行ではなく、`workflow_dispatch`による手動実行です。また、配信するのはアプリ本体とPWA用ファイルだけで、文書・レビュー・状態ファイルはPages artifactへ含めません。

## iPhoneから使う

1. Safariで [https://kkrod899.github.io/kajitori-game/](https://kkrod899.github.io/kajitori-game/) を開く。
2. v0.3のブルーグレーUIが表示されることを確認する。
3. 共有メニューを開く。
4. 「ホーム画面に追加」を選ぶ。
5. ホーム画面の`家事取り`から起動する。

すでにv0.2をホーム画面へ追加している場合も、同じURL・同じ保存領域を使います。v0.3ではservice worker cache名を`kajitori-shell-v3`へ更新しているため、Safariで公開URLを一度開き直した後にホーム画面版を再起動してください。

旧画面が残る場合は、まずSafari側の公開URLを再読み込みし、その後ホーム画面版を完全に閉じて再起動します。保存データを消す必要はありません。

## 保存データについて

保存キー `kajitori_stable_mvp_v2` は変更していません。v0.3も既存の`v02` namespace / version 2を利用します。

- URL版で保存したデータは、そのURLのブラウザ内に残る
- v0.2からv0.3へのUI更新で保存キーは変わらない
- 旧root `tasksByDate / missedLog / retryQueue` は保持する
- 以前にHTMLファイルを直接開いて保存した`file://`のデータは、URL版へ自動移行しない

## v0.3の物理iPhone受入

自動検証ではChromium / WebKit 390×844ともPassしています。残る最終確認は実機だけです。

確認項目:

- 下部ナビが本文に重ならない
- 一番下まで普通にスクロールできる
- 通常項目を左のチェック1タップで完了できる
- オムツ等の状態項目でボトムシートが開き、状態選択→完了できる
- 完了した項目を再タップして戻せる
- `今日 / この先 / 記録`を切り替えられる
- ホーム画面追加版でも同じUI・保存内容になる

ここで問題が出た場合は、7〜14日実生活テストを再開せずv0.3を修正します。
