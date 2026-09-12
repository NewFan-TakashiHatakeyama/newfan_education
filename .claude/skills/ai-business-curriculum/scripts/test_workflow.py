"""Portable smoke/regression tests for extraction, selection, generation, lint, source check and fetch helpers."""
import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path

from select_context import select
from validate_curriculum import validate
from lint_curriculum import lint, expand_tails, objective_ids
from gen_from_spec import build, tables, validate_spec, checklist_items
from source_check import check
from fetch_source import grep, json_to_text, normalize_url

BASE = Path(__file__).resolve().parents[1]


def s001_spec(data):
    return {'skill_id': 'S001', 'date': '2026-09-11',
            'objectives': [{'id': o['id'], 'behavior': o['behavior']} for o in data['objectives']],
            'modules': [{'id': m['id'], 'level': m['level'], 'objectives': m['objectives'], 'title': 't', 'evidence': m['evidence'],
                         'exercise': m['exercise'], 'assessment': 'A' + str(m['level']),
                         'minutes': [m['minutes'][k] for k in ('explanation', 'worked_example', 'practice', 'review', 'assessment')]} for m in data['modules']],
            'assessments': [{'id': a['id'], 'level': a['level'], 'objectives': a['objectives'], 'observation_points': ['x'], 'evidence': a['evidence'],
                             'pass_rule': a['pass_rule'], 'critical_errors': a['critical_errors']} for a in data['assessments']]}


class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads((BASE / 'assets/source-v1.json').read_text(encoding='utf-8'))
        cls.golden = BASE / 'assets/reference-S001'

    def _copy_golden(self, folder):
        for file in self.golden.iterdir():
            if file.is_file():
                (folder / file.name).write_bytes(file.read_bytes())

    def test_dictionary_complete(self):
        self.assertEqual({s['id'] for s in self.source['skills']}, {f'S{i:03}' for i in range(1, 107)})
        self.assertEqual(len(self.source['skills']), 106)

    def test_s001_reference_passes(self):
        self.assertTrue(validate(self.golden, self.source)['ok'])

    def test_s001_reference_lints(self):
        result = lint(self.golden, self.source)
        self.assertTrue(result['ok'], result['errors'])
        self.assertFalse(result['strict'])

    def test_distinct_skill_context(self):
        for skill_id in ['S001', 'S003', 'S037', 'S106']:
            result = select(self.source, skill_id)
            self.assertEqual(result['skill']['id'], skill_id)
            self.assertTrue(result['skill']['Lv3'])
            self.assertTrue(result['context'])
        with self.assertRaises(ValueError):
            select(self.source, 'S999')

    def test_changed_source_rejected(self):
        source = copy.deepcopy(self.source)
        source['sha256'] = 'different'
        self.assertFalse(validate(self.golden, source)['ok'])

    def test_unassessed_objective_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self._copy_golden(folder)
            data = json.loads((folder / 'curriculum.json').read_text(encoding='utf-8'))
            data['assessments'][0]['objectives'].pop()
            (folder / 'curriculum.json').write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
            self.assertTrue(any('Unassessed' in e for e in validate(folder, self.source)['errors']))

    def test_wrong_time_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self._copy_golden(folder)
            data = json.loads((folder / 'curriculum.json').read_text(encoding='utf-8'))
            data['total_minutes'] += 30
            (folder / 'curriculum.json').write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
            self.assertTrue(any('Total time' in e for e in validate(folder, self.source)['errors']))

    def test_lint_detects_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self._copy_golden(folder)
            data = json.loads((folder / 'curriculum.json').read_text(encoding='utf-8'))
            data['modules'][0]['minutes']['practice'] += 10
            data['total_minutes'] += 10
            data['assessments'][0]['observation_points'] = ['存在しない観点']
            (folder / 'curriculum.json').write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
            text = (folder / '03-exercises.md').read_text(encoding='utf-8')
            (folder / '03-exercises.md').write_text(text + '\n（作成中）\n前提：記入。\n', encoding='utf-8')
            d04 = (folder / '04-instructor.md').read_text(encoding='utf-8')
            (folder / '04-instructor.md').write_text(d04.replace('### E07 停止通知の完成例', '### 停止通知の完成例'), encoding='utf-8')
            result = lint(folder, self.source)
            self.assertFalse(result['ok'])
            joined = ' '.join(result['errors'])
            for needle in ['M01', '存在しない観点', 'placeholder', '：記入。']:
                self.assertIn(needle, joined)
            self.assertTrue(any('### E07' in w for w in result['warnings']), result['warnings'])

    def test_spec_roundtrip(self):
        data = json.loads((self.golden / 'curriculum.json').read_text(encoding='utf-8'))
        spec = s001_spec(data)
        built = build(spec, self.source)
        self.assertEqual(built['total_minutes'], data['total_minutes'])
        self.assertEqual([a['minutes'] for a in built['assessments']], [50, 100, 150])
        self.assertEqual(built['source_sha256'], self.source['sha256'])
        self.assertEqual(built['review']['self_check'], 'pending')
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / 'curriculum.json').write_text(json.dumps(built, ensure_ascii=False), encoding='utf-8')
            for name in ['01-design.md', '02-learner.md', '03-exercises.md', '04-instructor.md']:
                (folder / name).write_bytes((self.golden / name).read_bytes())
            self.assertTrue(validate(folder, self.source)['ok'])
        md = tables(spec, built)
        self.assertIn('| M01 |', md)
        self.assertIn('合計1,800分', md)
        self.assertIn('| 28 |', md)
        with self.assertRaises(ValueError):
            build({**spec, 'objectives': [{'id': 'S002-L1-O01', 'behavior': 'x'}]}, self.source)

    def test_spec_validation_lists_all_problems(self):
        data = json.loads((self.golden / 'curriculum.json').read_text(encoding='utf-8'))
        spec = s001_spec(data)
        spec['objectives'].append({'id': 'S001-L2-O99', 'behavior': 'orphan'})
        spec['modules'][0]['objectives'].append('S001-L3-O01')
        spec['modules'][1]['minutes'] = [10, 10]
        spec['assessments'][2]['observation_points'] = []
        spec['cards'] = [{'id': 'K01', 'title': 'no registry'}]
        issues = validate_spec(spec, self.source)
        joined = ' '.join(issues)
        for needle in ['S001-L2-O99 is not taught', 'S001-L3-O01 is Lv3 but module is Lv1', 'minutes must be 5', 'A3: observation_points is empty', 'K01 needs "registry"']:
            self.assertIn(needle, joined, issues)
        with self.assertRaises(ValueError):
            build(spec, self.source)

    def test_tables_skeletons(self):
        data = json.loads((self.golden / 'curriculum.json').read_text(encoding='utf-8'))
        spec = s001_spec(data)
        spec.update({'scope': {'owns': 'a', 'assumes': 'b', 'delegates': 'c'}, 'roles': [{'id': 'R01', 'actor': 'x', 'role': 'y'}],
                     'templates': [{'id': 'T1', 'name': 'n', 'columns': ['c1', 'c2']}], 'cards': [{'id': 'K01', 'registry': 'gdpr', 'title': 't'}]})
        built = build(spec, self.source)
        self.assertEqual(built['templates'], ['T1'])
        self.assertEqual(built['cards'][0]['registry'], 'gdpr')
        md = tables(spec, built)
        for needle in ['| R01 | x | y |', '### T1 n', '| c1 | c2 |', '### K01 t（registry: gdpr）', '本講座が担うこと：a', '### E01', '| 1 | ', '| 28 | ']:
            self.assertIn(needle, md)
        self.assertEqual(len(checklist_items()), 28)

    def test_strict_lint_requires_self_check_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self._copy_golden(folder)
            data = json.loads((folder / 'curriculum.json').read_text(encoding='utf-8'))
            data['review']['self_check'] = 'pending'
            (folder / 'curriculum.json').write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
            result = lint(folder, self.source)
            self.assertTrue(result['strict'])
            self.assertTrue(any('§8' in e for e in result['errors']), result['errors'])
            rows = ['## 8. 教材の内容品質レビュー記録', '', '| # | 項目 | 結果 | 確認方法・根拠 |', '|---|---|---|---|']
            for n, text in checklist_items():
                rows.append(f'| {n} | {text} | {"未実施（試行なし）" if n == 27 else "済"} | 実際に確認した根拠をここに書く |')
            d04 = (folder / '04-instructor.md').read_text(encoding='utf-8')
            (folder / '04-instructor.md').write_text(d04 + '\n' + '\n'.join(rows) + '\n', encoding='utf-8')
            result = lint(folder, self.source)
            self.assertFalse(any('§8' in e for e in result['errors']), result['errors'])
            self.assertTrue(result['self_check']['complete'])
            self.assertEqual(len(result['self_check']['done']), 27)
            self.assertEqual([n for n, _ in result['self_check']['not_done']], [27])

    def test_date_table_recomputed(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self._copy_golden(folder)
            block = ('\n### 日付計算表（テスト）\n\n| 名称 | 日付 | 導出 |\n|---|---|---|\n| 基準日 | 2026-09-14（月） | — |\n'
                     '| 再判定期限 | 2026-09-24（木） | 基準日 ＋ 10暦日 |\n| 誤り | 2026-09-20（日） | 基準日 ＋ 7暦日 |\n| 曜日誤り | 2026-10-05（火） | 基準日 ＋ 3週間 |\n')
            d03 = (folder / '03-exercises.md').read_text(encoding='utf-8')
            (folder / '03-exercises.md').write_text(d03 + block, encoding='utf-8')
            result = lint(folder, self.source)
            errs = [e for e in result['errors'] if '日付計算表' in e]
            self.assertEqual(len(errs), 2, result['errors'])
            self.assertTrue(any('誤り: 基準日＋7暦日 = 2026-09-21' in e for e in errs), errs)
            self.assertTrue(any('曜日誤り' in e and '月曜' in e for e in errs), errs)

    def test_objective_id_expansion(self):
        self.assertEqual(expand_tails('O01〜O04'), {'O01', 'O02', 'O03', 'O04'})
        self.assertEqual(expand_tails('O04、O05'), {'O04', 'O05'})
        self.assertEqual(objective_ids('目標S002-L3-O04、O05。180分'), {'S002-L3-O04', 'S002-L3-O05'})
        self.assertEqual(objective_ids('目標S002-L2-O01〜O03。'), {'S002-L2-O01', 'S002-L2-O02', 'S002-L2-O03'})
        self.assertEqual(objective_ids('目標S001-L1-O01、S001-L1-O02。'), {'S001-L1-O01', 'S001-L1-O02'})

    def test_source_check(self):
        result = check(self.source, 'S002', today='2026-09-12')
        self.assertTrue(result['legal_content'])
        ids = {m['id'] for m in result['matched']}
        self.assertIn('eu-ai-act', ids)
        self.assertIn('appi-breach', ids)
        self.assertFalse(any(m['stale'] for m in result['matched']))
        entry = next(m for m in result['matched'] if m['id'] == 'appi-breach')
        self.assertTrue(entry['cards'] and entry['scope'] and entry['not_covered'])
        stale = check(self.source, 'S002', today='2027-06-01')
        self.assertTrue(all(m['stale'] for m in stale['matched']))
        event = check(self.source, 'S002', today='2026-12-03')
        eu = next(m for m in event['matched'] if m['id'] == 'eu-ai-act')
        self.assertTrue(eu['stale'] and any('event 2026-12-02' in r for r in eu['stale_reasons']))
        api = check(self.source, 'S037', today='2026-09-12')
        self.assertEqual(api['matched'], [])
        self.assertFalse(api['legal_content'])
        us = next(e for e in json.loads((BASE / 'references/source-registry.json').read_text(encoding='utf-8'))['entries'] if e['id'] == 'us-state')
        self.assertEqual(us['facts'], [])
        self.assertTrue(us['unverified'])

    def test_fetch_helpers(self):
        self.assertTrue(normalize_url('https://laws.e-gov.go.jp/law/507AC0000000053').startswith('https://laws.e-gov.go.jp/api/2/law_data/507AC0000000053'))
        law = {'law_full_text': {'tag': 'Law', 'children': [
            {'tag': 'Article', 'children': [{'tag': 'ArticleTitle', 'children': ['第一条']}, {'tag': 'Paragraph', 'children': [{'tag': 'Sentence', 'children': ['目的の条文。']}]}]},
            {'tag': 'Article', 'children': [{'tag': 'ArticleTitle', 'children': ['第二条']}, {'tag': 'Paragraph', 'children': [{'tag': 'Sentence', 'children': ['定義の条文。']}]}]}]}}
        lines = json_to_text(law).splitlines()
        self.assertEqual(len(lines), 4)
        self.assertTrue(lines[0].startswith('第一条') and lines[2].startswith('第二条'))
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 't.txt'
            p.write_text('x' * 500 + '第七条 活用事業者の責務 ' + 'y' * 500 + '\n' + '第七条\n' * 50, encoding='utf-8')
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                grep(p, ['第七条'], window=20, max_matches=5)
            text = out.getvalue()
            self.assertIn('活用事業者', text)
            self.assertIn('showed 5', text)
            self.assertLess(len(text), 1200)


if __name__ == '__main__':
    unittest.main()
