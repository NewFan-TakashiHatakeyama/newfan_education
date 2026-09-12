"""Validate source identity and curriculum coverage; does not grade pedagogical quality."""
import argparse
import json
from pathlib import Path

def validate(folder, source):
    data = json.loads((folder/'curriculum.json').read_text(encoding='utf-8'))
    errors = []
    def check(condition, message):
        if not condition:
            errors.append(message)
    record = next((s for s in source['skills'] if s['id'] == data['skill_id']), None)
    check(record is not None, 'Unknown skill ID')
    check(data['source_sha256'] == source['sha256'], 'Source hash mismatch')
    if record:
        check(data['skill_name'] == record['name'], 'Skill name mismatch')
    required = ['01-design.md','02-learner.md','03-exercises.md','04-instructor.md']
    check(set(data['files']) == set(required), 'Required deliverables mismatch')
    contents = {}
    for name in required:
        file = folder/name
        check(file.is_file(), f'Missing {name}')
        contents[name] = file.read_text(encoding='utf-8') if file.is_file() else ''
    objectives = {o['id']:o for o in data['objectives']}
    check(len(objectives) == len(data['objectives']), 'Duplicate objective ID')
    for key in ['modules','assessments']:
        check(len({x['id'] for x in data[key]}) == len(data[key]), f'Duplicate {key} ID')
    for level in [1,2,3]:
        check(any(o['level'] == level for o in objectives.values()), f'No Lv{level} objectives')
        check(any(a['level'] == level for a in data['assessments']), f'No Lv{level} assessment')
    taught, assessed, total = set(), set(), 0
    for module in data['modules']:
        check(module['id'] in contents['02-learner.md'], f'No learner content for {module["id"]}')
        check(bool(module['evidence']), f'No module evidence: {module["id"]}')
        check(set(module['minutes']) == {'explanation','worked_example','practice','review','assessment'}, 'Time components incomplete')
        check(all(isinstance(v,int) and v >= 0 for v in module['minutes'].values()), 'Invalid duration')
        total += sum(module['minutes'].values())
        taught.update(module['objectives'])
        for oid in module['objectives']:
            check(oid in objectives and objectives[oid]['level'] == module['level'], f'Unknown or wrong-level objective {oid}')
    for assessment in data['assessments']:
        assessed.update(assessment['objectives'])
        check(bool(assessment['evidence']) and bool(assessment['pass_rule']), f'Incomplete assessment {assessment["id"]}')
        for name in ['03-exercises.md','04-instructor.md']:
            check(assessment['id'] in contents[name], f'No assessment reference {assessment["id"]} in {name}')
        for oid in assessment['objectives']:
            check(oid in objectives and objectives[oid]['level'] == assessment['level'], f'Unknown or wrong-level assessment objective {oid}')
    check(taught == set(objectives), 'Untaught/unknown objectives: '+str(taught ^ set(objectives)))
    check(assessed == set(objectives), 'Unassessed/unknown objectives: '+str(assessed ^ set(objectives)))
    check(total == data['total_minutes'], f'Total time mismatch: {total}')
    for oid, obj in objectives.items():
        check(obj['source_field'] == f'Lv{obj["level"]}', f'Wrong source level: {oid}')
        check(oid in contents['01-design.md'], f'No design entry: {oid}')
    for key in ['source_alignment','case_solvable','answers_checked']:
        check(data['review'].get(key) is True, f'Content review not recorded: {key}')
    return {'ok':not errors, 'errors':errors, 'objectives':len(objectives), 'modules':len(data['modules']), 'minutes':total}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    result = validate(args.directory, json.loads(args.source.read_text(encoding='utf-8')))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['ok'] else 1)
