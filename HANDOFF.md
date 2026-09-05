# Handoff

最終更新: 2026-09-05 / ChatGPT

## 現在地

| 項目 | 状態 |
|---|---|
| プロダクト | 家事取りゲーム v0.3 UX刷新 |
| 正本リポジトリ | `kkrod899/kajitori-game` |
| 本番ブランチ | `main` — 現時点では公開中のv0.2 |
| 実装ブランチ | `ux/mobile-v03` — v0.3実装済み、公開前検証中 |
| 公開URL | `https://kkrod899.github.io/kajitori-game/` |
| 保存 | `localStorage` / key `kajitori_stable_mvp_v2` / `v02` namespace version 2を維持 |
| v0.3仕様 | `docs/V0_3_UX_SLICE.md` |
| 共有思想 | `docs/PRODUCT_BRIEF.md` |
| Decision | D-026 / D-027をAcceptedで追加 |
| 現在フェーズ | v0.3独立レビュー → iPhone実機確認 → main → Pages公開 |

## v0.3へ進んだ理由

2026-09-05、主要利用者本人がGitHub Pages版v0.2をiPhoneで実利用し、7〜14日テストを続ける前にUI/UX上の大きな摩擦を確認した。

- 下部ナビが本文へ重なり、スクロールが崩れる
- `今やる`を経由することでタップ数が多い
- `状態事実`等の文言が内部仕様寄りで直感的でない
- 理由・終了条件の常時表示でカードが長すぎる
- `担当`固定タブの価値が低い
- 時間帯と候補優先順位が合わない
- 旧くすみグリーン系の視覚方向が本人の嗜好に合わない

このためD-014の実生活テストを一度止め、UI摩擦を先に修正することをD-026でAcceptedとした。

## v0.3で固定したUX

| 領域 | 決定 |
|---|---|
| 視覚 | 白〜暖灰ベース + ブルーグレー `#5F86A4`。イラストなし |
| ナビ | `今日 / この先 / 記録` の3タブ |
| 設定 | 右上歯車 |
| 今日の量 | 0 / 1 / 2 / 3件を直接選択。評価スコアではなく負荷設定 |
| 一覧 | コンパクトカード。カテゴリ / タイトル / 短い補足 / 目安時間 |
| 通常項目 | チェック1タップで完了 |
| 状態項目 | ボトムシートで3段階状態を選び、最大2タップで状態記録＋完了 |
| 詳細 | ボトムシート。理由と終了条件は`判断のヒントを見る`へ格納 |
| 低頻度操作 | `…`に`あとで見る / 今日は出さない / もう済んでいる` |
| Undo | トーストまたは完了チェック再タップ |
| スクロール | 本文と下ナビを別レイアウト行へ分離。固定ナビを本文に重ねない |
| 優先順位 | 時間帯で静的に候補順を補正 |

## 実装済みファイル — `ux/mobile-v03`

- `kajitori_minimal_pictogram_compact.html`
- `kajitori_v03.css`
- `kajitori_v03_core.js`
- `kajitori_v03_actions.js`
- `kajitori_v03_ui.js`
- `index.html`
- `manifest.webmanifest`
- `sw.js`
- `.github/workflows/pages.yml`
- `docs/V0_3_UX_SLICE.md`
- `docs/DECISIONS.md`

### 保存互換性

v0.3はデータ移行ではなくUX/UI刷新として実装した。

- `STORAGE_KEY='kajitori_stable_mvp_v2'`を維持
- `v02.version=2`を維持
- 旧rootの`tasksByDate / missedLog / retryQueue`を削除しない
- 既存profile/day/stateFacts/evidenceEvents/spontaneousを継続利用
- localStorage書込失敗時のロールバックを維持

## 現在までの検証

| 検証 | 結果 |
|---|---|
| ローカルで生成したv0.3 JavaScriptの`node --check` | Pass |
| v0.3 HTMLからCSS/JSを外部資産として分離 | 完了 |
| service worker cache | `kajitori-shell-v3`へ更新 |
| Pages artifact | v0.3 CSS/JSをコピー対象へ追加 |
| index / manifest / app theme color | `#5F86A4`へ統一 |
| 既存保存キー/namespace | 変更なし |
| ローカルChrome実行 | **未完了**。実行環境の組織ポリシーでlocalhost/file/data URLがブロックされたため |
| iPhone Safari実機 | **未確認**。公開候補で最終確認が必要 |

ローカルブラウザ検証を実施できなかったことをPass扱いしない。

## 公開前に必ず確認すること

1. 独立レビューでP0/P1がないこと
2. JavaScript構文と参照資産の欠落がないこと
3. iPhone Safariで下部ナビが本文を隠さないこと
4. ホーム画面追加版でも本文だけがスクロールすること
5. 通常項目が1タップ完了できること
6. 状態項目が状態選択→完了で閉じること
7. 完了Undoが動くこと
8. 既存localStorageを読み込んでも記録が消えないこと
9. service worker更新後に旧UIが残らないこと

## 既知の残存リスク

| Severity | 内容 |
|---|---|
| P2 | 保育園先読みは祝日・個別休園日を知らず、次の平日を候補とする |
| P3 | ホーム画面PNGアイコンは旧配色のまま。アプリ内UI・manifest themeはブルーグレーへ更新済み |
| Validation | 現環境ではブラウザ実行できないため、Safari実機確認が公開前の必須ゲート |

## 次の一手

1. `ux/mobile-v03`の差分を独立レビューする
2. FindingsをAccepted / Rejected / Deferredで処理する
3. P0/P1解消後に`main`へマージ
4. GitHub Pages workflowを手動実行
5. iPhoneの公開URL / ホーム画面追加版で実機確認
6. 問題がなければv0.3として7〜14日実生活テストを再開

## 再開時の読み順

1. `HANDOFF.md`
2. `docs/PRODUCT_BRIEF.md`
3. `docs/COLLABORATION_WORKFLOW.md`
4. `docs/DECISIONS.md`
5. `docs/V0_3_UX_SLICE.md`
6. `docs/V0_2_UX_SPEC.md` — v0.3でも維持するプロダクト原則・データルール確認用
7. `reviews/2026-08-30-0004-chatgpt-v0-2-slice-01-post.md` — v0.2以前の実装レビュー履歴
