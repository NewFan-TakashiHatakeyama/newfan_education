"""工程マスタのスキルと、学習カリキュラムのコースの対応表。

工程マスタは原本07のスキル辞書（S001〜S106）を語彙とし、学習側は
`course_seed.default_courses()` のコースを持つ。両者を結ぶデータがどこにも無く、
スキル不足からコースへ飛ぶ導線（`/courses?q=<スキル名>`）は106件すべてが0件だった。

**この表はマスタJSONに入れない。** マスタJSONは原本の抽出結果と完全一致することを
受入試験 IT12 が検査しており、原本に無いデータを1件でも足すと落ちる。対応表は
原本ではなく本サービスの都合なので、コード側に版管理して置く。

**対応が無いことも答えである。** 現行のカタログは5コースしかなく、106スキルのうち
対応づけられるのは10件だけ。残る96件は「学習コンテンツが無い」のであって、
検索語を工夫すれば見つかるものではない。画面では対応の有無をそのまま出す。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SkillCourseLink:
    skill_id: str
    course_slug: str
    #: そのコースを終えて到達を主張できる原本07のLv。
    #: 現行カタログは入門〜中級で、Lv2「指導なしで遂行」を主張できる根拠が無いため全件1。
    covers_level: int
    #: 対応の限界。過大な主張をしないための但し書き。
    note: str


SKILL_COURSE_LINKS: tuple[SkillCourseLink, ...] = (
    SkillCourseLink(
        "S054", "genai-foundations", 1,
        "生成AI・基盤モデルの基礎。モデルの選定基準や権利の判断は扱わない。",
    ),
    SkillCourseLink(
        "S064", "genai-foundations", 1,
        "プロンプト設計と構造化出力。評価による較正までは扱わない。",
    ),
    SkillCourseLink(
        "S024", "genai-foundations", 1,
        "Pythonとデータ処理の基礎部分のみ。大規模データの処理設計は未収載。",
    ),
    SkillCourseLink(
        "S061", "rag-eval-bootcamp", 1,
        "RAG設計と検索評価。ACL・鮮度・削除反映の設計は未収載。",
    ),
    SkillCourseLink(
        "S070", "rag-eval-bootcamp", 1,
        "LLM評価設計の入門。凍結セットの運用と独立評価は未収載。",
    ),
    SkillCourseLink(
        "S059", "rag-eval-bootcamp", 1,
        "評価セット構築の入門。母集団設計とスライス分析は未収載。",
    ),
    SkillCourseLink(
        "S037", "fastapi-business-api", 1,
        "API設計・実装と認証認可の基礎。テナント分離と権限設計は未収載。",
    ),
    SkillCourseLink(
        "S038", "fastapi-business-api", 1,
        "LLMアプリケーション層の実装。フォールバック設計は未収載。",
    ),
    SkillCourseLink(
        "S025", "sql-data-analytics", 1,
        "SQLの集計まで。データモデリングは未収載。",
    ),
    SkillCourseLink(
        "S055", "sql-data-analytics", 1,
        "探索的データ分析の入門。データ品質の管理設計は未収載。",
    ),
)


def courses_for_skill(skill_id: str) -> list[SkillCourseLink]:
    return [link for link in SKILL_COURSE_LINKS if link.skill_id == skill_id]


def mapped_skill_ids() -> set[str]:
    return {link.skill_id for link in SKILL_COURSE_LINKS}
