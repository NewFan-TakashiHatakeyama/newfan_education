"""Select a bounded, source-labelled skill context. Python standard library only."""
import argparse
import json
from pathlib import Path

def select(source, skill_id):
    skill = next((s for s in source['skills'] if s['id'] == skill_id), None)
    if not skill:
        raise ValueError('Unknown skill: '+skill_id)
    tasks = set(skill.get('tasks','').replace(' ', '').split(',')) - {''}
    matches, roles, related_ids = {}, set(), set()
    for name, rows in source['sheets'].items():
        if not name.startswith('08_'):
            continue
        for row in rows:
            c, n = row['cells'], row['row']
            if c.get(f'E{n}') == skill_id or c.get(f'A{n}') in tasks:
                related_ids.add(c.get(f'E{n}'))
                for col in ['C','D']:
                    roles.update(c.get(f'{col}{n}', '').replace(' ', '').split(','))
    for name, rows in source['sheets'].items():
        chosen = []
        for row in rows:
            c, n = row['cells'], row['row']
            if name.startswith(('02_','08_','09_')):
                keep = c.get(f'A{n}') in tasks or c.get(f'E{n}') == skill_id
            elif name.startswith('06_'):
                keep = c.get(f'A{n}') in roles
            elif name.startswith('28_'):
                keep = c.get(f'B{n}') == skill_id
            else:
                keep = False
            if keep:
                chosen.append(row)
        if chosen:
            matches[name] = [row for row in rows if row['row'] <= 3] + chosen
    return {'source_file':source['source_file'],'source_sha256':source['sha256'],'skill':skill,'related_skills':[s for s in source['skills'] if s['id'] in related_ids and s['id'] != skill_id],'context':matches,'available_sheets':list(source['sheets'])}

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path)
    p.add_argument('skill_id')
    p.add_argument('output', type=Path)
    args = p.parse_args()
    result = select(json.loads(args.source.read_text(encoding='utf-8')), args.skill_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'skill':args.skill_id,'tasks':result['skill']['tasks'],'context_sheets':len(result['context'])},ensure_ascii=False))
