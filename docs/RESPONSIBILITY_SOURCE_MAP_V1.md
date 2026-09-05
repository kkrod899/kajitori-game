# RESPONSIBILITY SOURCE MAP v1

Date: 2026-09-05
Status: Primary-source baseline

本ファイルは、健康・安全・家庭マネジメント項目を「思いつき」だけで作らないための一次情報マップ。

## 1. 家事・家庭マネジメント

### 内閣府 男女共同参画局 — 令和2年版男女共同参画白書 特集 第2節

https://www.gender.go.jp/about_danjo/whitepaper/r02/zentai/html/honpen/b1_s00_02.html

重要点:

- 家事は食事準備・後片付け、掃除、洗濯、衣類・日用品の整理片付け等を含む
- 育児は乳幼児の世話、付き添い、遊び、送迎、保護者会等を含む
- 作業時間とは別に、家庭生活を滞りなく送るための「マネジメント責任」がある
- 例として、食材・日用品の在庫把握、献立、家族予定調整が明示されている

Masterへの反映:

- `FOOD-*`
- `SUP-*`
- `PLAN-*`
- `LAUN-*`
- `CLEAN-*`
- `DAYCARE-*`
- `FAM-*`

## 2. 母子健康手帳・育児情報

### こども家庭庁 — 母子健康手帳

https://www.cfa.go.jp/policies/boshihoken/techou/

### こども家庭庁 — 母子健康手帳情報支援サイト

https://mchbook.cfa.go.jp/

扱われている主要領域:

- 新生児
- 育児のしおり
- 予防接種
- 乳幼児期の栄養
- お口と歯の健康
- 病気やけが
- 事故予防
- 応急手当

Masterへの反映:

- `INF-*`
- `CHD-MED-*`
- `SAFE-*`
- `FOOD-*`
- `GROW-*`

## 3. 乳幼児健診

### こども家庭庁 — 乳幼児健診に関する取組み

https://www.cfa.go.jp/policies/boshihoken/nyuyojikenshin

重要点:

- 出産後から就学前までの切れ目のない乳幼児健診を扱う
- 実施状況・時期は自治体差があるため、地域設定が必要

Masterへの反映:

- `CHD-MED-005`
- `CHD-MED-006`
- 健診項目は `C` (地域依存) を併記する方向でmetadata化する

## 4. 予防接種

### 厚生労働省 — 予防接種・ワクチン情報

https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/kenkou/kekkaku-kansenshou/yobou-sesshu/index.html

### 生後2か月から推奨される予防接種

https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/kenkou/kekkaku-kansenshou/yobou-sesshu/vaccine/months-2.html

### 生後5か月から推奨される予防接種

https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/kenkou/kekkaku-kansenshou/yobou-sesshu/vaccine/months-5.html

Masterへの反映:

- `CHD-MED-001`〜`CHD-MED-004`
- 実際の接種スケジュールは年齢・接種歴・自治体運用を踏まえる必要があるため、単純な月齢固定カードにしない

## 5. こどもの事故予防

### こども家庭庁 — こどもの事故防止ハンドブック

https://www.cfa.go.jp/policies/child-safety-actions/handbook

対象領域:

- 窒息・誤飲
- 転落・転倒
- 自動車・自転車
- 水まわり
- やけど
- 挟む・切る等
- 応急手当

### 窒息・誤飲事故

https://www.cfa.go.jp/policies/child-safety-actions/handbook/content-1/

Masterへの反映:

- `SAFE-001`〜`SAFE-018`
- `INF-SLEEP-004`〜`INF-SLEEP-006`
- `EMG-*`

特に睡眠安全は「何となく安全」ではなく公式ガイダンスを根拠にする。

## 6. 今後追加する一次情報

- 自治体ごとの保育園・健診・予防接種運用
- 年齢別の歯科・口腔ケア
- 離乳食・栄養
- 熱中症・季節安全
- 災害時の乳幼児家庭向け備蓄
- 車・自転車の乳幼児安全

これらはmetadata pass時に各責任項目へ紐付ける。

## 7. Source rule

- 健康・安全: official source必須
- 園・自治体固有: household/local config必須
- 一般家事: official survey + household config +実証データ
- 事実表示: evidence ruleがないものは「できた」「防げた」と断定しない
