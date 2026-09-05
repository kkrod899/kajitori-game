# Handoff

最終更新: 2026-09-05 / ChatGPT

## 現在地

| 項目 | 状態 |
|---|---|
| プロダクト | 家事取りゲーム v0.3 UX刷新 |
| 正本リポジトリ | `kkrod899/kajitori-game` |
| 本番ブランチ | `main` — 現時点では公開中のv0.2 |
| 実装ブランチ | `ux/mobile-v03` |
| Pull Request | PR #1 `v0.3: iPhone向けUX/UI刷新` |
| 公開URL | `https://kkrod899.github.io/kajitori-game/` |
| 保存 | `localStorage` / key `kajitori_stable_mvp_v2` / `v02` namespace version 2を維持 |
| v0.3仕様 | `docs/V0_3_UX_SLICE.md` |
| 事後監査 | `reviews/2026-09-05-0005-chatgpt-v0-3-ux-post.md` |
| Decision | D-026〜D-030をAccepted |
| 現在フェーズ | 最終branch CI → mainへmerge → Pages手動配信 → 物理iPhone受入 |

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
| 一覧 | 最大5件のコンパクトカード。カテゴリ / 行動名 / 短い補足 / 目安時間 |
| 通常項目 | チェック1タップで完了 |
| 状態項目 | ボトムシートで3段階状態を確認して完了 |
| 詳細 | ボトムシート。理由と終了条件は`判断のヒントを見る`へ格納 |
| 低頻度操作 | `…`に`あとで見る / 今日は出さない / もう済んでいる` |
| Undo | トーストまたは完了チェック再タップ。派生証拠も整合させる |
| スクロール | 本文と下ナビを別レイアウト行へ分離。固定ナビを本文に重ねない |
| 優先順位 | 時間帯で静的に候補順を補正 |
| 0件 | Today候補一覧を閉じる |
| 1日1問 | 独立カードを廃止し、必要な状態確認を該当タスク詳細へ統合 |

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
- `tests/v03_smoke.mjs`
- `.github/workflows/v03-validate.yml`
- `docs/V0_3_UX_SLICE.md`
- `docs/DECISIONS.md`
- `reviews/2026-09-05-0005-chatgpt-v0-3-ux-post.md`

### 保存互換性

v0.3はデータ移行ではなくUX/UI刷新として実装した。

- `STORAGE_KEY='kajitori_stable_mvp_v2'`を維持
- `v02.version=2`を維持
- 旧rootの`tasksByDate / missedLog / retryQueue`を削除しない
- 既存profile/day/stateFacts/evidenceEvents/spontaneous/questionHistoryを継続利用
- localStorage書込失敗時のロールバックを維持

## 事後監査で発見・修正したこと

| Severity | Finding | 状態 |
|---|---|---|
| P1 | `この先`から明示追加した低優先度項目がToday上位5件に入らず見えない | Fixed — 明示追加を最優先表示 |
| P1 | オムツ証拠が実際には未確認の「補充できた」まで主張 | Fixed — `少ない段階で気づけた`へ限定 |
| P1 | 完了を戻した後も派生証拠が残る | Fixed — 同日同templateの派生証拠も削除 |
| P2 | `今日は出さない` / `あとで見る`がForecast側で同日再提示される | Fixed |
| P2 | 完了済み詳細から低頻度操作で別状態へ遷移できる | Fixed — `完了を戻す`へ一本化 |

P0/P1の未解決Findingはない。

## 自動検証

GitHub Actions `Validate v0.3 mobile UX` を追加した。

Run #9 `33934349296` の結果:

| 検証 | 結果 |
|---|---|
| JavaScript syntax | Pass |
| 必須資産 / Pages配信参照 | Pass |
| Chromium 390×844 | Pass |
| WebKit 390×844 | Pass |
| main scroll / bottom nav non-overlap | Pass |
| 0件で候補一覧を閉じる | Pass |
| 3件設定の保存 | Pass |
| 状態入力 → 完了 → 保存 | Pass |
| 証拠イベント生成 | Pass |
| 完了取消 → 派生証拠削除 → 再完了で再生成 | Pass |
| 通常項目1タップ完了 / reopen | Pass |
| Forecast → Today明示追加 | Pass |
| 3タブ遷移 | Pass |
| 旧root / questionHistory保持 | Pass |
| console/page error | 0 |

WebKitスクリーンショットも目視し、ボトムシートと背景レイアウトに大きな崩れは確認されなかった。

## レビュー境界

事後監査は実装と同じChatGPTセッション内で役割を切り替えて実施しており、Claude等の独立レビューではない。この制約はレビュー記録にも明記している。

自動検証を含めP0/P1は解消済みのため、v0.3を限定Pages配信し、物理iPhone受入へ進める。物理端末で問題が出た場合は7〜14日実生活テストを再開せず、v0.3を修正する。

## 残存リスク

| Severity | 内容 |
|---|---|
| P2 / Validation | 物理iPhone Safari / ホーム画面追加版のsafe-area、実キャッシュ更新は未確認 |
| P2 | 保育園先読みは祝日・個別休園日を知らず、次の平日を候補とする |
| P3 | ホーム画面PNGアイコンは旧配色のまま。アプリ内UI・manifest themeはブルーグレーへ更新済み |

## 次の一手

1. `ux/mobile-v03`最終headのCIがPassしていることを確認
2. PR #1を`main`へmerge
3. `Publish the app to GitHub Pages`を手動実行
4. 公開URLがv0.3資産を配信していることを確認
5. 主要利用者本人のiPhoneで以下を受入確認
   - 下ナビが本文を隠さない
   - 最下部まで普通にスクロールできる
   - 通常項目1タップ完了
   - オムツ状態選択→完了
   - 完了を戻せる
   - `今日 / この先 / 記録`が切り替わる
   - ホーム画面追加版でも同じ表示
6. 問題がなければv0.3で7〜14日実生活テストを再開

## 再開時の読み順

1. `HANDOFF.md`
2. `docs/PRODUCT_BRIEF.md`
3. `docs/COLLABORATION_WORKFLOW.md`
4. `docs/DECISIONS.md`
5. `docs/V0_3_UX_SLICE.md`
6. `reviews/2026-09-05-0005-chatgpt-v0-3-ux-post.md`
7. `docs/V0_2_UX_SPEC.md` — v0.3でも維持するプロダクト原則・データルール確認用
