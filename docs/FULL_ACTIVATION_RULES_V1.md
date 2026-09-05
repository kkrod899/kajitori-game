# FULL ACTIVATION RULES v1

Date: 2026-09-05  
Branch: `experiment/production-scope-v1`  
Status: 293/293 rule coverage / shadow-only

## 結論

293項目すべてについて、`その家庭に存在し得る`と`今日表示する`を分離したactivation contractを生成できる状態にした。

- 高影響163項目: item-level explicit policy pass 1
- 残り130項目: constrained policy pass 1
- 合計: 293項目

ただし130項目は、実生活データで個別調整する前の制約付き初期ルールであり、production-readyと扱わない。全ルールの`maturity_ceiling`は`shadow_only_not_active_reliance`。

## 全項目に持たせるもの

1. profile gate
2. age / lifecycle gate
3. feature gate
4. household/local config gate
5. runtime activation signals
6. suppression signals
7. layer policy (`now / today / routine / review`)
8. repeat / cooldown policy
9. close condition
10. evidence claim ceiling
11. source / health-safety review linkage

## 重要な安全条件

- profileや家族構成が一致しただけでは表示しない
- runtime signalが0なら候補も0
- `target_count`や`daily_limit`を使わない
- 健康・安全は別review gateを通らない限り候補化しない
- UIに収めるために候補を3件へ削らない

## 130項目の扱い

キッチン、洗濯、掃除、日用品、ごみ、行政、設備、災害、成長、遊びの130項目は、trigger typeと家庭設備・年齢・地域設定を用いたconstrained pass。

このpassの目的は、すべてを毎日表示することではなく、shadow testで次を検出可能にすること。

- 本来出すべきなのにsignal設計が足りない
- feature gateがなく不要家庭へ出る
- review cadenceが早すぎる / 遅すぎる
- 1項目の粒度が粗すぎる / 細かすぎる
- masterに項目自体がない

## 受入の境界

293/293 coverageは「使えることの証明」ではない。

次の証明は7日shadow baselineで行う。

- critical miss = 0
- hard-deadline miss = 0
- evidence overclaim = 0
- management miss / noise / timing errorのbaseline取得
- partner prompt dependency / close-loop failure / master gapの特定
