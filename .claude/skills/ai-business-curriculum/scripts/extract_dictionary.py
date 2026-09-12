"""Read skill dictionary and workbook context using only the Python standard library."""
import argparse
import hashlib
import json
import posixpath
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'

def extract(path):
    with zipfile.ZipFile(path) as z:
        strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            strings = [''.join(n.itertext()) for n in ET.fromstring(z.read('xl/sharedStrings.xml'))]
        rels = {r.attrib['Id']: r.attrib['Target'] for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        sheets = {}
        for node in ET.fromstring(z.read('xl/workbook.xml')).find('s:sheets', NS):
            target = rels[node.attrib[REL]]
            member = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
            rows = []
            for row in ET.fromstring(z.read(member)).findall('s:sheetData/s:row', NS):
                cells = {}
                for cell in row:
                    address = cell.attrib.get('r')
                    if not address:
                        continue
                    value = cell.find('s:v', NS)
                    if cell.attrib.get('t') == 'inlineStr':
                        text = ''.join(t.text or '' for t in cell.findall('.//s:t', NS))
                    elif value is not None:
                        text = strings[int(value.text)] if cell.attrib.get('t') == 's' else value.text
                    else:
                        text = None
                    if text is not None:
                        cells[address] = text
                if cells:
                    rows.append({'row': int(row.attrib['r']), 'cells': cells})
            sheets[node.attrib['name']] = rows
    names = [name for name in sheets if 'スキル辞書' in name]
    if len(names) != 1:
        raise ValueError('Expected exactly one スキル辞書 sheet')
    records = []
    columns = {'B':'axis', 'C':'category', 'D':'name', 'E':'definition', 'F':'Lv1', 'G':'Lv2', 'H':'Lv3', 'I':'evidence', 'J':'tasks', 'K':'legacy', 'L':'source_ids', 'M':'notes'}
    for row in sheets[names[0]]:
        n = row['row']
        cells = row['cells']
        skill_id = cells.get(f'A{n}', '')
        if not re.fullmatch(r'S\d{3}', skill_id):
            continue
        records.append({'id':skill_id, 'sheet':names[0], 'range':f'A{n}:M{n}', **{field:cells.get(f'{col}{n}', '') for col, field in columns.items()}})
    ids = [r['id'] for r in records]
    expected = {f'S{i:03}' for i in range(1,107)}
    if len(ids) != len(set(ids)) or set(ids) != expected:
        raise ValueError(f'Dictionary IDs do not match S001–S106: {len(ids)} rows; missing={sorted(expected-set(ids))}')
    return {'source_file':str(path.resolve()), 'sha256':hashlib.sha256(path.read_bytes()).hexdigest(), 'skills':records, 'sheets':sheets}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = extract(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'skills':len(result['skills']), 'sheets':len(result['sheets']), 'sha256':result['sha256']}, ensure_ascii=False))
