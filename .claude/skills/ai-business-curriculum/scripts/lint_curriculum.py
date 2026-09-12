"""Cross-file consistency lint for a curriculum folder (deterministic, no model tokens).

Checks the things a human/agent review would otherwise spend tokens on:
- module minutes / level / objectives / exercise: curriculum.json == 02 heading lines == 01 単元表 rows; level and grand totals
- assessment minutes: 03 header total == sum of module assessment minutes per level
- observation points (json) appear in the 03 採点 line and as filled rows of the 04 rubric table
- 04 has a model answer heading for every exercise, and 照会応答カード tables inside the A2/A3 sections
- IDs: M/E/T/K referenced anywhere are defined where they must be; objectives are rows of the 01 table;
  templates/cards/roles declared in the spec exist in 03
- every module in 02 has the section markers of the production standard
- every appendix card (K) has a URL, a confirmation date and 原典との差
- 日付計算表 rows are recomputed (暦日/週間 exactly, 営業日 without holidays) and weekdays are checked
- placeholders / unfinished markers (incl. the 記入 cells of the generated skeletons); legal status words without a date
- the self-check table in 04 §8 (all checklist items, valid results, evidence) for harness-built curricula
Strict mode (curriculum.json built by the harness: review.self_check present) turns the newer checks into errors;
for the older S001/S002 they are warnings. Errors block `harness finish`.
Python 3.10+, standard library only.
"""
import argparse
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_curriculum import validate  # noqa: E402
from gen_from_spec import checklist_items  # noqa: E402

PARTS = ['explanation', 'worked_example', 'practice', 'review', 'assessment']
MODULE_MARKERS = ['**状況と問い', '**手順', '**例', '**誤りと修正', '**振り返り']
PLACEHOLDERS = ['（作成中', 'TODO', 'TBD', 'XXX', '（後で', '後日追記', '記入予定']
# skeleton cells left by gen_from_spec.tables(); plain "| 記入 |" rows are legitimate blank template rows in 03
PLACEHOLDER_RES = [r'：記入。', r'／記入', r'こと：記入', r'^\| R\d{2} \| 記入 \|', r'registry: None']
E_ID = r'(?<![A-Z:])(E\d{2})(?!\d)'
NB = r'(?![0-9A-Za-z])'  # id boundary that also works before CJK text
WEEKDAYS = '月火水木金土日'
RESULT_RE = re.compile(r'^(済|該当なし|未実施)')


def section(text, start_pattern, end_pattern=r'^## '):
    m = re.search(start_pattern, text, re.M)
    if not m:
        return ''
    rest = text[m.end():]
    e = re.search(end_pattern, rest, re.M)
    return rest[:e.start()] if e else rest


def expand_tails(text, base=''):
    """'O01〜O04', 'O04、O05', 'O01・O03' -> {'O01', …}; with base, full ids are returned."""
    out, prev = set(), None
    for sep, num in re.findall(r'([〜、・,]?)\s*O(\d{2})', text):
        n = int(num)
        if sep == '〜' and prev is not None:
            out.update(f'O{i:02}' for i in range(prev, n + 1))
        else:
            out.add(f'O{n:02}')
        prev = n
    return {f'{base}-{t}' if base else t for t in out}


def objective_ids(line):
    """Expand '目標S002-L1-O01、O02' / 'S002-L1-O01〜O03' / 'S002-L1-O01、S002-L1-O02' into a set of ids."""
    ids = set()
    for base, tails in re.findall(r'(S\d{3}-L\d)-((?:O\d{2}(?:\s*[〜、・,]\s*(?!S\d{3})O\d{2})*))', line):
        ids.update(expand_tails(tails, base))
    return ids


def add_days(d, n, kind):
    if kind in ('営業日',):
        step = 1 if n >= 0 else -1
        left = abs(n)
        while left:
            d += timedelta(days=step)
            if d.weekday() < 5:
                left -= 1
        return d
    if kind in ('週間', '週'):
        n *= 7
    return d + timedelta(days=n)


def check_date_tables(text, where, E, W):
    found = False
    for m in re.finditer(r'^### [^\n]*日付計算表[^\n]*\n(.*?)(?=^###? |\Z)', text, re.M | re.S):
        found = True
        rows = {}
        for r in re.finditer(r'^\| ([^|]+?) \| (\d{4}-\d{2}-\d{2})(?:（([月火水木金土日])）)? \| ([^|]*) \|', m.group(1), re.M):
            name, ds, wd, deriv = r.group(1).strip(), r.group(2), r.group(3), r.group(4).strip()
            try:
                d = date.fromisoformat(ds)
            except ValueError:
                E(f'{where}: 日付計算表 {name}: invalid date {ds}')
                continue
            rows[name] = d
            if wd and WEEKDAYS[d.weekday()] != wd:
                E(f'{where}: 日付計算表 {name}: {ds} is {WEEKDAYS[d.weekday()]}曜, table says {wd}')
            dm = re.match(r'^(.+?)\s*([＋+−\-－])\s*(\d+)\s*(暦日|日|営業日|週間|週)$', deriv)
            if dm:
                base, sign, n, kind = dm.group(1).strip(), dm.group(2), int(dm.group(3)), dm.group(4)
                if base not in rows:
                    E(f'{where}: 日付計算表 {name}: base "{base}" must be an earlier row')
                    continue
                n = -n if sign in '−-－' else n
                exp = add_days(rows[base], n, kind)
                if exp != d:
                    E(f'{where}: 日付計算表 {name}: {base}{sign}{abs(n)}{kind} = {exp.isoformat()}, table says {ds}')
                if kind == '営業日':
                    W(f'{where}: 日付計算表 {name}: 営業日 computed without holidays; confirm 祝日')
    return found


def lint(folder, source=None):
    errors, warnings = [], []
    E, W = errors.append, warnings.append
    f = {}
    for name in ['01-design.md', '02-learner.md', '03-exercises.md', '04-instructor.md']:
        p = folder / name
        f[name] = p.read_text(encoding='utf-8') if p.is_file() else ''
        if not f[name]:
            E(f'missing or empty: {name}')
    try:
        data = json.loads((folder / 'curriculum.json').read_text(encoding='utf-8'))
    except Exception as ex:  # noqa: BLE001
        return {'ok': False, 'errors': [f'curriculum.json unreadable: {ex}'], 'warnings': [], 'validate': None, 'strict': False, 'self_check': None}
    strict = 'self_check' in data.get('review', {})
    EW = E if strict else W
    d01, d02, d03, d04 = f['01-design.md'], f['02-learner.md'], f['03-exercises.md'], f['04-instructor.md']
    all_text = d01 + d02 + d03 + d04

    for name, text in f.items():
        for ph in PLACEHOLDERS:
            if ph in text:
                E(f'{name}: placeholder "{ph}" remains')
        for pat in PLACEHOLDER_RES:
            m = re.search(pat, text)
            if m:
                E(f'{name}: placeholder cell "{m.group(0)}" remains (skeleton not filled)')

    # modules
    level_sum = {1: 0, 2: 0, 3: 0}
    for mod in data['modules']:
        mid = mod['id']
        mins = [mod['minutes'][k] for k in PARTS]
        total = sum(mins)
        level_sum[mod['level']] += total
        m02 = re.search(rf'^## {mid}{NB}[^\n]*\n(?:[ \t]*\n)*([^\n]*?)(\d+)分（(\d+)/(\d+)/(\d+)/(\d+)/(\d+)）', d02, re.M)
        if not m02:
            E(f'02: heading/time line for {mid} not found (expected "## {mid} 単元名", then "目標…。NNN分（a/b/c/d/e）。" on the next non-blank line)')
        else:
            got = [int(m02.group(i)) for i in range(3, 8)]
            if int(m02.group(2)) != total or got != mins:
                E(f'02: {mid} minutes {m02.group(2)}({"/".join(map(str, got))}) != json {total}({"/".join(map(str, mins))})')
            ids = objective_ids(m02.group(1))
            if ids and ids != set(mod['objectives']):
                EW(f'02: {mid} line names objectives {sorted(ids)} but json has {mod["objectives"]}')
            elif not ids:
                W(f'02: {mid} time line does not name its objective ids')
        m01 = re.search(rf'^\| {mid} \| (\d)・([^|]*) \|[^\n]*\| (\d+)/(\d+)/(\d+)/(\d+)/(\d+) = (\d+) \|([^\n]*)', d01, re.M)
        if not m01:
            E(f'01: 単元表 row for {mid} not found or not in "| Mxx | Lv・Oyy | … | a/b/c/d/e = total | Exx … | An |" form')
        else:
            got = [int(m01.group(i)) for i in range(3, 8)]
            if got != mins or int(m01.group(8)) != total:
                E(f'01: {mid} row minutes {"/".join(map(str, got))}={m01.group(8)} != json {"/".join(map(str, mins))}={total}')
            if int(m01.group(1)) != mod['level']:
                EW(f'01: {mid} row says Lv{m01.group(1)} but json level is {mod["level"]}')
            tails = expand_tails(m01.group(2))
            exp_tails = {o.rsplit('-', 1)[1] for o in mod['objectives']}
            if tails != exp_tails:
                EW(f'01: {mid} row objectives {sorted(tails)} != json {sorted(exp_tails)}')
            if mod.get('exercise') and mod['exercise'] not in m01.group(9):
                EW(f'01: {mid} row does not name its exercise {mod["exercise"]}')
        body = section(d02, rf'^## {mid}{NB}')
        for marker in MODULE_MARKERS:
            if marker not in body:
                W(f'02: {mid} lacks marker {marker}：')
        ex = mod.get('exercise')
        if ex and f'**{ex}' not in body and f'{ex}：' not in body and f'{ex}を' not in body and f'{ex}で' not in body:
            E(f'02: {mid} does not reference its exercise {ex}')
    for lv, s in level_sum.items():
        if f'Lv{lv}={s}分' not in d01:
            W(f'01: level total "Lv{lv}={s}分" not stated')
    if f'{data["total_minutes"]:,}分' not in d01 and f'{data["total_minutes"]}分' not in d01:
        E(f'01: total {data["total_minutes"]} minutes not stated')

    # assessments
    sec2_04 = section(d04, r'^## 2\.')
    for mod in data['modules']:
        ex = mod.get('exercise')
        if ex and not re.search(rf'^### [^\n]*{ex}{NB}', sec2_04, re.M):
            EW(f'04: §2 has no model-answer heading "### {ex} …"')
    for a in data['assessments']:
        aid = a['id']
        sec03 = section(d03, rf'^## {aid}{NB}')
        if not sec03:
            E(f'03: section "## {aid}" not found')
            continue
        expected = sum(m['minutes']['assessment'] for m in data['modules'] if m['level'] == a['level'])
        if 'minutes' in a and a['minutes'] != expected:
            E(f'json: {aid}.minutes {a["minutes"]} != sum of module assessment minutes at Lv{a["level"]} ({expected})')
        first_para = sec03.split('\n###')[0]
        head = re.search(r'^(\d+)分', first_para, re.M) or re.search(r'(?:所要(?:時間)?[：:]?\s*|合計)(\d+)分', first_para)
        if not head:
            head = re.search(r'(\d+)分', first_para)
            if head:
                W(f'03: {aid} total time taken from the first "N分" in the intro ({head.group(1)}分); start a line with "NN分" to be explicit')
        if not head:
            W(f'03: {aid} has no total time before its first ### subsection')
        elif int(head.group(1)) != expected:
            E(f'03: {aid} states {head.group(1)}分 but module assessment minutes at Lv{a["level"]} sum to {expected}')
        pts = a.get('observation_points')
        sec04 = section(d04, rf'^## \d+\. {aid}{NB}')
        if not pts:
            W(f'json: {aid} has no observation_points (required for new curricula)')
        else:
            grade_lines = [ln for ln in sec03.splitlines() if '採点' in ln]
            for pt in pts:
                if not any(pt in ln for ln in grade_lines):
                    E(f'03: {aid} 採点 line does not name observation point "{pt}"')
            if not sec04:
                E(f'04: section "## n. {aid} 採点" not found')
            else:
                rows = {r.group(1).strip(): r.group(2).strip() for r in re.finditer(r'^\| ([^|]+?) \| ([^|]*)\|', sec04, re.M)}
                for pt in pts:
                    if pt not in rows:
                        E(f'04: {aid} rubric table has no row "{pt}" (first cell must equal the observation point exactly)')
                    elif not rows[pt]:
                        E(f'04: {aid} rubric row "{pt}" has an empty 2点 cell')
                if '重大誤判断' not in sec04:
                    E(f'04: {aid} section lacks 重大誤判断')
                if aid in ('A2', 'A3'):
                    card = re.search(r'^### [^\n]*応答カード[^\n]*\n(.*?)(?=^###? |\Z)', sec04, re.M | re.S)
                    if not card:
                        EW(f'04: {aid} section has no "### 照会応答カード" heading')
                    elif len(re.findall(r'^(?:\| |- )', card.group(1), re.M)) < 3:
                        EW(f'04: {aid} 照会応答カード has fewer than 3 rows/bullets of facts')
        if aid in ('A2', 'A3') and '最低完成条件' not in sec03:
            EW(f'03: {aid} states no 最低完成条件')
        if aid == 'A1' and '知識' in a.get('pass_rule', '') and '必須' not in sec03:
            W(f'03: {aid} knowledge questions have no 【必須】 mark')
    if not strict and any(a['id'] in ('A2', 'A3') for a in data['assessments']) and '応答カード' not in d04:
        E('04: no 照会応答カード for Lv2/Lv3 assessments')

    # IDs
    e_def = set()
    for line in d03.splitlines():
        if re.match(r'^### (?![TK]\d)', line) or '提出' in line[:14] or line.startswith('**E'):
            e_def.update(re.findall(E_ID, line))
    e_def |= set(re.findall(r'(E\d{2})提出', d03))
    e_ref = set(re.findall(E_ID, all_text))
    for e in sorted(e_ref - e_def):
        E(f'03: exercise {e} referenced but not defined in a 03 heading (### Exx / ### P-… パック（Exx）) or a line starting with 提出Exx：')
    t_def = set(re.findall(r'^### (T\d{1,2})\b', d03, re.M))
    t_ref = set(re.findall(r'(?<![A-Z〜])(T\d{1,2})(?!\d)', all_text))
    t_used = set(re.findall(r'(?<![A-Z〜])(T[1-3])(?=[でのにをへ（(、・])', all_text))
    for t in sorted(t_ref - t_def):
        if int(t[1:]) > 3:
            E(f'03: template {t} referenced but not defined (### {t} ...)')
        elif t in t_used:
            EW(f'03: template {t} is used as a submission template but has no "### {t}" heading (Tier T0〜T3 mentions are ignored)')
    for t in data.get('templates', []) or []:
        if t not in t_def:
            E(f'03: spec declares template {t} but 03 has no "### {t}" heading')
    k_def = set(re.findall(r'^### (K\d{2})\b', d03, re.M))
    k_ref = set(re.findall(r'(?<![A-Z])(K\d{2})(?!\d)', all_text))
    for k in sorted(k_ref - k_def):
        E(f'03: appendix card {k} referenced but not defined')
    for c in data.get('cards', []) or []:
        if c['id'] not in k_def:
            E(f'03: spec declares card {c["id"]} but 03 has no "### {c["id"]}" heading')
    appendix = section(d03, r'^## 付録')
    for k in sorted(k_def):
        body = section(d03, rf'^### {k}\b', r'^###? ')
        if 'http' not in body:
            E(f'03: {k} has no URL')
        if '確認日' not in body and '確認日' not in appendix[:400]:
            EW(f'03: {k} has no 確認日 (put it in the card or the 付録 heading)')
        if '原典との差' not in body:
            W(f'03: {k} has no 原典との差 line')
    m_ref = set(re.findall(r'(?<![A-Z])(M\d{2})(?!\d)', all_text))
    m_def = {m['id'] for m in data['modules']}
    for m in sorted(m_ref - m_def):
        E(f'module {m} referenced but not in curriculum.json')
    for oid in [o['id'] for o in data['objectives']]:
        if oid not in d01:
            E(f'01: objective {oid} missing from design')
        elif not re.search(rf'^\| {re.escape(oid)} \|', d01, re.M):
            EW(f'01: objective {oid} is not a row of the 学習目標表')

    # roles
    role_rows = set(re.findall(r'^\| (R\d{2}) \|', d03, re.M))
    used = set(re.findall(r'(?<![A-Z])(R\d{2})(?!\d)', d02 + d03 + d04))
    for r in sorted(used - role_rows):
        W(f'03: role {r} used but not in 共通の役割 table')
    for r in data.get('roles', []) or []:
        if r not in role_rows:
            E(f'03: spec declares role {r} but the 共通の役割 table has no row for it')

    # dates
    has_table = check_date_tables(d03, '03', E, W) | check_date_tables(d04, '04', E, W)
    if not has_table:
        dates = set()
        for a in data['assessments']:
            if a['id'] in ('A2', 'A3'):
                dates.update(re.findall(r'\d{4}-\d{2}-\d{2}', section(d03, rf'^## {a["id"]}{NB}') + section(d04, rf'^## \d+\. {a["id"]}{NB}')))
        if len(dates) >= 3:
            W(f'A2/A3 use {len(dates)} distinct dates but there is no "### 日付計算表" (| 名称 | YYYY-MM-DD（曜） | 導出 |) for lint to recompute')

    # copied sentences (practice answers reused as assessment answers / examples that are the exercise answers)
    def sentences(text):
        return {ln.strip() for ln in text.splitlines() if len(ln.strip()) >= 25 and not ln.strip().startswith(('|', '#', '<'))}
    sec3_5 = ''.join(section(d04, rf'^## \d+\. {a["id"]}{NB}') for a in data['assessments'])
    dup1 = sentences(sec2_04) & sentences(sec3_5)
    if len(dup1) > 3:
        W(f'04: {len(dup1)} sentences (>=25 chars) appear both in §2 practice answers and in the assessment sections, e.g. "{sorted(dup1)[0][:40]}…"')
    examples = '\n'.join(re.findall(r'\*\*例[：:]\*\*([^\n]*)', d02))
    dup2 = sentences(examples) & sentences(sec2_04)
    if len(dup2) > 3:
        W(f'02/04: {len(dup2)} example sentences are identical to practice model answers')

    # legal/source hygiene
    if ('## 2. 一次資料' in d01 or k_def) and '確認日' not in d01:
        E('01: primary-source section has no 確認日')
    for phrase in ['採択済み', '施行済み', '適用中']:
        for name, text in (('02', d02), ('03', d03), ('04', d04)):
            for line in text.splitlines():
                if phrase in line and not re.search(r'20\d\d', line):
                    W(f'{name}: "{phrase}" without a date: {line[:50]}…')
                    break
    m_vals = re.search(r'\| 適用判定 \|([^\n]*)', d02)
    if m_vals and '対象外候補' in m_vals.group(1) and '対象外候補' not in d03:
        W('03: 用語集 defines 対象外候補 but templates never use it')

    # self-check record (04 §8) for harness-built curricula
    self_check = None
    if strict:
        sec8 = section(d04, r'^## 8\.')
        items = checklist_items()
        got = {}
        for r in re.finditer(r'^\| (\d+) \| [^|]* \| ([^|]*) \| ([^|]*) \|', sec8, re.M):
            got[int(r.group(1))] = (r.group(2).strip(), r.group(3).strip())
        if not sec8:
            E('04: §8 内容品質レビュー記録 not found (## 8. …)')
        done, na, not_done = [], [], []
        for n, text in items:
            if n not in got:
                E(f'04 §8: checklist item {n} has no row')
                continue
            res, why = got[n]
            if not RESULT_RE.match(res):
                E(f'04 §8: item {n} result "{res[:20]}" must start with 済／該当なし／未実施')
            elif res.startswith('済'):
                done.append(n)
                if len(why) < 8 or why == '記入':
                    E(f'04 §8: item {n} is 済 but the 確認方法・根拠 cell is empty')
            elif res.startswith('該当なし'):
                na.append(n)
            else:
                not_done.append((n, res))
        self_check = {'done': done, 'na': na, 'not_done': not_done, 'complete': not sec8 == '' and all(n in got for n, _ in items)}
        if not_done:
            W(f'04 §8: {len(not_done)} checklist items 未実施: {[n for n, _ in not_done]}')

    base = validate(folder, source) if source else None
    if base and not base['ok']:
        errors = base['errors'] + errors
    return {'ok': not errors, 'errors': errors, 'warnings': warnings, 'strict': strict, 'self_check': self_check,
            'chars': {k: len(v) for k, v in f.items()},
            'validate': base and {k: base[k] for k in ('objectives', 'modules', 'minutes')}}


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    p = argparse.ArgumentParser()
    p.add_argument('directory', type=Path)
    p.add_argument('source', type=Path, nargs='?')
    p.add_argument('--quiet', action='store_true')
    args = p.parse_args()
    src = json.loads(args.source.read_text(encoding='utf-8')) if args.source else None
    result = lint(args.directory, src)
    if args.quiet:
        print(json.dumps({'ok': result['ok'], 'errors': len(result['errors']), 'warnings': len(result['warnings'])}))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['ok'] else 1)
