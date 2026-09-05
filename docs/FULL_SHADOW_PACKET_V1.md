# FULL SHADOW PACKET v1

Date: 2026-09-05  
Status: local/private packet generator / shadow-only

## 目的

293項目のactivation rulesを、実生活へ依存させずに照合するための1日分packetを生成する。

生成物:

- `packet_manifest.json` — ファイルhashと件数
- `engine_candidates.json` — engineの全出力
- `engine_candidates_night_review.md` — 夜に開く人間向け一覧
- `night_observations_template.csv` — 実際に必要だった項目との照合表

## Privacy

実在家庭を使うファイルは`private=true`を必須とし、`data/private/`またはGit管理外の場所へ置く。生成先`artifacts/private_shadow/`もGit対象外。

例示ファイルは`synthetic=true`であり、実在利用者データではない。

## 重要な制約

- 候補は生活判断の正解として使わない
- 日中は候補を原則開示しない
- 夜に実際の出来事と照合する
- 健康・安全・期限は公的案内、園・自治体、医療機関、製品説明書、家庭判断を優先する
- 293/293 rule coverageは実生活適合性の証明ではない

## 現時点のUX課題

JSONとCLIは非エンジニアの日次運用には重い。実baseline開始前に、同じ入力契約を使う簡単なローカルフォームまたはワークブックを作る。
