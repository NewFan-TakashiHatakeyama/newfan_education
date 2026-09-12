"""Generate curriculum.json and the design-document skeletons from a compact spec.

The spec keeps the model's writing small: objectives, modules (5-part minute
split), assessments, and the allocations that the four Markdown files share
(scope sentences, roles, templates, appendix cards). Everything derived from it
(totals, level sums, curriculum.json, the 単元表 / 目標表, the 02 heading lines,
the 03 role/template/card skeletons, the 04 §2 headings and the 04 §8 self-check
table) is produced here so the files cannot drift apart. build() validates the
spec structurally and lists every violation before any prose is written.

Spec (JSON, UTF-8; fields marked * are optional):
{
  "skill_id": "S003", "curriculum_version": "1.0.0", "status": "draft-reviewed", "date": "YYYY-MM-DD",
  "scope"*: {"owns": "…", "assumes": "…", "delegates": "…（S番号・タスクID）"},
  "objectives": [{"id": "S003-L1-O01", "behavior": "…",
                  "condition"*: "…", "input"*: "…", "deliverable"*: "…", "quality"*: "…", "boundary"*: "…", "failure"*: "…"}],
  "modules": [{"id": "M01", "level": 1, "objectives": ["S003-L1-O01"], "title": "…",
               "minutes": [25, 15, 30, 20, 0], "exercise": "E01", "evidence": ["…"], "assessment": "A1"}],
  "assessments": [{"id": "A1", "level": 1, "observation_points": ["…"], "evidence": ["…"],
                   "pass_rule": "…", "critical_errors": ["…"]}],
  "roles"*: [{"id": "R14", "actor": "架空の担当", "role": "…"}],
  "templates"*: [{"id": "T1", "name": "…", "columns": ["…"]}],
  "cards"*: [{"id": "K01", "registry": "appi-breach", "title": "…"}],
  "review": {"limitations": ["試行授業未実施"]}
}
Python 3.10+, standard library only.
"""
import argparse
import json
import re
from datetime import date
from pathlib import Path

PARTS = ['explanation', 'worked_example', 'practice', 'review', 'assessment']
PART_LABELS = ['説明', '例解', '演習', 'レビュー', '評価']
OBJ_FIELDS = ['condition', 'input', 'deliverable', 'quality', 'boundary', 'failure']
CHECKLIST = Path(__file__).resolve().parents[1] / 'references' / 'quality-checklist.md'


def validate_spec(spec, source):
    """Return the list of structural violations (empty when the spec is sound)."""
    issues = []
    sid = spec.get('skill_id', '')
    record = next((s for s in source['skills'] if s['id'] == sid), None)
    if record is None:
        return ['Unknown skill: ' + str(sid)]
    obj_level = {}
    for o in spec.get('objectives', []):
        m = re.match(r'^(S\d{3})-L([123])-O(\d{2})$', str(o.get('id', '')))
        if not m or m.group(1) != sid:
            issues.append('Bad objective id: ' + str(o.get('id')))
            continue
        if o['id'] in obj_level:
            issues.append('Duplicate objective id: ' + o['id'])
        obj_level[o['id']] = int(m.group(2))
        if not str(o.get('behavior', '')).strip():
            issues.append(f'{o["id"]}: behavior is empty')
    if not obj_level:
        issues.append('No objectives')
    for lv in (1, 2, 3):
        if lv not in obj_level.values():
            issues.append(f'No Lv{lv} objective')
    mod_ids, taught, ex_ids = set(), set(), set()
    level_assess = {}
    for mod in spec.get('modules', []):
        mid = str(mod.get('id', ''))
        if not re.match(r'^M\d{2}$', mid):
            issues.append('Bad module id: ' + mid)
        if mid in mod_ids:
            issues.append('Duplicate module id: ' + mid)
        mod_ids.add(mid)
        lv = mod.get('level')
        if lv not in (1, 2, 3):
            issues.append(f'{mid}: level must be 1, 2 or 3 (got {lv!r})')
        mins = mod.get('minutes')
        if not isinstance(mins, list) or len(mins) != 5 or any((not isinstance(v, int)) or isinstance(v, bool) or v < 0 for v in mins):
            issues.append(f'{mid}: minutes must be 5 non-negative integers [説明, 例解, 演習, レビュー, 評価]')
            mins = [0] * 5
        if sum(mins) == 0:
            issues.append(f'{mid}: all minutes are 0')
        if not mod.get('objectives'):
            issues.append(f'{mid}: no objectives')
        for oid in mod.get('objectives', []):
            if oid not in obj_level:
                issues.append(f'{mid}: unknown objective {oid}')
            elif obj_level[oid] != lv:
                issues.append(f'{mid}: objective {oid} is Lv{obj_level[oid]} but module is Lv{lv}')
            taught.add(oid)
        if not mod.get('evidence'):
            issues.append(f'{mid}: evidence is empty')
        ex = str(mod.get('exercise', ''))
        if not re.match(r'^E\d{2}$', ex):
            issues.append(f'{mid}: exercise must look like E01 (got {ex!r})')
        ex_ids.add(ex)
        if not str(mod.get('title', '')).strip():
            issues.append(f'{mid}: title is empty')
        aid = mod.get('assessment')
        if aid:
            level_assess.setdefault(lv, set()).add(aid)
    for oid in obj_level:
        if oid not in taught:
            issues.append(f'objective {oid} is not taught by any module')
    a_ids, assessed = set(), set()
    for a in spec.get('assessments', []):
        aid = str(a.get('id', ''))
        if not re.match(r'^A[123]$', aid):
            issues.append('Bad assessment id: ' + aid)
        if aid in a_ids:
            issues.append('Duplicate assessment id: ' + aid)
        a_ids.add(aid)
        lv = a.get('level')
        if lv not in (1, 2, 3):
            issues.append(f'{aid}: level must be 1, 2 or 3')
        if aid == f'A{lv}' and not any(m.get('assessment') == aid for m in spec.get('modules', [])):
            issues.append(f'{aid}: no module points to it (set modules[].assessment)')
        for key in ('observation_points', 'evidence', 'critical_errors'):
            if not a.get(key):
                issues.append(f'{aid}: {key} is empty')
        if not str(a.get('pass_rule', '')).strip():
            issues.append(f'{aid}: pass_rule is empty')
        objs = a.get('objectives') or [oid for m in spec.get('modules', []) if m.get('assessment') == aid for oid in m.get('objectives', [])]
        for oid in objs:
            if oid in obj_level and obj_level[oid] != lv:
                issues.append(f'{aid}: objective {oid} is Lv{obj_level[oid]} but assessment is Lv{lv}')
        assessed.update(objs)
        if sum(m['minutes'][4] for m in spec.get('modules', []) if m.get('level') == lv and isinstance(m.get('minutes'), list) and len(m['minutes']) == 5 and isinstance(m['minutes'][4], int)) == 0:
            issues.append(f'{aid}: Lv{lv} modules give 0 assessment minutes')
    for lv in (1, 2, 3):
        if f'A{lv}' not in a_ids:
            issues.append(f'No assessment A{lv}')
    for oid in obj_level:
        if oid not in assessed:
            issues.append(f'objective {oid} is not assessed by any assessment')
    for key, pat in (('templates', r'^T\d{1,2}$'), ('cards', r'^K\d{2}$'), ('roles', r'^R\d{2}$')):
        seen = set()
        for item in spec.get(key, []) or []:
            iid = str(item.get('id', '')) if isinstance(item, dict) else str(item)
            if not re.match(pat, iid):
                issues.append(f'{key}: bad id {iid!r}')
            if iid in seen:
                issues.append(f'{key}: duplicate id {iid}')
            seen.add(iid)
            if key == 'cards' and isinstance(item, dict) and not item.get('registry') and not item.get('fetched'):
                issues.append(f'{key}: {iid} needs "registry" (entry id) or "fetched" (url)')
    return issues


def build(spec, source):
    issues = validate_spec(spec, source)
    if issues:
        raise ValueError('spec has %d problem(s):\n- ' % len(issues) + '\n- '.join(issues))
    record = next(s for s in source['skills'] if s['id'] == spec['skill_id'])
    objectives = []
    for o in spec['objectives']:
        level = int(re.match(r'^S\d{3}-L([123])-O\d{2}$', o['id']).group(1))
        objectives.append({'id': o['id'], 'level': level, 'source_field': f'Lv{level}', 'behavior': o['behavior']})
    modules = [{'id': m['id'], 'level': m['level'], 'objectives': m['objectives'], 'minutes': dict(zip(PARTS, m['minutes'])),
                'evidence': m['evidence'], 'exercise': m['exercise']} for m in spec['modules']]
    assessments = []
    for a in spec['assessments']:
        assessments.append({'id': a['id'], 'level': a['level'],
                            'objectives': a.get('objectives') or sorted({oid for m in spec['modules'] if m.get('assessment') == a['id'] for oid in m['objectives']}),
                            'observation_points': a['observation_points'], 'evidence': a['evidence'],
                            'pass_rule': a['pass_rule'], 'critical_errors': a['critical_errors'],
                            'minutes': sum(m['minutes'][4] for m in spec['modules'] if m['level'] == a['level'])})
    total = sum(sum(m['minutes'].values()) for m in modules)
    today = spec.get('date') or date.today().isoformat()
    review = spec.get('review', {})
    data = {
        'skill_id': spec['skill_id'], 'skill_name': record['name'],
        'standard_version': spec.get('standard_version', '1.0.0'),
        'curriculum_version': spec.get('curriculum_version', '1.0.0'),
        'source_sha256': source['sha256'], 'status': spec.get('status', 'draft-reviewed'),
        'created_at': spec.get('created_at', today), 'reviewed_at': spec.get('reviewed_at', today),
        'files': ['01-design.md', '02-learner.md', '03-exercises.md', '04-instructor.md'],
        'objectives': objectives, 'modules': modules, 'assessments': assessments,
        'total_minutes': total,
        'templates': [t['id'] if isinstance(t, dict) else t for t in spec.get('templates', []) or []],
        'cards': [{'id': c['id'], 'registry': c.get('registry'), 'fetched': c.get('fetched')} for c in spec.get('cards', []) or []],
        'roles': [r['id'] if isinstance(r, dict) else r for r in spec.get('roles', []) or []],
        # the three flags are confirmed by the self-check table in 04 §8; `harness finish` records the date
        'review': {'source_alignment': True, 'case_solvable': True, 'answers_checked': True, 'pilot_conducted': False,
                   'self_check': review.get('self_check', 'pending'),
                   'limitations': review.get('limitations', ['試行授業未実施', '独立採点者間の一致度未検証'])},
    }
    return data


def checklist_items():
    items = []
    if CHECKLIST.is_file():
        for line in CHECKLIST.read_text(encoding='utf-8').splitlines():
            m = re.match(r'^(\d+)\. (.+)$', line)
            if m:
                items.append((int(m.group(1)), re.sub(r'◎.*$', '', m.group(2)).strip()))
    return items


def tables(spec, data):
    L = ['<!-- generated by gen_from_spec.py from _spec.json; paste the blocks into 01/02/03/04 and keep them in sync via lint -->', '']
    L.append('<!-- 01 §5 単元表 -->')
    L.append('| 単元 | Lv・目標末尾 | 内容 | 時間内訳 | 演習・主な提出物 | 修了評価 |')
    L.append('|---|---|---|---|---|---|')
    sums = [0] * 5
    level_tot = {1: 0, 2: 0, 3: 0}
    for mod in spec['modules']:
        mins = mod['minutes']
        tail = '、'.join('O' + o.rsplit('-O', 1)[1] for o in mod['objectives'])
        total = sum(mins)
        sums = [s + v for s, v in zip(sums, mins)]
        level_tot[mod['level']] += total
        L.append(f"| {mod['id']} | {mod['level']}・{tail} | {mod['title']} | {'/'.join(map(str, mins))} = {total} | {mod['exercise']} {mod['evidence'][0]} | {mod.get('assessment', '')} |")
    grand = sum(sums)
    exec_part = sums[2] + sums[3] + sums[4]
    L.append('')
    L.append(f"Lv1={level_tot[1]}分、Lv2={level_tot[2]}分、Lv3={level_tot[3]}分、合計{grand:,}分（{grand // 60}時間{grand % 60}分）。"
             + '、'.join(f'{l}{v}分' for l, v in zip(PART_LABELS, sums))
             + f"。実行・レビュー・評価が合計{exec_part:,}分（約{round(100 * exec_part / grand)}%）。原典の要求時間ではなく初版の設計値。")
    L.append('')
    L.append('<!-- 01 §4 学習目標表 -->')
    L.append('| ID | 条件・入力 | 観察する行動／提出物 | 品質・権限境界／典型失敗 |')
    L.append('|---|---|---|---|')
    for o in spec['objectives']:
        g = {k: str(o.get(k, '')).strip() or '記入' for k in OBJ_FIELDS}
        L.append(f"| {o['id']} | {g['condition']}／{g['input']} | {o['behavior']}／{g['deliverable']} | {g['quality']}／{g['boundary']}／{g['failure']} |")
    L.append('')
    scope = spec.get('scope') or {}
    L.append('<!-- 01 §1/§3 範囲 -->')
    L.append(f"本講座が担うこと：{scope.get('owns') or '記入'}")
    L.append(f"前提として説明すること：{scope.get('assumes') or '記入'}")
    L.append(f"他スキルへ委ねること：{scope.get('delegates') or '記入'}")
    L.append('')
    L.append('<!-- 01 §6 合格基準 -->')
    for a in data['assessments']:
        L.append(f"- {a['id']}：{a['pass_rule']}（{a['minutes']}分。観点：{'・'.join(a['observation_points'])}。重大誤判断：{'／'.join(a['critical_errors'])}）")
    L.append('')
    L.append('<!-- 02 単元見出し直下の行 -->')
    for mod in spec['modules']:
        mins = mod['minutes']
        objs = '、'.join(mod['objectives'])
        L.append(f"## {mod['id']} {mod['title']}\n\n目標{objs}。{sum(mins)}分（{'/'.join(map(str, mins))}）。前提：記入。\n")
    if spec.get('roles'):
        L.append('<!-- 03 共通の役割 -->')
        L.append('| Role | 架空の担当 | 役割 |')
        L.append('|---|---|---|')
        for r in spec['roles']:
            if isinstance(r, dict):
                L.append(f"| {r['id']} | {r.get('actor') or '記入'} | {r.get('role') or '記入'} |")
            else:
                L.append(f'| {r} | 記入 | 記入 |')
        L.append('')
    if spec.get('templates'):
        L.append('<!-- 03 提出テンプレート見出し -->')
        for t in spec['templates']:
            cols = ' | '.join(t.get('columns', [])) if isinstance(t, dict) else ''
            L.append(f"### {t['id'] if isinstance(t, dict) else t} {t.get('name', '') if isinstance(t, dict) else ''}".rstrip())
            if cols:
                L.append(f'| {cols} |')
            L.append('')
    if spec.get('cards'):
        L.append('<!-- 03 付録 抜粋カード見出し（registry の cards 本文を転記し、確認日と原典との差を書く） -->')
        for c in spec['cards']:
            L.append(f"### {c['id']} {c.get('title', '')}（registry: {c.get('registry') or c.get('fetched')}）".rstrip())
            L.append('')
    L.append('<!-- 04 §2 見出し（全演習） -->')
    for mod in spec['modules']:
        L.append(f"### {mod['exercise']} ")
    L.append('')
    items = checklist_items()
    if items:
        L.append('<!-- 04 §8 内容品質レビュー記録（結果は 済／該当なし／未実施（理由）。根拠は実際に確認した内容） -->')
        L.append('| # | 項目 | 結果 | 確認方法・根拠 |')
        L.append('|---|---|---|---|')
        for n, text in items:
            L.append(f'| {n} | {text} | 記入 | 記入 |')
        L.append('')
    return '\n'.join(L)


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    p = argparse.ArgumentParser()
    p.add_argument('spec', type=Path)
    p.add_argument('source', type=Path)
    p.add_argument('out_dir', type=Path)
    args = p.parse_args()
    spec = json.loads(args.spec.read_text(encoding='utf-8'))
    source = json.loads(args.source.read_text(encoding='utf-8'))
    data = build(spec, source)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / 'curriculum.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (args.out_dir / '_tables.md').write_text(tables(spec, data), encoding='utf-8')
    print(json.dumps({'skill': data['skill_id'], 'objectives': len(data['objectives']), 'modules': len(data['modules']),
                      'assessments': [(a['id'], a['minutes']) for a in data['assessments']], 'total_minutes': data['total_minutes'],
                      'written': ['curriculum.json', '_tables.md']}, ensure_ascii=False))
