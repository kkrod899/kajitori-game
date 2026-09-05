# RESPONSIBILITY SOURCE MAP v1

Date: 2026-09-05  
Status: Primary-source baseline / high-impact source pass 2

本ファイルは、健康・安全・家庭マネジメント項目を「思いつき」だけで作らないための一次情報マップ。

## Source IDs

| Source ID | 発行主体 | 文書 / ページ | URL | 主な適用範囲 |
|---|---|---|---|---|
| `SRC-HOUSEHOLD-001` | 内閣府 男女共同参画局 | 令和2年版男女共同参画白書 特集 第2節「家事・家庭のマネジメントの分担」 | https://www.gender.go.jp/about_danjo/whitepaper/r02/zentai/html/honpen/b1_s00_02.html | 食材・日用品在庫、献立、家族予定、家庭マネジメント責任 |
| `SRC-MCH-001` | こども家庭庁 | 母子健康手帳 / 母子健康手帳情報支援 | https://www.cfa.go.jp/policies/boshihoken/techou/ / https://mchbook.cfa.go.jp/ | 乳幼児の健康・発達・育児全般の基礎領域 |
| `SRC-CHECKUP-001` | こども家庭庁 | 乳幼児健診に関する取組み | https://www.cfa.go.jp/policies/boshihoken/nyuyojikenshin | `CHD-MED-005`〜`006`。自治体差を前提に扱う |
| `SRC-VAX-001` | 厚生労働省 | 予防接種・ワクチン情報 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/kenkou/kekkaku-kansenshou/yobou-sesshu/index.html | `CHD-MED-001`〜`004` |
| `SRC-SLEEP-001` | こども家庭庁 | 赤ちゃんが安全に眠れるように ～1歳未満の赤ちゃんを育てるみなさまへ～ | https://www.cfa.go.jp/policies/boshihoken/kenkou/sids | あおむけ寝、硬く平坦な寝具、寝床周辺、掛け布団等の睡眠環境 |
| `SRC-ACCIDENT-001` | こども家庭庁 | こどもの事故防止ハンドブック | https://www.cfa.go.jp/policies/child-safety-actions/handbook | 窒息・誤飲、転落、車・自転車、水まわり、やけど等 |
| `SRC-DAYCARE-INFECT-001` | こども家庭庁 | 保育所における感染症対策ガイドライン（2018年改訂版、2023年一部改訂・修正） | https://www.mhlw.go.jp/content/10900000/20231010_policies_hoiku_25.pdf | 園利用時の感染症情報・登園関連。個別園ルールの上書きが必要 |
| `SRC-FEED-001` | 厚生労働省 | 授乳・離乳の支援ガイド（2019年3月） | https://www.mhlw.go.jp/content/11908000/000496257.pdf | 授乳、離乳、食物アレルギーを含む栄養支援。個別性を前提に扱う |
| `SRC-ORAL-001` | 厚生労働省 | 乳幼児期における歯科保健指導 | https://www.mhlw.go.jp/content/001490222.pdf | 歯磨き・仕上げ磨き、口腔観察、年齢・状態に応じた歯科保健 |
| `SRC-HEAT-001` | 環境省 | 熱中症予防情報サイト / 暑さ指数(WBGT) | https://www.wbgt.env.go.jp/ | 暑熱時の外出・活動判断に使う環境リスク情報 |
| `SRC-CHILDSEAT-001` | 警察庁 | 子供を守るチャイルドシート | https://www.npa.go.jp/bureau/traffic/anzen/childseat.html | チャイルドシート使用、取付・着座、安全確認 |
| `SRC-BICYCLE-001` | 警察庁 | 自転車は車のなかま～自転車はルールを守って安全運転～ | https://www.npa.go.jp/bureau/traffic/bicycle/info.html | 子どものヘルメット、幼児用座席利用時の安全 |
| `SRC-DISASTER-001` | 内閣府 防災 | 自然災害への備えは万全ですか？チェックしてみよう！ | https://www.bousai.go.jp/kyoiku/hokenkyousai/check.html | 乳幼児用哺乳瓶・紙おむつを含む持出品、家庭備蓄、連絡方法 |
| `SRC-CHILD-8000-001` | 厚生労働省 | 子ども医療電話相談事業（#8000） | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/newpage_55223.html | 休日・夜間の子どもの症状で判断に迷う際の相談先。地域別実施時間も確認対象 |
| `SRC-FIRE-001` | 総務省消防庁 | 住宅用火災警報器Q&A / 点検・交換 | https://www.fdma.go.jp/relocation/html/life/yobou_contents/qa/ | 住宅用火災警報器の作動確認、維持管理、交換 |

## 1. 家事・家庭マネジメント

`SRC-HOUSEHOLD-001`では、実作業とは別に「日々の家事をマネジメントする責任」「家庭生活を滞りなく送る責任」が明示され、例として食材・日用品の在庫、献立、家族予定の調整が扱われている。

Masterへの反映:

- `FOOD-*`
- `SUP-*`
- `PLAN-*`
- `LAUN-*`
- `CLEAN-*`
- `DAYCARE-*`
- `FAM-*`

## 2. 母子健康・健診

`SRC-MCH-001`を乳幼児の一般的な健康・発達領域の基礎ソースとする。ただし個別の安全・医療・栄養項目では、より直接的な一次情報を追加する。

乳幼児健診は自治体運用差があるため、`SRC-CHECKUP-001`だけで実施時期を断定しない。`CHD-MED-005`・`006`は地域設定を必要とする。

## 3. 予防接種

`CHD-MED-001`〜`004`は`SRC-VAX-001`を直接ソースとする。

接種候補は単純な月齢固定カードにしない。少なくとも年齢、接種歴、予約状況、自治体・医療機関の運用を状態入力として扱う。

## 4. 睡眠安全・事故予防

`INF-SLEEP-004`〜`006`と`SAFE-001`は`SRC-SLEEP-001`を直接紐付ける。睡眠環境については、あおむけ、硬く平坦な寝具、顔周辺へ物を置かない等の公式情報を根拠にする。

`SAFE-*`は`SRC-ACCIDENT-001`を基本ソースとし、車・自転車・暑熱など専門情報がある項目は追加ソースを併用する。

重要な証拠境界:

- 安全状態を確認した記録から「事故を防いだ」とは断定しない
- 記録できるのは確認時点の状態と、実際に行った除去・回避等のアクションまで

## 5. 保育所・感染症

`CHD-MED-015`等の園利用時の感染症関連は`SRC-DAYCARE-INFECT-001`を基礎にする。

ただし、登園可否や提出方法は個別園・自治体の運用が優先されるため、必ず`daycare_rules` / `local_infection_rules`を設定してから出す。

## 6. 授乳・離乳・食事制約

`SRC-FEED-001`は2019年改定版を採用する。ガイド自体が親子の個別性を尊重する考え方を示しているため、アプリ側で画一的な食事量・開始時期・進行を「正解」として断定しない。

主な紐付け:

- `INF-FEED-*`
- `FOOD-015`
- `FOOD-016`

## 7. 乳幼児の口腔ケア

`OLD-DAILY-003`等の歯磨き・仕上げ磨き関連は`SRC-ORAL-001`を直接ソースとする。

年齢・口腔内状態に応じた対応が必要なため、歯の生え方や個別相談の必要性を機械的に診断しない。

## 8. 暑熱・季節安全

`SAFE-018`は`SRC-HEAT-001`を追加ソースとし、将来リアルタイム化する場合はWBGT等の外部状態を入力として扱う。

現段階の実証では、シナリオ側から`context_changed`や暑熱リスク状態を与え、アプリが独自に気象値を推定しない。

**Finding:** 現行masterの`SAFE-018`は「暑さ・寒さ」を一つにまとめているが、現sourceは暑熱側を直接支える。寒冷側を同じ根拠で出さない。item-level reviewで分割または文言修正が必要。

## 9. 車・自転車

- `SAFE-011` / `GROW-005`: `SRC-CHILDSEAT-001`
- `SAFE-013`: `SRC-BICYCLE-001`

車・自転車を使わない家庭には出さない。チャイルドシートは使用有無だけでなく、取付・着座状態の確認を別の状態として扱う。

## 10. 休日・夜間の子どもの症状

`CHD-MED-008`・`CHD-MED-009`・`SAFE-016`の「相談先」部分には`SRC-CHILD-8000-001`を追加する。

#8000は診断ロジックではなく、休日・夜間に保護者が判断に迷った時の専門相談導線として使う。実施時間は都道府県で異なるため、表示時に地域情報を確認する。

アプリ側は症状から独自に診断・受診要否を確定しない。

## 11. 災害・緊急時準備

`EMG-*`は`SRC-DISASTER-001`を基本ソースとする。

内閣府情報では、乳幼児がいる家庭の持出品として哺乳瓶や紙おむつ等を挙げ、家庭備蓄は最低3日、できれば1週間を目安としている。実証ではこの数字をそのまま毎日のノルマにせず、備蓄レビューの根拠として使う。

`EMG-010`の住宅用火災警報器は、防災一般情報だけでなく`SRC-FIRE-001`を直接ソースとする。作動確認・維持管理・交換は消防庁情報を基準にする。

## 12. Source rule

- 健康・安全 (`S`): official source必須 + manual review必須
- 園・自治体固有 (`C`): household/local config必須
- 一般家事: official survey + household config + 実証データ
- 事実表示: evidence ruleがないものは「できた」「防げた」と断定しない
- ソースがあっても、個別診断・個別医療判断を自動生成しない
- source coverageは「URLが付いている」だけでPassにしない。項目の表示条件・完了条件・断定範囲を直接支えているかを確認する

## 13. 次のsource pass

今後、293項目を個別レビューする際に追加する。

- `SAFE-018`寒冷側の分割/直接source
- 自治体ごとのごみ・健診・予防接種・保育園運用
- 個別の設備・製品安全（ベビーカー、抱っこ紐等）の製品説明書 / 安全基準
- 食品衛生・家庭内衛生のより直接的な公的資料
- 行政・給付・保険項目の制度別一次情報

source passは「URLを付けたら完了」ではなく、そのソースが当該項目の表示条件・完了条件・断定可能範囲を実際に支えているかまで確認する。
