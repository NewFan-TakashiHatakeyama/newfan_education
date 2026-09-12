"""Refresh bundled curriculum examples, mirror a skill, and produce a portable ZIP."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

def package(skill, curricula, destination, output):
    for file in ['SKILL.md','scripts/validate_curriculum.py']:
        if not (skill/file).is_file():
            raise ValueError('Missing skill resource: '+file)
    subprocess.run([sys.executable, str(skill/'scripts/validate_curriculum.py'),str(curricula/'S001'),str(curricula/'source-v1.json')], check=True)
    assets=skill/'assets'
    assets.mkdir(exist_ok=True)
    for filename in ['source-v1.json','catalog.json']:
        shutil.copy2(curricula/filename,assets/filename)
    golden=assets/'reference-S001'
    golden.mkdir(exist_ok=True)
    for filename in ['01-design.md','02-learner.md','03-exercises.md','04-instructor.md','curriculum.json']:
        shutil.copy2(curricula/'S001'/filename,golden/filename)
    subprocess.run([sys.executable,str(skill/'scripts/test_workflow.py')],check=True)
    files=[p for p in skill.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc']
    if destination.resolve()!=skill.resolve():
        destination.mkdir(parents=True,exist_ok=True)
        for file in files:
            target=destination/file.relative_to(skill)
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(file,target)
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
        for file in files:
            relative=file.relative_to(skill)
            if relative.parts[0]=='agents':
                continue
            archive.write(file,Path('ai-business-curriculum')/relative)
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None or 'ai-business-curriculum/SKILL.md' not in archive.namelist():
            raise ValueError('Invalid package')
    return {'zip':str(output.resolve()),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'files':len(files),'mirror':str(destination.resolve()),'claude_generation_tested':False}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--skill',type=Path,required=True)
    p.add_argument('--curricula',type=Path,required=True)
    p.add_argument('--mirror',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(package(args.skill,args.curricula,args.mirror,args.output),ensure_ascii=False,indent=2))
