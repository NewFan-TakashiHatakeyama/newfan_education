# 成果物・評価仕様 v1.0.0

## 5つの標準成果物

`Sxxx/` に次を置く。元Excelへ書き戻さず、利用者の指定保存先を優先する。

### 01-design.md カリキュラム設計書

1. 教材版、スキル基準版、原典名・ハッシュ参照、対象ID・正式名、原典のLv定義。
2. 対象者、前提知識、範囲、関連スキル、受講・免除・実務確認方針。
3. 学習目標表（ID、原典Lvとの対応、条件、入力、行動、成果物、品質、境界、失敗）。
4. 単元表（ID、Lv、目標ID、時間内訳、内容、演習、成果物、評価ID）。
5. 学習目標→単元→演習・評価→証拠の対応。
6. 受講順序、必要教材、運営方法、版の管理、設計上の仮定。

### 02-learner.md 受講者教材

導入・用語集と、各単元の本文。単元の記載項目はproduction-standard.mdに従う。練習の解説は含めてよいが、初見評価の解答は含めない。

### 03-exercises.md ケース・課題集

ケースの事業前提、資料、数値、証拠、時系列、問題、提出テンプレートを具体化する。練習と初見評価を明確に区分し、評価問題には問題ID・条件・時間・採点観点を記載する。講師が印刷・切り出しできる単位にする。

### 04-instructor.md 講師・採点ガイド

進行、各課題の模範解・根拠・許容代替解・不適切解、配点、必須合格項目、情報照会への応答、口頭質問、再提出ルール。末尾に内容品質レビュー結果を残す。実際にしていない試行授業や独立レビューを実施済みと書かない。

### curriculum.json 機械確認用の対応表

以下の構造を使う。各説明文を繰り返し収録せず、MarkdownのIDを参照する。

```
{
  "skill_id": "S001", "skill_name": "原典の正式名",
  "standard_version": "1.0.0", "curriculum_version": "1.0.0",
  "source_sha256": "原典ハッシュ", "status": "draft-reviewed",
  "files": ["01-design.md", "02-learner.md", "03-exercises.md", "04-instructor.md"],
  "objectives": [{"id":"S001-L1-O01","level":1,"source_field":"Lv1","behavior":"説明する"}],
  "modules": [{"id":"M01","level":1,"objectives":["S001-L1-O01"],
    "minutes":{"explanation":20,"worked_example":10,"practice":20,"review":10,"assessment":0},
    "evidence":["ゲート整理表"]}],
  "assessments": [{"id":"A1","level":1,"objectives":["S001-L1-O01"],
    "evidence":["ゲート整理表"],"pass_rule":"所定基準","critical_errors":["重大誤判断"]}],
  "total_minutes":60,
  "review":{"source_alignment":true,"case_solvable":true,"answers_checked":true,
    "pilot_conducted":false,"limitations":["試行授業未実施"]}
}
```

配布仕様1.2.0の追加（`scripts/harness.py build` が生成する）：`assessments[].observation_points`（採点表の行名。03の「採点」行と04の採点表に同名で現れること）、`assessments[].minutes`（同Lvの単元の評価分の合計。03の評価見出し直下の分数と一致）、`templates`／`cards`／`roles`（specで割り付けたID。03の見出し・行と照合）、`review.self_check`（`harness finish` が quality-checklist の28項目を04 §8で確認した日付を記録。未完なら "pending"）。`review.case_solvable`・`answers_checked` は自己点検表の該当項目（7〜12、14）と独立解答の記録で裏づける。curriculum.jsonは手書きせず `_spec.json` から生成し、`scripts/lint_curriculum.py` で4本のMarkdownと照合する。lintエラーや未完の自己点検を残して `finish --force` した場合、status は `draft-unverified` になる。

## 統一評価尺度

各評価観点を0〜3で採点する。各Lvの許容支援条件に照らす。

| 点 | 観察基準 |
|---|---|
| 0 | 未提出、実行不能、または重大に誤っている |
| 1 | 重要な欠落があり、許容範囲を超える助言・修正が必要 |
| 2 | 当該Lvで必要な行動・成果物・根拠を満たす |
| 3 | 必要条件に加え、代替案・限界・追跡性まで明確で、手戻りを減らせる |

実技の合格は「全必須観点2以上、重大誤判断0件」。平均点で重大欠陥を相殺しない。知識確認は標準80%以上、必要ならスキルに応じて理由付きで変更。必須確認項目は全問正答。具体的な重大誤判断はスキルごとに定義する。低影響の文章課題等へS001の公開停止ルールを流用しない。

## 内容品質チェック

- 原典の各Lvの動詞・対象・条件を省略なく評価できるか。
- 目標に授業・練習・評価・提出証拠があるか。
- 知識・実行・設計/指導の違いが課題に表れているか。
- 提示資料から解答できるか。不足時の照会回答があるか。
- 数値、時系列、版、権限、模範解に矛盾がないか。
- 正常例・異常例・境界例と、許容できる代替解があるか。
- 講師が採点でき、受講者が不足を修正できる具体性があるか。
- 文章だけでなく当該技能の実演・成果物で判定できるか。
- 同じ能力を過不足なく評価し、無関係な専門知識で落とさないか。
- 設計値・架空設定・未確認事項を事実と混同していないか。

機械検証（validate＋lint）、独立解答（評価問題を資料だけで解く1エージェント1回。使えない環境では自己解答と明記）、quality-checklistによる自己点検（結果を04の8節の表に記録）を通った状態をdraft-reviewedとする。独立した多視点レビューは必須ではなく、実施した場合のみ記録する。試行授業後に、完遂時間、誤読、採点者間の差を記録してpilot-validatedへ進める。全106件は制作状態を個別管理し、未制作行を機械的に完成へ変更しない。
