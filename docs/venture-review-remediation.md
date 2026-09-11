# PdM敵対的レビュー 修正対応表

全実装レビューのP0・P1（R01〜R20）の追加修正・提供範囲・移行手順は、[P0・P1修正対応](pdm-review-p0-p1-remediation.md)を参照。

更新日：2026-09-11。対象：[元の15件の指摘](../outputs/review-ai-project/PdM敵対的レビュー_2026-09-11.md)。

F01〜F15について、API・永続化・画面・設計と受入試験を修正した。業務設計の正本は [AI自社事業PJの設計](venture-governance-design.md)。原本Excelのセル数式をそのまま移植することと、アプリで判断の意味を保つことを区別し、予約行数や確認者情報はアプリの責務として補った。

## 指摘と修正の対応

| ID | 修正後の動作 | 主な検証 |
|---|---|---|
| F01 | GateRunを判断の唯一の入力元とし、概要・ゲート・公開が同じ点検を参照。旧直接承認APIは拒否 | `test_canonical_release_and_eval_revocation_propagate`、`test_archive_preserves_history_and_legacy_gate_cannot_approve` |
| F02 | 集合版・URI・承認者、PlanKey・Manifest・Release・Runの内容と取消を照合。取消を公開準備まで反映 | `test_eval_set_requires_exact_plan_release_and_source_approval`、`test_set_versions_and_duplicate_classifications_are_not_mixed`、取消伝播の正常／異常系 |
| F03 | E01〜E18の欠落・重複を検出。画面に未登録分類を常時表示。RAG/Agentの工程と固有評価も要求 | 1分類・17分類・重複分類・RAG未完了を拒否。18分類の正常公開を検証。画面の18分類表示テスト |
| F04 | EvalTypeを計画版・行IDから分離し、新しい計画でも入力可能。E05のFixture/Reset規則を新しい版でも適用 | `test_new_agent_plan_versions_keep_classification_and_trial_requirements`、新規行とEvalType編集の画面テスト |
| F05 | 完了申告と有効完了を分離。証拠・実績・ロール・独立性・依存を集計へ反映。重要変更で再承認 | `test_completed_status_does_not_count_without_approval_and_edits_invalidate`、`test_dependency_evidence_invalidation_and_runtime_cycle_detection`、独立承認テスト |
| F06 | 確定済み計画／評価／判断は上書き・削除不可。取消は追記のみ。変更前後を監査記録し、案件をアーカイブ | 計画削除拒否、取消の消去拒否、履歴保全、案件保全、並行する承認と内容更新のテスト |
| F07 | 案件RACIとアプリの役割を分離。代筆した判断と責任ロールによる正本確認を区別。サーバが確認者・日時を記録 | `test_project_role_overrides_application_role_without_granting_verification`、署名列の偽装拒否、本人実施の独立承認拒否 |
| F08 | 意味に対応する固定コードとseverityを返す。成功色は完全一致で判定し、未知のラベルを成功にしない | `test_negative_verdicts_never_use_success_style`、未充足の画面色テスト、未保存の正本確認禁止 |
| F09 | イベントを時差付きISO日時で保存・比較。同日逆転を拒否。旧日付のみの記録は要再確認 | `test_same_day_approval_order_and_timezone_required`、`test_timezone_equivalence_and_overnight_incident_order`、既存の公開／緊急／事故の試験 |
| F10 | 工程×ロール×スキル×Personの割当と実在する第三者評価・証拠・稼働期間を照合。工程別不足を表示 | `test_skill_coverage_requires_role_assignment_evidence_and_current_capacity`、実施者との独立性、個人評価の閲覧範囲テスト |
| F11 | 未判定／判定案／確認済み／再判定待ちを分離。R19が根拠付き確認。条件・データ用途・外部AI等の変更で再確認 | `test_risk_change_invalidates_and_full_set_is_required`、`test_data_use_change_invalidates_risk_and_old_decision_after_reconfirmation` |
| F12 | 仮説・次の実験・判断期限・停止条件・KPI・条件・資金・反復期限を案件概要へ接続。実績根拠のある追加投資残額を表示 | `test_summary_prioritizes_overdue_decisions_and_calculates_evidenced_budget`、対象範囲／仮説ID／期間を絞るG4の試験、概要表示テスト |
| F13 | 未入力・未計測の金額や工数を0扱いしない。対象外の理由を持ち、必要入力欠落時は計算値を伏せる | `test_unmeasured_finances_remain_unknown_and_zero_is_explicit`、RT49/50の明示的な0と単位原価の試験 |
| F14 | Excel予約行数を運用上限から外し、seeded台帳にも追加可能。25件ずつ表示 | `test_repeated_runs_can_exceed_workbook_reserved_rows`（61件）、IT04の予約範囲と新規追加、26行目へのページ移動 |
| F15 | 事業PJの追加設計正本と本対応表を追加し、既存のスコープ正本を更新。目録件数を製品適合の証明として扱わない | 原本72ケースとの照合、具体的な業務の正常／異常系、API全体と画面の回帰試験 |

APIの追加試験は [test_venture_governance.py](../apps/api/tests/test_venture_governance.py)、原本との対応は [test_acceptance_sheet33.py](../apps/api/tests/test_acceptance_sheet33.py)、既存のアクセス制御等は [test_venture_ledger.py](../apps/api/tests/test_venture_ledger.py)。画面の試験は [governance.test.tsx](../apps/web/app/ventures/governance.test.tsx) に置く。

## 実施した検証

- API全体：**126 passed / 29.41秒**。最終の実行ログは [api-final-tests.txt](../outputs/review-ai-project/api-final-tests.txt)。一時SQLiteで実行し、開発用・本番用のデータを試験データで更新しない。
- 画面回帰：**6 passed**。分類未登録の表示、否定判定の色、seeded台帳の追加、26行目、保存失敗時の入力保持、未保存の確認禁止、期限超過・未計測表示を検証。
- TypeScript型検査、事業PJ画面のESLint、Next.js本番ビルドを確認。ビルドログは [web-build.txt](../outputs/review-ai-project/web-build.txt)。既存の複数lockfileによるroot推測と学習教材のファイル追跡について警告が出る。
- Alembicの移行を独立したSQLiteで実行し、旧承認を未確認のGateRunへ複写し元行も保持することを検証。移行で承認を推測・昇格しない。
- 並行する承認と内容編集をSQLite上で検証。PostgreSQL実機での並行負荷試験は未実施。

ブラウザで外部正本にログインして署名や証拠内容を検証する操作、本番実行権限との連携、本番デプロイはこの試験に含めていない。DOMテストとAPIテストの成功を、本番の決裁・公開実行が許可されたこととは扱わない。

## 導入時の変更

既存DBには `20260911_0004` の適用が必要。アプリの起動だけでは既存テーブルへ列が追加されない。手順と旧記録の扱いは [DB移行と導入](venture-governance-design.md#db移行と導入) を参照する。この作業では移行ファイルを追加・検証し、本番DBには適用していない。

以前の「証拠なしの完了」「1評価だけの公開前提」「日付だけの公開記録」「旧ゲート画面からの直接承認」「確定記録や案件の物理削除」は、そのまま成功する互換性を保たない。各記録を残したうえで、不足を確認・訂正する導線へ変更している。
