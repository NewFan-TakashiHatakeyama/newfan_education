"""Decide which primary sources a skill needs and whether the registry facts are fresh enough.

Matches the registry topics against the skill definition (definition, Lv1-3,
evidence, notes) only. Hits that occur solely in the related task rows are
reported as weak "hints". Every matched entry is returned in full (facts, cards,
scope, not_covered, unverified, urls, origin, events) so that `harness plan` can
write them to _sources.json and the model never reads the whole registry.
Stale = checked_at older than max_age_days, or an event date has passed. Stale
does not block production: the facts are transcribed with their check date and
the re-check is recorded in 01 §2 and the catalog.
Python 3.10+, standard library only.
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
REGISTRY = BASE / 'references' / 'source-registry.json'
# Topics that have no registry entry. Reported as "unregistered": the material
# must say 未確認・要法務確認 unless the user asks for new primary-source work.
EXTRA_TOPICS = {
    'medical-law': ['医療機器', '薬機法', '医療法'], 'finance-law': ['金融商品取引法', '金商法', '銀行法', '保険業法'],
    'employment-law': ['労働基準法', '採用選考', '労働者派遣', '職業安定法'],
    'copyright': ['著作権', '知的財産', '生成物の権利'], 'consumer': ['消費者契約法', '景品表示法', '景表法', '特定商取引法', '優良誤認'],
    'security-frameworks': ['OWASP', 'MITRE', 'ISO/IEC 27001', 'NIST SP 800'],
}
LEGAL_WORDS = ['個人情報保護法', '個人情報', 'GDPR', 'AI Act', 'AI法', '法令', '法規', '法律', '規制', 'コンプライアンス', '法務', '著作権', '業法', 'プライバシー']
TASK_COLS = 'DEFIJQ'  # 名・内容・成果物・完了条件・適用条件・AI/人境界


def skill_text(source, skill_id):
    skill = next((s for s in source['skills'] if s['id'] == skill_id), None)
    if not skill:
        raise ValueError('Unknown skill: ' + skill_id)
    primary = '\n'.join(str(skill.get(k, '') or '') for k in ('name', 'definition', 'Lv1', 'Lv2', 'Lv3', 'evidence', 'notes'))
    tasks = set(str(skill.get('tasks', '')).replace(' ', '').split(',')) - {''}
    task_parts = []
    for name, rows in source['sheets'].items():
        if name.startswith('02_'):
            for row in rows:
                c, n = row['cells'], row['row']
                if c.get(f'A{n}') in tasks:
                    task_parts.append(' '.join(str(c.get(f'{col}{n}', '') or '') for col in TASK_COLS))
    return skill, primary, '\n'.join(task_parts)


def entry_status(entry, today, max_age):
    age = (today - date.fromisoformat(entry['checked_at'])).days
    passed = [ev for ev in entry.get('events', []) if date.fromisoformat(ev['date']) <= today]
    reasons = []
    if age > max_age:
        reasons.append(f'checked_at {entry["checked_at"]} is {age} days old (> {max_age})')
    for ev in passed:
        reasons.append(f'event {ev["date"]}: {ev["what"]}')
    return age, reasons


def check(source, skill_id, today=None, registry_path=REGISTRY, include_entries=True):
    registry = json.loads(Path(registry_path).read_text(encoding='utf-8'))
    today = date.fromisoformat(today) if today else date.today()
    skill, primary, task_text = skill_text(source, skill_id)
    max_age = registry.get('max_age_days', 120)
    matched, hints, unregistered = [], [], []
    for topic, words in registry['topics'].items():
        strong = [w for w in words if w in primary]
        weak = [w for w in words if w in task_text and w not in strong]
        if not strong and not weak:
            continue
        entry = next((e for e in registry['entries'] if e['id'] == topic), None)
        if not entry:
            unregistered.append({'topic': topic, 'hits': strong or weak})
            continue
        age, reasons = entry_status(entry, today, max_age)
        item = {'id': topic, 'title': entry['title'], 'checked_at': entry['checked_at'], 'age_days': age, 'stale': bool(reasons),
                'stale_reasons': reasons, 'hits': strong or weak, 'match': 'skill' if strong else 'tasks-only', 'access': entry['access'],
                'scope': entry.get('scope', ''), 'not_covered': entry.get('not_covered', ''), 'facts': len(entry['facts'])}
        if include_entries:
            item.update({'urls': entry['urls'], 'facts_text': entry['facts'], 'cards': entry.get('cards', []), 'unverified': entry.get('unverified', []),
                         'origin': entry.get('origin', []), 'events': entry.get('events', []), 'notes': entry.get('notes', [])})
        (matched if strong else hints).append(item)
    for topic, words in EXTRA_TOPICS.items():
        hits = [w for w in words if w in primary]
        if hits:
            unregistered.append({'topic': topic, 'hits': hits})
    legal = [w for w in LEGAL_WORDS if w in primary]
    stale = [m['id'] for m in matched if m['stale']]
    if matched and not stale:
        action = 'matched entries: transcribe facts/cards with their check date; facts not in scope -> fetch the entry urls with --grep, or write 未確認'
    elif matched:
        action = f'stale entries {stale}: still transcribe with the check date; record the re-check need in 01 §2 and catalog open_items (registry maintenance is separate)'
    else:
        action = 'no registry topic matched in the skill text; write legal statements only as 未確認・要法務確認 unless the user asks for new primary-source work'
    return {'skill': skill_id, 'name': skill['name'], 'legal_content': bool(legal), 'legal_words': legal, 'max_age_days': max_age,
            'registry_maintained_at': registry.get('maintained_at'), 'matched': matched, 'hints': hints, 'unregistered': unregistered,
            'unregistered_rule': '教材で扱う場合は「未確認・要法務確認」と書く。一次資料の新規取得はユーザーが依頼した場合のみ',
            'action': action}


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path)
    p.add_argument('skill_id')
    p.add_argument('--today')
    p.add_argument('--brief', action='store_true', help='omit the entry bodies')
    args = p.parse_args()
    result = check(json.loads(args.source.read_text(encoding='utf-8')), args.skill_id, args.today, include_entries=not args.brief)
    print(json.dumps(result, ensure_ascii=False, indent=2))
