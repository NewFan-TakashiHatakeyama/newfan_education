"""事業PJ台帳の共通ルール。

原本の点検数式が横断的に使う概念を、1箇所だけに置く。

- **管理基準日（AsOfDate）**: 原本は名前付き範囲 `AsOfDate = '00_前提・使い方'!$B$5`
  を持ち、17!W・18!AG/AQ・22!O・29!S/AD・30!M・31!Q・34!P・35!R・06!S/U・16!S の
  ほぼ全ての点検数式がこれを参照して「未来日」「期限超過」を判定する。
  案件ごとに設定でき、未設定ならサーバの当日を使う。
- **PersonID**: 原本の Owner PersonID / 承認者PersonID / 確認者PersonID は、
  本システムでは `users.user_id` と同一とする。実名（06!G・17!G・28!D・29!O）は
  自由記述の別列で、user_id とは混ぜない。
"""
from __future__ import annotations

import re
from datetime import date, datetime, timezone

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# 管理基準日の出所。案件で設定されていれば venture、していなければサーバ当日。
AS_OF_FROM_VENTURE = "venture"
AS_OF_FROM_TODAY = "today"


def today() -> date:
    return datetime.now(timezone.utc).date()


def as_of(venture: dict) -> tuple[date, str]:
    """案件の管理基準日と、その出所を返す。

    原本のテンプレート値（2026-09-06）へはフォールバックしない。原本の値は
    ブックの作成日であって、この案件の基準日ではないため。
    """
    raw = (venture.get("asOfDate") or "").strip()
    parsed = parse_date(raw)
    if parsed is not None:
        return parsed, AS_OF_FROM_VENTURE
    return today(), AS_OF_FROM_TODAY


def parse_date(value: str | None) -> date | None:
    """YYYY-MM-DD だけを受ける。書式が違えば None。"""
    text = (value or "").strip()
    if "T" in text:
        timestamp = parse_timestamp(text)
        return timestamp.date() if timestamp else None
    if not DATE_PATTERN.match(text):
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def parse_timestamp(value: str | None) -> datetime | None:
    """Events require an explicit UTC offset; date-only legacy values stay unverified."""
    try:
        text = (value or "").strip()
        if "T" not in text:
            return None
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo is not None else None
    except ValueError:
        return None


def is_future(value: str | None, basis: date) -> bool:
    """管理基準日より後の日付か。原本の `INT(値) > INT(AsOfDate)` に相当。"""
    parsed = parse_date(value)
    return parsed is not None and parsed > basis


def is_before(earlier: str | None, later: str | None) -> bool:
    """両方が日付として読めて、かつ earlier < later のときだけ True。"""
    first = parse_date(earlier)
    second = parse_date(later)
    return first is not None and second is not None and first < second
