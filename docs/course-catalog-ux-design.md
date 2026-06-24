# コースカタログ（AI講座）UI/UX 設計

> Udemy を参考にしつつ、**動画ではなくユーザーが画面にコードを入力して学ぶ**ハンズオン型の
> AI 講座カタログを、既存の Newfan Education（AI Field Ready）基盤の上に設計する。

---

## 1. 背景と現状（コード調査の結論）

### 既存システムの要点
- 既存は **B2B SES 人材育成プラットフォーム**。`ロードマップ → 演習 → AIレビュー/メンター承認 → 実務証跡 → 案件提案` という縦の流れが中心。
- 学習の最小単位はフラットに存在し、**「コース」という束ねる概念が無い**。
  - `CurriculumVersion`（= MDX 1レッスン: slug / version / title / mdx_path / skill_tags / difficulty / estimated_minutes / published）
  - `Exercise`（= コード入力課題: kind = `notebook | sql | rag | ocr` / prompt / starterCode / metadata）
  - `Roadmap` / `RoadmapItem`（受講者に割り当てる順序付き学習パス）
  - `Submission` / `ReviewResult` / `EvidenceItem`
- 学習者ホーム `/learner/learn` は「本日の演習」ダッシュボードで、**カタログ・検索・コース一覧は無い**。
- `/learn/[curriculumSlug]/[lessonSlug]` のルートとテンプレート（`LearningLessonExperience` / `LearningExerciseWorkspace`）は**スキャフォルドのみ**で実データ未接続。
- **コード入力 UX は既に存在**: `LearnerExercisePage`（`/learner/exercises/[exerciseId]`）が `runExercise` / `submitExercise` を呼び、`pyodide`（ブラウザ）/ `docker_sandbox` で実行 → コンソール表示 → AIレビュー。
- コンテンツは `content/curriculum/<slug>/*.mdx`。
- ナビゲーションはロール別（learner / company / mentor / admin）の左サイドバー（`AppShell`）。

### ギャップ（今回つくるもの）
1. **コースという束ね（Course → Section → Lesson）** が無い。
2. **カタログ／検索／コース詳細（カリキュラム一覧）** の画面が無い。
3. コース単位の**受講登録（enrollment）と進捗**が無い。

> 既存の「コード実行・AIレビュー・実務証跡」資産はそのまま再利用し、その**上にカタログ層を載せる**方針。

---

## 2. 情報設計（ドメインモデル）

新しい最上位の束ね単位 **Course** を導入する。

```
Course（コース / 講座）
 ├─ id, slug, title, subtitle, category, level(入門|中級|実践)
 ├─ tags[], heroSummary, description
 ├─ outcomes[]（このコースで学べること）
 ├─ targetAudience[]（対象者）, prerequisites[]（前提）
 ├─ instructor, rating, enrolledCount, updatedAt, published
 ├─ totalLessons, totalExercises, estimatedHours
 └─ sections[]（セクション）
       └─ lessons[]（レッスン = 学習の1単位）
            ├─ kind: "reading"（解説のみ）| "code"（コード演習あり）
            ├─ contentRef → 既存 MDX（content/curriculum/...）
            ├─ exerciseId? → 既存 Exercise（notebook/sql/rag/ocr）
            ├─ skillTags[], estimatedMinutes
            └─ isPreview（未受講でも閲覧可）
```

### 既存モデルとのマッピング
| 新概念 | 既存資産 |
|---|---|
| `Lesson.contentRef` | 既存 MDX（`content/curriculum/...`） |
| `Lesson.exerciseId` | 既存 `Exercise`（notebook / sql / rag / ocr） |
| Course の `sections[].lessons[]` | 既存 `CurriculumVersion` + `Exercise` を順序付きでグルーピングしたもの |
| 受講登録・進捗 | 新 `Enrollment` + 既存 `ProgressEvent`（courseId を追加） |
| 修了の価値 | 既存 `EvidenceItem`（実務証跡）へロールアップ |

### B2C カタログ と B2B ロードマップの関係（重要な設計判断）
- 既存は強く B2B（企業がロードマップを割り当てる）。今回の要望は Udemy 的な**学習者の自己選択**。
- **両立させる**: `Course` = 公開カタログ＋順序付きレッスン。`Enrollment` = ユーザーごとの受講・進捗。
  既存 `Roadmap` は「キュレーションされた Course の並び」と捉え、**企業割り当て**でも**自己受講**でも同じ Course/Enrollment 基盤に乗る。
- → 学習者は自分でコースを選べる。企業は引き続きロードマップ（=複数コースの推奨順）を割り当てられる。

---

## 3. ルーティング（Next.js App Router）

```
/courses                              コースを探す（カタログ: 検索＋フィルタ＋グリッド）   ← Udemy「Find Courses」
/courses?q=&category=&level=&sort=     検索結果（同一ページのクエリ）
/courses/[courseSlug]                 コース詳細（ランディング＋カリキュラム一覧）        ← Udemy コースページ
/learn/[courseSlug]                   受講プレイヤー入口（最初／続きのレッスンへリダイレクト）
/learn/[courseSlug]/[lessonSlug]      レッスン・ワークスペース（解説＋コードエディタ）      ← テンプレート再利用
/learner/my-courses                   マイラーニング（受講中／ウィッシュ／修了）           ← Udemy「My learning」
```

- 既存 `/learner/learn`（本日の演習ホーム）は維持し、入口として「コースを探す」「マイコース」導線を追加。
- 既存 `/learn/[curriculumSlug]/[lessonSlug]` は `courseSlug/lessonSlug` 体系に寄せて実装する。

---

## 4. 画面別 UI/UX

### 4.1 カタログ `/courses`（コースを探す）
- **検索バー（大）**＋「急上昇」候補のドロップダウン（Udemy のトレンド候補を踏襲。例: `RAG`, `LLMアプリ`, `pandas`, `FastAPI`）。
- **カテゴリ・チップ列**: 生成AI基礎 / LLMアプリ開発 / RAG / データ分析(SQL・pandas) / Python API / 評価・MLOps / OCR・文書AI（`skill_tags` と `kind` から導出）。
- **フィルタ（左サイドバー）**: レベル、所要時間、トピック、評価、難易度。
- **コースカード・グリッド**: サムネ（グラデ）／タイトル／講師／評価／レッスン数／時間／レベルバッジ／タグ／「ベストセラー」「最高評価」バッジ。CTA = 「詳細を見る」/「学習を続ける」（受講中なら進捗％）。
- **並び替え**: 人気順 / 新着 / 評価順。
- ゼロ件状態: 近いタグの提案を表示。

### 4.2 コース詳細 `/courses/[courseSlug]`（コースランディング）
Udemy 同様の 2 カラム。**右カラムは「動画プレビュー＋価格」ではなく「受講開始カード」に置き換える**（無料・コード学習プロダクトのため）。

- **左（メイン）**
  - パンくず（カテゴリ > サブ > コース）
  - タイトル＋サブタイトル、評価、受講者数、最終更新、言語、レベル
  - **「このコースで学べること」** グリッド（outcomes）
  - **「カリキュラム」アコーディオン**: セクション → レッスン。各行に種別アイコン（📖 解説 / ⌨️ コード演習）、タイトル、所要分、プレビュー可否。セクション見出しにレッスン数＋合計時間。
    → **ユーザーが求めた「コース別にカリキュラムが整理されたページ」はここ。**
  - 前提条件、対象者、説明
- **右（スティッキー受講カード）**
  - 「このコースを開始」/「受講を続ける」（受講中は進捗％・続きのレッスン）
  - メタ: ◯レッスン / ◯コード演習 / 推定◯時間 / 修了証
  - **「コードを書いて学ぶ」バッジ**（動画時間の代わり。ハンズオンであることを明示）
  - マイリストに追加 / ウィッシュリスト

### 4.3 レッスン・ワークスペース `/learn/[courseSlug]/[lessonSlug]` ← 中核
**動画の代わりにコードを書く**、IDE 風 3 ペイン。

- **左レール（折りたたみ可）= コースのカリキュラム／目次**: セクション＋レッスンを完了チェック付きで表示。現在地ハイライト。コース内移動（Udemy プレイヤー左サイドバー相当）。
- **中央 = レッスン本文＋課題**（上）→ **コードエディタ＋コンソール**（下）
  - `reading` レッスン: MDX 解説＋「次へ」。
  - `code` レッスン: 課題説明（概念・タスク・入出力例・評価ルーブリック）＋コードエディタ＋コンソール＋ `▶実行` / `提出`。`LearnerExercisePage` のワークスペースを再利用。
- **右（折りたたみ可）= AIガイド／ヒント**: ヒント、提出前チェック、参照。テンプレートに既存。
- **下部バー**: ◀ 前へ / 次へ ▶、進捗バー、「完了にする」。

**コードレッスンの学習ループ**:
`課題を読む → エディタに記述 → ▶実行(pyodide/docker) → コンソールで確認 → 提出 → AIレビュー → 合格で次へ`（合格すると実務証跡が加算され、既存 B2B 価値に接続）。

### 4.4 マイラーニング `/learner/my-courses`
- タブ: 受講中 / ウィッシュリスト / 修了。
- 「続きから」カード（進捗リング付き）。Udemy の「My learning」を踏襲。

---

## 5. 検索の設計
- 入口: カタログの検索バー＋トップバーの横断検索（既存を流用）。
- クエリ: `q`, `category`, `level`, `tags`, `sort`, `duration`。
- バックエンド: `GET /courses?q=&category=&level=&tag=&sort=&page=`。title / subtitle / tags / outcomes の全文検索。
- 急上昇: よく使われるクエリを事前集計（Udemy の「急上昇」相当）。
- ゼロ件: 近接タグの提案＋人気コースを表示。

---

## 6. 受講登録・進捗モデル
```
Enrollment {
  userId, courseId,
  status: not_started | in_progress | completed,
  startedAt, lastLessonSlug,
  completedLessonSlugs[], progressRate
}
```
- レッスン完了 = `reading` は閲覧、`code` は演習合格（AIレビュー pass）。
- 既存 `ProgressEvent`（lesson_started / lesson_completed）に `courseId` を付与して再利用。
- コース修了 → 修了証＋実務証跡へロールアップ。

---

## 7. API 追加
```
GET  /courses                              一覧・検索（フィルタ／並び替え／ページング）
GET  /courses/trending                     急上昇候補
GET  /courses/categories                   カテゴリツリー
GET  /courses/{slug}                       詳細（sections＋lessons 含む）
POST /courses/{slug}/enroll                受講登録
GET  /me/enrollments                       マイコース＋進捗
GET  /courses/{slug}/lessons/{lessonSlug}  レッスン本文＋演習バインディング
POST /progress/events                      （既存）courseId を拡張
```
レッスンのコード部分は既存 `GET /exercises/{id}` を再利用。

---

## 8. 再利用マップ（既にあるもの）
| 機能 | 既存資産 |
|---|---|
| コードエディタ／実行／提出／コンソール | `LearnerExercisePage`, `runExercise`/`submitExercise`, pyodide/docker |
| レッスン 3 ペインの骨格 | `LearningLessonExperience` / `LearningExerciseWorkspace`（実データ接続が必要） |
| AIレビュー／実務証跡／ルーブリック | 既存サービス |
| コンテンツ MDX パイプライン | `content/curriculum` |
| UI キット（カード／チップ／ヒーロー／タブ／フィルタチップ／アイコン） | `components/ui`, `components/learner` |

---

## 9. 実装フェーズ
- **Phase 1（カタログ骨格・閲覧のみ）**: Course モデル＋既存レッスン/演習を束ねた 4〜6 コースをシード。`/courses` カタログ（検索・フィルタ）。`/courses/[slug]` 詳細（カリキュラム・アコーディオン）。
- **Phase 2（学習プレイヤー）**: enrollment ＋ `/learn/[slug]/[lessonSlug]` の 3 ペインを実 MDX・実演習に接続。進捗トラッキング。マイコース。
- **Phase 3（仕上げ）**: 急上昇検索、カテゴリ、評価、修了証、実務証跡ロールアップ、レコメンド。

---

## 10. 設計上の前提（要確認ポイント）
- カタログは **学習者の自己選択（Udemy 型）** とし、既存の企業ロードマップ割り当てと**共存**させる前提で設計。
- コースは**無料／プラン内**を想定し、Udemy の価格カードは「受講開始カード」に置換。課金が必要なら右カードに価格 UI を足すだけで拡張可能。
