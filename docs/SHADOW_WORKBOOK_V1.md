# SHADOW WORKBOOK v1

Date: 2026-09-05  
Status: non-engineer operator surface / first-baseline preparation

## 目的

7日間のshadow baselineを、JSONやCLIを直接扱わず記録できるようにする。

Workbook generator:

```bash
python3 tools/build_shadow_workbook.py --out artifacts/kajitori_shadow_test_7days_v1.xlsx
```

記入済みworkbookは次でprivate JSON/JSONLへ変換できる。

```bash
python3 tools/parse_shadow_workbook.py \
  --input artifacts/kajitori_shadow_test_7days_v1.xlsx \
  --out-dir artifacts/private_shadow/workbook_import
```

利用者はコードを実行しない。記入済みファイルを実証担当へ渡し、担当側が変換・engine照合・集計を行う。

## Sheets

| Sheet | 用途 |
|---|---|
| `使い方` | shadow mode、hard gate、毎日の流れ |
| `家庭設定` | 家族構成・設備・生活条件。黄色は要確認 |
| `朝スキャン` | 7日分の既知状態・期限・不足・未完了 |
| `状態ログ` | 具体的な責任IDとruntime signal |
| `実際ログ` | 日中に本当に必要だった家庭運営 |
| `候補取込` | 夜または7日後にengine候補を貼り付けて判定 |
| `集計` | hard gateとbaseline metrics |
| `マスター` | 293責任項目。非表示 |
| `コード表` | プルダウン用。非表示 |
| `変更履歴` | 実証途中の仕様変更を記録 |

## 設計上の重要点

- 日中にengine候補を見る必要はない
- 朝の状態を先に固定し、候補は決定論的に後生成できる
- 実際ログにはmasterに無い項目もID空欄で記録できる
- 候補側では不要・早すぎ・遅すぎ・重複・Evidence過大を記録できる
- 集計は件数ノルマを持たず、critical miss / hard deadline miss / evidence overclaimをhard gateとする
- 第一期間中に都合よく合格線を追加しない

## Privacy

実在家庭の記入済みworkbook、変換JSON、観測CSVはGitへ入れない。`.gitignore`のprivate pathへ置く。

## 完了していないこと

Workbookは入力・照合面であり、293 ruleの実生活妥当性を証明しない。第一期7日データを取得した後、miss/noise/timing/master gapに基づきruleを修正する。
