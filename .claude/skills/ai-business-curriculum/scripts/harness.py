"""Production harness: the mechanical steps of making one curriculum, as one command line.

  python scripts/harness.py plan   S003 --source SRC.json --out docs/curricula/S003 --catalog CAT.json [--force]
  python scripts/harness.py build  --spec docs/curricula/S003/_spec.json --source SRC.json --out docs/curricula/S003
  python scripts/harness.py lint   docs/curricula/S003 --source SRC.json
  python scripts/harness.py finish docs/curricula/S003 --source SRC.json --catalog docs/curricula/catalog.json [--force] [--keep-temp]
  python scripts/harness.py fetch  URL --out DIR [--grep PATTERN ...] [--window N] [--max-matches N] [--grep-only]

`plan` writes the bounded context (_context.json), the matched registry entries in full (_sources.json)
and a spec template, and prints the step list. `build` validates the spec and turns it into
curriculum.json and _tables.md (skeletons for all four files). `lint` runs validate + cross-file checks.
`finish` refuses on lint errors or an incomplete self-check, records the self-check date and the
sources used, and updates only this skill's row in the catalog. Nothing here calls a model.
Python 3.10+, standard library only. Use `python3` or the absolute interpreter path where `python`
is a store alias.
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from select_context import select  # noqa: E402
from source_check import check as source_check  # noqa: E402
from gen_from_spec import build as build_json, tables  # noqa: E402
from lint_curriculum import lint  # noqa: E402

STEPS = """手順（読む・書く対象の上限。トークンの目安は SKILL.md「予算」）
 1 read   SKILL.md、references の5本、examples.md、_context.json、_sources.json。原典スナップショット全文・完成例全文・source-registry.json 本体は読まない。
 2 spec   _spec.template.json → _spec.json（目標の7項目、単元・分数、評価の観点・重大誤判断、scope、roles、templates、cards）→ build。エラーは spec を直して再 build。
 3 write  03 → 04 → 02 → 01。_tables.md の骨組みを貼って埋める。1ファイル1回の Write（3万字を超える場合は前半・後半の2回）。
 4 check  lint → エラーを差分修正（Edit）→ 独立解答（Agent が使える環境では 03 だけを渡して A1〜A3 を解かせ、04 と突き合わせる。1回）→ quality-checklist を 04 §8 の表に記録 → lint。
 5 finish 台帳の当該行だけ更新。報告は「作成物／確認したこと（lint・独立解答・使った registry entry・再取得した資料）／未確認・未実施」。
禁止：多エージェント・Workflow・Web検索・多視点レビュー（ユーザーが明示した場合のみ）。registry 本体・原典全文・完成例全文の読込。書いたファイルの全文再読（修正は Edit の差分）。"""


def brief(source, ctx, legal, w_ids=()):
    """Bounded context: the skill row, related tasks, roles, this skill's task x skill rows; legal items only when needed."""
    def cells(row, cols):
        n = row['row']
        return {c: row['cells'].get(f'{c}{n}') for c in cols if row['cells'].get(f'{c}{n}')}
    sid = ctx['skill']['id']
    out = {'source_file': ctx['source_file'], 'source_sha256': ctx['source_sha256'], 'skill': ctx['skill'],
           'related_skills': [{k: s[k] for k in ('id', 'name', 'definition', 'tasks')} for s in ctx['related_skills']],
           'tasks': [], 'roles': [], 'task_skill_rows': []}
    for name, rows in ctx['context'].items():
        for row in rows:
            if row['row'] <= 3:
                continue
            if name.startswith('02_'):
                out['tasks'].append(cells(row, 'ABCDEFGHIJNOPQU'))
            elif name.startswith('06_'):
                out['roles'].append(cells(row, 'ABCDEF'))
            elif name.startswith('08_') and row['cells'].get(f'E{row["row"]}') == sid:
                out['task_skill_rows'].append(cells(row, 'ACDGH'))
    out['_columns'] = {'tasks': 'A=ID B=工程 C=区分 D=名 E=内容 F=成果物 G=実施R H=承認A I=完了条件 J=適用条件 N=Gate O=依存 P=必要スキル Q=AI/人境界 U=URL',
                       'roles': 'A=ID B=ロール C=主要責任 D=関与 E=独立性注意 F=中核Skill', 'task_skill_rows': f'A=Task C=実施R D=承認A G=必要Lv H=証拠（Skill={sid}の行のみ）'}
    if legal:
        for name, rows in source['sheets'].items():
            if name.startswith('12_'):
                out['legal_items'] = [cells(r, 'ABCDEFMN') for r in rows if r['row'] >= 4]
            if name.startswith('03_'):
                out['tier'] = [cells(r, 'ABCDE') for r in rows if 4 <= r['row'] <= 7]
            if name.startswith('24_'):
                out['source_sheet'] = [cells(r, 'ABCDFGI') for r in rows if str(r['cells'].get(f'A{r["row"]}', '')).startswith('W')
                                       and (not w_ids or r['cells'].get(f'A{r["row"]}') in w_ids)]
        out['_columns'].update({'legal_items': 'A=判定ID B=対象 C=位置づけ D=確認内容 E=責任Role F=タイミング M=根拠ID(→source_sheet) N=公式URL',
                                'tier': 'A=Tier B=名称 C=用途 D=評価強度 E=注意', 'source_sheet': 'A=SourceID B=公開/版 C=組織 D=資料名 F=採用内容 G=確認範囲・限界 I=URL（原典の記載。「原典との差」の比較元）'})
    return out


def cmd_plan(args):
    source = json.loads(args.source.read_text(encoding='utf-8'))
    status = None
    if args.catalog and args.catalog.is_file():
        cat = json.loads(args.catalog.read_bytes().decode('utf-8'))
        row = next((s for s in cat['skills'] if s['id'] == args.skill_id), None)
        status = row and row.get('status')
    existing = [f.name for f in args.out.iterdir() if f.suffix in ('.md', '.json') and not f.name.startswith('_')] if args.out.is_dir() else []
    if status in ('draft-reviewed', 'pilot-validated') and existing and not args.force:
        print(json.dumps({'refused': f'{args.skill_id} is already {status} with files {existing}; nothing written. Use --force for a deliberate revision.'}, ensure_ascii=False))
        raise SystemExit(1)
    args.out.mkdir(parents=True, exist_ok=True)
    ctx = select(source, args.skill_id)
    sc = source_check(source, args.skill_id)
    w_ids = {o['w'] for m in sc['matched'] for o in m.get('origin', [])}
    legal = sc['legal_content'] or bool(sc['matched'])
    (args.out / '_context.json').write_text(json.dumps(brief(source, ctx, legal, w_ids), ensure_ascii=False, indent=1), encoding='utf-8')
    (args.out / '_sources.json').write_text(json.dumps(sc, ensure_ascii=False, indent=1), encoding='utf-8')
    tmpl = args.out / '_spec.template.json'
    if not tmpl.exists() and not (args.out / '_spec.json').exists():
        oid = f'{args.skill_id}-L1-O01'
        tmpl.write_text(json.dumps({
            'skill_id': args.skill_id, 'curriculum_version': '1.0.0', 'status': 'draft-reviewed', 'date': date.today().isoformat(),
            'scope': {'owns': '本講座が担うこと（1〜3文）', 'assumes': '前提として説明すること', 'delegates': '他スキルへ委ねること（S番号・タスクID）'},
            'objectives': [{'id': oid, 'behavior': '観察可能な行動を1つ', 'condition': '状況・支援', 'input': '渡される情報', 'deliverable': '提出物',
                            'quality': '揃えば適切といえる条件', 'boundary': '委ねる相手・確定者', 'failure': '典型誤り'}],
            'modules': [{'id': 'M01', 'level': 1, 'objectives': [oid], 'title': '単元名', 'minutes': [25, 15, 30, 20, 0],
                         'exercise': 'E01', 'evidence': ['提出物名'], 'assessment': 'A1'}],
            'assessments': [{'id': 'A1', 'level': 1, 'observation_points': ['観点1'], 'evidence': ['提出物名'],
                             'pass_rule': '知識8/10以上・必須問全正答、全観点2以上・重大誤判断0件', 'critical_errors': ['観察可能な行動で書いた重大誤判断']}],
            'roles': [{'id': 'R14', 'actor': '架空の担当', 'role': '判定の確定者'}],
            'templates': [{'id': 'T1', 'name': '様式名', 'columns': ['列1', '列2']}],
            'cards': [{'id': 'K01', 'registry': m['id'], 'title': m['title']} for m in sc['matched']][:1],
            'review': {'limitations': ['試行授業未実施', '独立採点者間の一致度未検証']},
        }, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'skill': args.skill_id, 'name': ctx['skill']['name'], 'tasks': ctx['skill']['tasks'], 'catalog_status': status,
                      'existing_files': existing, 'context_chars': len((args.out / '_context.json').read_text(encoding='utf-8')),
                      'sources': {'legal_content': sc['legal_content'], 'reuse': [m['id'] for m in sc['matched'] if not m['stale']],
                                  'stale': [m['id'] for m in sc['matched'] if m['stale']], 'hints_from_tasks': [h['id'] for h in sc['hints']],
                                  'unregistered': [u['topic'] for u in sc['unregistered']], 'action': sc['action'],
                                  'sources_chars': len((args.out / '_sources.json').read_text(encoding='utf-8'))},
                      'spec_template': str(tmpl) if tmpl.exists() else None}, ensure_ascii=False, indent=2))
    print(STEPS)


def cmd_build(args):
    spec = json.loads(args.spec.read_text(encoding='utf-8'))
    source = json.loads(args.source.read_text(encoding='utf-8'))
    try:
        data = build_json(spec, source)
    except ValueError as ex:
        print(json.dumps({'refused': str(ex)}, ensure_ascii=False, indent=2))
        raise SystemExit(1)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'curriculum.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (args.out / '_tables.md').write_text(tables(spec, data), encoding='utf-8')
    print(json.dumps({'total_minutes': data['total_minutes'], 'modules': len(data['modules']),
                      'assessments': [(a['id'], a['minutes']) for a in data['assessments']],
                      'next': 'paste the _tables.md blocks into 01/02/03/04 (see the <!-- --> labels) and fill every 記入'}, ensure_ascii=False))


def run_lint(folder, source_path):
    return lint(folder, json.loads(source_path.read_text(encoding='utf-8')))


def cmd_lint(args):
    r = run_lint(args.directory, args.source)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    raise SystemExit(0 if r['ok'] else 1)


def cmd_finish(args):
    r = run_lint(args.directory, args.source)
    sc = r.get('self_check')
    incomplete = r['strict'] and (not sc or not sc['complete'])
    if (not r['ok'] or incomplete) and not args.force:
        print(json.dumps({'refused': 'lint errors' if not r['ok'] else 'self-check table in 04 §8 incomplete', 'errors': r['errors']}, ensure_ascii=False, indent=2))
        raise SystemExit(1)
    today = date.today().isoformat()
    cur_path = args.directory / 'curriculum.json'
    cur = json.loads(cur_path.read_text(encoding='utf-8'))
    verified = r['ok'] and not incomplete
    if r['strict']:
        cur['review']['self_check'] = today if verified else 'pending'
        cur['review']['self_check_not_done'] = [f'{n}: {res}' for n, res in (sc or {}).get('not_done', [])]
    if not verified:
        cur['status'] = 'draft-unverified'
    cur['reviewed_at'] = today
    cur_path.write_text(json.dumps(cur, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    raw = args.catalog.read_bytes()
    crlf = b'\r\n' in raw
    cat = json.loads(raw.decode('utf-8'))
    row = next((s for s in cat['skills'] if s['id'] == cur['skill_id']), None)
    if row is None:
        raise SystemExit('skill not in catalog: ' + cur['skill_id'])
    if row.get('name') != cur['skill_name']:
        raise SystemExit('catalog name mismatch: ' + str(row.get('name')))
    sources = {'registry': [], 'stale': [], 'urls': []}
    sp = args.directory / '_sources.json'
    if sp.is_file():
        s = json.loads(sp.read_text(encoding='utf-8'))
        sources['registry'] = [f"{m['id']}@{m['checked_at']}" for m in s['matched']]
        sources['stale'] = [m['id'] for m in s['matched'] if m['stale']]
    d03 = (args.directory / '03-exercises.md').read_text(encoding='utf-8') if (args.directory / '03-exercises.md').is_file() else ''
    app = d03[d03.find('## 付録'):] if '## 付録' in d03 else ''
    sources['urls'] = sorted(set(re.findall(r'https?://[^\s）)、｜|]+', app)))
    open_items = list(cur.get('review', {}).get('limitations', []))
    open_items += [f'自己点検 未実施: {x}' for x in cur.get('review', {}).get('self_check_not_done', [])]
    if sources['stale']:
        open_items.append(f'一次資料の再確認待ち（registry stale）: {sources["stale"]}')
    if not r['ok']:
        open_items.append(f'lint errors ({len(r["errors"])}) left with --force')
    row.update({'status': cur['status'], 'curriculum_path': args.directory.name, 'curriculum_version': cur['curriculum_version'],
                'standard_version': cur['standard_version'], 'source_sha256': cur['source_sha256'], 'reviewed_at': cur['reviewed_at'],
                'validation': {'script': 'harness lint', 'checked_at': today, 'ok': r['ok'], 'strict': r['strict'],
                               'objectives': len(cur['objectives']), 'modules': len(cur['modules']), 'assessments': len(cur['assessments']),
                               'minutes': cur['total_minutes'], 'errors': len(r['errors']), 'warnings': len(r['warnings'])},
                'self_check': ({'date': cur['review'].get('self_check'), 'done': len(sc['done']), 'na': len(sc['na']), 'not_done': [n for n, _ in sc['not_done']]}
                               if sc else {'date': None, 'note': 'pre-harness curriculum; review recorded in 04'}),
                'sources': sources,
                'not_performed': ['試行授業', '独立採点者間の一致度検証', '実務での能力認定'],
                'open_items': open_items})
    out = json.dumps(cat, ensure_ascii=False, indent=2)
    if crlf:
        out = out.replace('\n', '\r\n')
    args.catalog.write_bytes(out.encode('utf-8'))
    for tmp in ('_context.json', '_sources.json', '_tables.md', '_spec.template.json'):
        if (args.directory / tmp).exists() and not args.keep_temp:
            (args.directory / tmp).unlink()
    print(json.dumps({'catalog_updated': cur['skill_id'], 'status': cur['status'], 'self_check': row['self_check'], 'sources': sources,
                      'lint_errors': r['errors'], 'lint_warnings': r['warnings']}, ensure_ascii=False, indent=2))


def cmd_fetch(args):
    cmd = [sys.executable, str(HERE / 'fetch_source.py'), args.url, '--out', str(args.out), '--window', str(args.window), '--max-matches', str(args.max_matches)]
    if args.grep:
        cmd += ['--grep', *args.grep]
    if args.grep_only:
        cmd.append('--grep-only')
    raise SystemExit(subprocess.run(cmd).returncode)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('plan'); a.add_argument('skill_id'); a.add_argument('--source', type=Path, required=True); a.add_argument('--out', type=Path, required=True)
    a.add_argument('--catalog', type=Path); a.add_argument('--force', action='store_true')
    a.set_defaults(fn=cmd_plan)
    b = sub.add_parser('build'); b.add_argument('--spec', type=Path, required=True); b.add_argument('--source', type=Path, required=True); b.add_argument('--out', type=Path, required=True)
    b.set_defaults(fn=cmd_build)
    c = sub.add_parser('lint'); c.add_argument('directory', type=Path); c.add_argument('--source', type=Path, required=True)
    c.set_defaults(fn=cmd_lint)
    d = sub.add_parser('finish'); d.add_argument('directory', type=Path); d.add_argument('--source', type=Path, required=True); d.add_argument('--catalog', type=Path, required=True)
    d.add_argument('--force', action='store_true'); d.add_argument('--keep-temp', action='store_true')
    d.set_defaults(fn=cmd_finish)
    e = sub.add_parser('fetch'); e.add_argument('url'); e.add_argument('--out', type=Path, required=True); e.add_argument('--grep', nargs='*')
    e.add_argument('--window', type=int, default=200); e.add_argument('--max-matches', type=int, default=30); e.add_argument('--grep-only', action='store_true')
    e.set_defaults(fn=cmd_fetch)
    args = p.parse_args()
    args.fn(args)
