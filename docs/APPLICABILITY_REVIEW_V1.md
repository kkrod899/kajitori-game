# APPLICABILITY REVIEW v1

Date: 2026-09-05  
Status: Model correction / item-level pass pending  
Branch: `experiment/production-scope-v1`

## 1. 289 / 293の読み方を修正する

架空家庭へ粗い適用条件を当てた結果、293項目中289項目が「長期的にはこの家庭に関係し得る」と判定された。

これはそのまま「289件を毎日出す」という意味ではない。

一般家庭では、掃除、洗濯、食事、在庫、予定、行政、災害準備等の多くは構造的には関係するため、**structural applicabilityが高いこと自体を失敗と断定しない**。

一方で、現在のmetadataがgroup-level条件に依存しすぎているのも事実。

問題は比率そのものではなく、次の2概念を十分分離できていないこと。

1. `structural applicability`
   - その責任がその家庭に存在し得るか
2. `activation eligibility`
   - 今・今日・今週にその責任を出す根拠があるか

## 2. production-scopeで必要な判定層

```text
293 responsibility master
    ↓ structural applicability
家庭に存在し得る責任
    ↓ lifecycle / feature / local rules
現在の生活段階で有効な責任
    ↓ state / deadline / inventory / cadence
今・今日・レビュー対象
```

「家庭に存在し得る責任」を60〜120件等へ先に合わせることはしない。

件数目標を先に置くと、旧「今日3件」と同じ問題を別レイヤーで再発させるため。

## 3. 現在入っている明示的feature gate

現時点で少なくとも以下は家庭条件で抑制する。

- 搾乳母乳管理 → `expressed_milk_used`
- 搾乳器管理 → `breast_pump_used`
- 離乳食 → `weaning_started`
- 自転車幼児座席 → `uses_bicycle_childseat`
- 車のチャイルドシート → `uses_car`
- トイレ支援 → `toilet_support_needed`
- 保育園20項目 → `daycare` + `daycare_rules`
- ごみ収集 → `municipality_waste_calendar`等
- 車・自転車管理 → `uses_car_or_bicycle`

## 4. まだ不足しているitem-level gate

### 乳児・成長

- 月齢/修正月齢だけでなく、実際の発達段階
- 寝返り・移動範囲等による安全環境の変化
- ミルク/母乳/搾乳/離乳の利用状態
- 使用中の育児機器

### 上の子

- 園利用日か休日か
- トイレ・着替え等の自立度
- 行事・持ち物・習い事等の家庭固有状態

### 安全

- 車、自転車、階段、ベビーゲート等の設備/利用有無
- 子どもが実際に届く範囲
- 季節・外出状況
- 製品固有の安全条件

### 家事・住環境

- 乾燥機、食洗機等の設備
- ごみ分別・回収制度
- 家の部屋/設備
- 定期購入・宅配利用

### 行政・制度

- 居住自治体
- 利用中の給付・保険・園制度
- 実際の期限・更新周期

## 5. 毎日表示を絞る本丸はactivation eligibility

structural applicabilityが高くても、以下が成立しなければ日次候補へ出さない。

- deadlineが近い
- inventory thresholdを下回った
- stateが変化した / unknownになった
- review cadenceが到来した
- handoffが必要になった
- lifecycle条件が変化した
- routine occurrenceが実際に発生した
- safety/health contextが変化した

したがってproduction experimentで測るべきなのは、単なる「家庭適用率」ではなく次。

- 今日出した候補が実際に必要だったか
- 必要だった責任を出せたか
- 出すタイミングが合っていたか
- 家庭固有のfeature gateが効いたか

これを`EXPERIMENT_SHADOW_TEST_V1.md`のmiss/noise/timing/master-gapで測る。

## 6. 現時点の判定

- 293 master coverage: seedとして成立
- structural applicability: **まだ粗いが、高比率だけを理由に失敗とはしない**
- activation eligibility: synthetic scenarioで可変件数化を確認済み
- item-level feature/lifecycle/local rules: **未完了**
- production PWA connection: **まだ不可**

## 7. 次のpass

優先順:

1. health/safety 42項目のboundary条件
2. 乳児59項目 + 子ども健康18項目
3. 園20項目
4. 成長・遊び22項目
5. 設備依存の家事・安全
6. 行政・自治体依存

各passで「項目を減らす」ことを目標にしない。**必要な家庭だけに、必要な時だけ出せる状態を作ること**を目標にする。
