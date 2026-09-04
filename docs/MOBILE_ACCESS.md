# スマホから使うための入口

このリポジトリでは、既存のHTMLアプリをURLから開けるようにするため、次を用意しています。

- `index.html`: リポジトリのURLを開いたときの入口
- `manifest.webmanifest`: ホーム画面追加時のアプリ名・色・起動先
- `sw.js`: 同じ端末で一度開いた後の読み込み補助
- `icons/`: ホーム画面用アイコン
- `.github/workflows/pages.yml`: GitHub Pagesを手動で公開するための設定

## 重要な公開範囲

このアプリは入力内容をサーバーへ送らず、ブラウザのlocalStorageへ保存します。ただし、URLから配信するページとページのソースは公開範囲の影響を受けます。

GitHub公式の利用条件では、非公開リポジトリからのPages利用はGitHub Proなどの対象プランが必要です。また、リポジトリが非公開でもPagesサイトは公開になる場合があり、非公開サイトのアクセス制御は組織向けEnterprise Cloudの機能です。公開範囲を確認するまでは、Pagesを有効化したりワークフローを実行したりしないでください。詳しくは [Pagesの公開元設定](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) と [PagesサイトのHTTPS・公開範囲](https://docs.github.com/en/enterprise-cloud@latest/pages/getting-started-with-github-pages/securing-your-github-pages-site-with-https) を確認してください。

この正本のPagesワークフローは自動実行ではなく、`workflow_dispatch`による手動実行です。また、配信するのはアプリ本体とPWA用ファイルだけで、文書・レビュー・状態ファイルは配信対象に含めません。

## 公開URLを許可する場合の一度だけの操作

1. GitHubで `kkrod899/kajitori-game` を開く。
2. `Settings` → `Pages` で、公開元に `GitHub Actions` を選ぶ。
3. `Actions` → `Publish the app to GitHub Pages` → `Run workflow` を一度実行する。
4. 表示されたURLをスマホで開く。
5. iPhoneはSafariの共有メニューから「ホーム画面に追加」、Androidはブラウザメニューから「ホーム画面に追加」を選ぶ。

公開URLを許可しない場合は、上の操作を行わず、認証付きホスティングを選びます。その場合も、アプリを同じURL・同じブラウザで開く限り、保存キーは変わりません。

## 保存データについて

保存キー `kajitori_stable_mvp_v2` は変更していません。URL版で保存したデータは、そのURLのブラウザ内に残ります。以前にHTMLファイルを直接開いて保存したデータは、`file://` とURL版で保存場所が分かれるため、URL版へ自動移行はしません。古いHTMLのデータを残したい場合は、URL版で動作確認するまで元ファイルを削除しないでください。
