"""Seed catalog courses for Phase 1 (browse-only).

Courses group existing curriculum MDX and exercises into browsable units. The
exercise ids referenced here match the demo exercises seeded by
``PostgresB2BRepository`` (``ex-notebook-001`` etc.), and ``content_ref`` points
at the checked-in MDX under ``content/curriculum``. Reading lessons whose MDX is
not authored yet leave ``content_ref`` as ``None`` until Phase 2 wires the player.
"""

from __future__ import annotations

from domain.models import Course, CourseLesson, CourseSection

_FASTAPI_MDX = "content/curriculum/python-fastapi/intro-v1.mdx"


def default_courses() -> list[Course]:
    return [
        Course(
            id="course-genai-foundations",
            slug="genai-foundations",
            title="生成AI基礎: プロンプトからアプリまで",
            subtitle="生成AIの全体像・プロンプト設計から、出力の構造化・簡易検索までをコードで学ぶ",
            category="生成AI基礎",
            level="beginner",
            instructor="矢野 哲平",
            summary=(
                "生成AIの仕組みと使いどころを理解し、プロンプト設計・出力の構造化・"
                "簡易検索（RAGの第一歩）をハンズオンで身につける入門コース。"
            ),
            description=(
                "生成AIの基本概念から、業務でのAI活用に必要なプロンプト設計・出力の構造化・"
                "簡易検索（RAGの第一歩）までを段階的に学びます。動画ではなく、各レッスンで実際に"
                "コードを書いて実行・提出します。"
            ),
            sections=[
                CourseSection(
                    title="生成AIの全体像",
                    lessons=[
                        CourseLesson(
                            lesson_slug="what-is-genai",
                            title="生成AIとは何か",
                            kind="reading",
                            estimated_minutes=12,
                            skill_tags=["genai.basics", "llm.fundamentals"],
                            content_ref="content/curriculum/genai-foundations/01-what-is-genai.mdx",
                            is_preview=True,
                        ),
                        CourseLesson(
                            lesson_slug="model-landscape",
                            title="主要サービスと使い分け",
                            kind="reading",
                            estimated_minutes=12,
                            skill_tags=["genai.services", "llm.selection"],
                            content_ref="content/curriculum/genai-foundations/02-model-landscape.mdx",
                        ),
                    ],
                ),
                CourseSection(
                    title="プロンプトを設計する",
                    lessons=[
                        CourseLesson(
                            lesson_slug="prompt-design",
                            title="プロンプト設計の基本",
                            kind="reading",
                            estimated_minutes=15,
                            skill_tags=["prompt.design"],
                            content_ref="content/curriculum/genai-foundations/03-prompt-design.mdx",
                        ),
                        CourseLesson(
                            lesson_slug="build-prompt",
                            title="プロンプトを組み立てる関数を実装する",
                            kind="code",
                            estimated_minutes=25,
                            skill_tags=["prompt.design", "python.functions"],
                            content_ref="content/curriculum/genai-foundations/04-build-prompt.mdx",
                            exercise_id="ex-genai-prompt-001",
                        ),
                    ],
                ),
                CourseSection(
                    title="コードから生成AIを使う",
                    lessons=[
                        CourseLesson(
                            lesson_slug="structured-output",
                            title="生成AIの出力を構造化データにする",
                            kind="code",
                            estimated_minutes=25,
                            skill_tags=["genai.output", "python.parsing"],
                            content_ref="content/curriculum/genai-foundations/05-structured-output.mdx",
                            exercise_id="ex-genai-structured-001",
                        ),
                        CourseLesson(
                            lesson_slug="retrieval-basics",
                            title="簡易検索でコンテキストを選ぶ（RAGの第一歩）",
                            kind="code",
                            estimated_minutes=30,
                            skill_tags=["rag.basics", "python.algorithms"],
                            content_ref="content/curriculum/genai-foundations/06-retrieval-basics.mdx",
                            exercise_id="ex-genai-retrieval-001",
                        ),
                    ],
                ),
            ],
            tags=["生成AI", "プロンプト", "RAG", "Python", "入門"],
            outcomes=[
                "生成AIの仕組みと得意・不得意を説明できる",
                "主要サービスを業務で使い分けられる",
                "再利用できるプロンプトを設計・実装できる",
                "生成AIの出力を構造化データに変換できる",
                "簡易検索でコンテキストを選ぶ（RAGの第一歩）を実装できる",
            ],
            target_audience=[
                "AI開発をこれから始める方",
                "業務へのAI導入を検討する担当者",
                "非エンジニアからの転向者",
            ],
            prerequisites=["基本的なPC操作", "Pythonの初歩（変数・関数）に触れたことがあると望ましい"],
            rating=4.5,
            rating_count=520,
            enrolled_count=2100,
            is_bestseller=True,
            updated_at="2026-05-01T00:00:00+00:00",
        ),
        Course(
            id="course-rag-eval-bootcamp",
            slug="rag-eval-bootcamp",
            title="RAG評価ハンズオン入門",
            subtitle="検索精度をHit@K / MRRで測り、改善示唆をコードで導く",
            category="LLMアプリ / RAG",
            level="intermediate",
            instructor="矢野 哲平",
            summary="RAGの検索精度を定量評価し、改善ループを回す実務スキルを身につける。",
            description=(
                "RAG（検索拡張生成）の品質を評価する指標を実装し、評価レポートとして"
                "まとめるまでを学びます。各演習はブラウザ上でコードを書いて実行します。"
            ),
            sections=[
                CourseSection(
                    title="評価の基礎",
                    lessons=[
                        CourseLesson(
                            lesson_slug="why-evaluate-rag",
                            title="RAG評価とは何か",
                            kind="reading",
                            estimated_minutes=8,
                            skill_tags=["rag.eval"],
                            is_preview=True,
                        ),
                        CourseLesson(
                            lesson_slug="retrieval-metrics",
                            title="検索精度を評価する",
                            kind="code",
                            estimated_minutes=25,
                            skill_tags=["rag.eval", "python.data"],
                            exercise_id="ex-rag-001",
                        ),
                    ],
                ),
                CourseSection(
                    title="改善ループの実践",
                    lessons=[
                        CourseLesson(
                            lesson_slug="aggregate-metrics",
                            title="メトリクスを集計する",
                            kind="code",
                            estimated_minutes=20,
                            skill_tags=["python.data"],
                            exercise_id="ex-notebook-001",
                        ),
                        CourseLesson(
                            lesson_slug="evaluation-report",
                            title="評価レポートをまとめる",
                            kind="reading",
                            estimated_minutes=15,
                            skill_tags=["rag.eval"],
                        ),
                    ],
                ),
            ],
            tags=["RAG", "評価", "LLM", "Python"],
            outcomes=[
                "Hit@K / MRR を自分で実装できる",
                "検索結果の改善ループを回せる",
                "評価レポートを作成し実務証跡につなげられる",
            ],
            target_audience=["LLMアプリ開発者", "PoC検証を担当するエンジニア"],
            prerequisites=["Pythonの基礎", "リスト・辞書の操作"],
            rating=4.6,
            rating_count=312,
            enrolled_count=1240,
            is_bestseller=True,
            updated_at="2026-05-20T00:00:00+00:00",
        ),
        Course(
            id="course-fastapi-business-api",
            slug="fastapi-business-api",
            title="FastAPIで作る業務API",
            subtitle="入出力検証とテストまで、現場で通用するAPIを実装する",
            category="Python API",
            level="beginner",
            instructor="高橋 健",
            summary="FastAPIでCRUD APIを実装し、入力検証とテストの基礎を固める。",
            description=(
                "FastAPIの基礎から、業務システム向けのバックエンドAPI実装までを"
                "段階的に学びます。各レッスンで実際にコードを書いて動作を確認します。"
            ),
            sections=[
                CourseSection(
                    title="はじめてのFastAPI",
                    lessons=[
                        CourseLesson(
                            lesson_slug="fastapi-intro",
                            title="FastAPI入門",
                            kind="reading",
                            estimated_minutes=35,
                            skill_tags=["python.api.fastapi"],
                            content_ref=_FASTAPI_MDX,
                            is_preview=True,
                        ),
                    ],
                ),
                CourseSection(
                    title="APIを実装する",
                    lessons=[
                        CourseLesson(
                            lesson_slug="implement-endpoint",
                            title="エンドポイントを実装する",
                            kind="code",
                            estimated_minutes=30,
                            skill_tags=["python.api.fastapi"],
                            exercise_id="ex-notebook-001",
                        ),
                    ],
                ),
            ],
            tags=["FastAPI", "Python", "API設計", "入門"],
            outcomes=[
                "FastAPIでエンドポイントを実装できる",
                "入出力のバリデーションを設計できる",
                "テストを分割して書ける",
            ],
            target_audience=["バックエンド開発を始める方", "案件参画前の若手エンジニア"],
            prerequisites=["Pythonの基礎文法"],
            rating=4.4,
            rating_count=188,
            enrolled_count=980,
            updated_at="2026-04-15T00:00:00+00:00",
        ),
        Course(
            id="course-sql-data-analytics",
            slug="sql-data-analytics",
            title="SQLで学ぶデータ集計",
            subtitle="学習進捗データを題材に、集計クエリを書けるようになる",
            category="データ分析",
            level="beginner",
            instructor="佐藤 みき",
            summary="実データを題材に、集計・可視化につながるSQLを手を動かして習得する。",
            description=(
                "受講者の学習進捗データを題材に、集計クエリの考え方と書き方を学びます。"
                "各演習はブラウザ上でSQLを書いて実行します。"
            ),
            sections=[
                CourseSection(
                    title="集計の基本",
                    lessons=[
                        CourseLesson(
                            lesson_slug="aggregation-basics",
                            title="SQL集計の考え方",
                            kind="reading",
                            estimated_minutes=12,
                            skill_tags=["sql.aggregate"],
                            is_preview=True,
                        ),
                        CourseLesson(
                            lesson_slug="completion-rate-query",
                            title="完了率を算出するクエリ",
                            kind="code",
                            estimated_minutes=25,
                            skill_tags=["sql.aggregate"],
                            exercise_id="ex-sql-001",
                        ),
                    ],
                ),
            ],
            tags=["SQL", "データ分析", "集計", "入門"],
            outcomes=[
                "GROUP BY と集計関数を使いこなせる",
                "完了率などの指標をSQLで算出できる",
            ],
            target_audience=["データ分析を始める方", "進捗指標を扱う運用担当"],
            prerequisites=["テーブルとカラムの基本概念"],
            rating=4.7,
            rating_count=96,
            enrolled_count=640,
            is_top_rated=True,
            updated_at="2026-05-10T00:00:00+00:00",
        ),
        Course(
            id="course-document-ai-ocr",
            slug="document-ai-ocr",
            title="文書AI・OCR実践",
            subtitle="OCR抽出結果を構造化JSONに変換する実務パターンを学ぶ",
            category="文書AI / OCR",
            level="advanced",
            instructor="田中 涼",
            summary="請求書などの文書をOCRで読み取り、構造化データに変換する実務スキル。",
            description=(
                "OCRで抽出したテキストを、業務で使える構造化JSONに変換する手法を学びます。"
                "各演習はブラウザ上でコードを書いて実行します。"
            ),
            sections=[
                CourseSection(
                    title="OCRと構造化",
                    lessons=[
                        CourseLesson(
                            lesson_slug="document-ai-overview",
                            title="文書AIの全体像",
                            kind="reading",
                            estimated_minutes=10,
                            skill_tags=["ocr.basics"],
                            is_preview=True,
                        ),
                        CourseLesson(
                            lesson_slug="invoice-to-json",
                            title="請求書を構造化JSONにする",
                            kind="code",
                            estimated_minutes=30,
                            skill_tags=["ocr.structuring"],
                            exercise_id="ex-ocr-001",
                        ),
                    ],
                ),
            ],
            tags=["OCR", "文書AI", "構造化", "実践"],
            outcomes=[
                "OCR抽出結果を構造化JSONに変換できる",
                "抽出フォーマットの妥当性を検証できる",
            ],
            target_audience=["文書処理を自動化したいエンジニア"],
            prerequisites=["Pythonの基礎", "辞書・JSONの操作"],
            rating=4.3,
            rating_count=54,
            enrolled_count=410,
            updated_at="2026-03-28T00:00:00+00:00",
        ),
    ]
