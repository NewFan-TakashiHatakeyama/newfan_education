# P0/P1・UI/UX・P2 リリース検証

## 2026-09-11 ローカル検証

- SQLite API：148件成功。
- 専用PostgreSQL 13 API：148件成功。新規移行と同時作成・同時更新テストを含む。
- PostgreSQL 0004→0005：既存ユーザー保持、セッション失効を確認。
- pg_dump / pg_restore：0004バックアップを別DBへ復元し、再移行に成功。
- Web：Lint、型チェック、単体8件、本番ビルド成功。
- ブラウザーE2E：7件成功（招待、独立確認者、評価履歴、PDF/CSV、操作性、通信失敗、保管・再開）。
- PostgreSQL＋本番WebビルドのローカルE2E：7件成功。
- GitHub Actions（コミット `ed304eb`）：web / api / postgres-e2e の全3ジョブ成功。PostgreSQL 16で移行・復元・API・業務E2Eを検証。
- 実行記録：https://github.com/NewFan-TakashiHatakeyama/newfan_education/actions/runs/34585755851

## 反映手順

1. 修正ブランチでCIを通す。
2. 本番DBと分離したステージングAPI・Webに同一コミットを反映し、認証・案件表示・更新・保管・再開を確認。
3. 本番の0004バックアップと復元先を確保する。
4. API移行・更新後、Webを更新。既存セッションは失効するため再ログインを確認。
5. healthz、認証、案件・台帳表示、ログの異常を確認。

## 復旧

0005は評価履歴を保持するためダウングレードしない。移行失敗・主要APIの継続的500・認証不能があれば公開を止め、旧コードと移行前バックアップを別DBへ復元して接続先を切り替える。移行後に追加された記録は保全し、差分を確認してから復旧する。

## 環境反映の状況

2026-09-12 JSTに本番反映後の確認まで完了。P2、アーカイブ、デモ、PostgreSQL・CI、ステージング確認後の本番適用の順に実施した。

### DBバックアップとステージング

- Neon認証完了後、プロジェクト `raspy-poetry-94338205`（PostgreSQL 18）で移行前のデータ・スキーマを複製。
- 本番ブランチ：`br-lingering-bird-azh22x1x`。
- 移行前バックアップ：`pre-release-20260911` / `br-orange-cloud-az6lfr0n`。2026-09-11 22:36:42 JST作成、自動削除なし。復旧用として変更せず保持する。
- ステージングDB：`staging-review-20260911` / `br-solitary-hat-az2zyfaz`。バックアップから分離して作成。
- ステージングAPI：https://newfan-education-api-staging.onrender.com （`srv-dai0c9ss728c73ds5ndg`）。専用JWTと分離DBを使用。
- ステージングWeb：https://newfan-education-git-71a3d8-newfan-takashihatakeyamas-projects.vercel.app 。VercelのAPI接続先はPreviewだけを変更し、本番設定を維持。
- PostgreSQL 18で0004→0005の移行・起動に成功。既存アカウントのログイン、既存保管案件の表示、検証案件の作成・保存・保管・理由付き再開を確認。
- 検証案件：`venture-350ce39cfc`「ステージング検証：問い合わせ支援AI」。工程132件、適用89件、判定待ち43件、評価計画の入力あり0/18を確認。

### 本番反映

- 本番コミット：`3bc34ef9ca076d6441ea68ffaf3d93461dd52fe9`。修正コードは `ed304eb`、その後の差分は検証記録。mainへ反映済み。
- [mainのCI](https://github.com/NewFan-TakashiHatakeyama/newfan_education/actions/runs/34607394637)：web / api / postgres-e2eの全3ジョブ成功。PostgreSQL 16で移行・同時更新・復元・業務E2Eを検証。
- [本番APIデプロイ](https://dashboard.render.com/web/srv-dahnh2bm8hqs73cjatu0/deploys/dep-dai0i26k1f9s73fdgr00)：上記コミットでDeploy succeeded / Live。2026-09-11 22:59:30 JSTにApplication startup complete。
- APIは起動前に `alembic upgrade head` を実行し、失敗時は起動を止める構成。今回の移行後の正常起動とhealthzの200を確認。
- [本番Webデプロイ](https://vercel.com/newfan-takashihatakeyamas-projects/newfan-education-web/8Q31CTk61J5HYx58Ukgxwb5Y7if6)：上記コミットでReady / Production / Current Domainsを確認。
- 本番Web：https://newfan-education-web.vercel.app
- 本番API：https://newfan-education-api.onrender.com

### 本番での操作確認

- 移行後に既存管理者アカウントで再ログイン成功。
- 既存案件 `venture-1f42811f7e` を一覧・概要から表示。保管状態と「アーカイブ済み・閲覧専用」を確認。
- 工程タスク：132件、適用89件、判定待ち43件、完了0件を表示。
- 評価計画・品質ゲート：初期行を入力済みと数えず「入力あり0/18」を表示。台帳を開き、既存18行と未入力項目の表示を確認。
- 概要の不足スキル98件を表示。確認した画面に取得失敗表示なし。
- デプロイログに認証・通知APIの200、healthzの200を確認。ルート `/` の404はAPIにトップページがないためで、監視は `/healthz` を使用。

### 利用再開時の注意

移行前のセッションは失効するため再ログインが必要。独立確認者R19の任命とリスク確認は、新しい権限・確認ルールに従って再確認する。今回の変更前に保管され、スナップショットのない案件については、過去時点の完全な復元を保証しない。

復旧手順の自動検証は分離したPostgreSQL 13/16で実施。本番Neonでは移行前の独立ブランチを確保し、実際の本番接続切替による復旧訓練は行っていない。
