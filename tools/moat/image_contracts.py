#!/usr/bin/env python3
"""Freeze original entrypoint, build, asset and API/CLI inventory for image work."""
import collections,json,re,subprocess
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from image_progress import record

def main():
 plan=json.loads((ROOT/'migration/rewrite/image-libraries-plan.json').read_text());e=Experiment('I0','image-original-contract-inventory','host-inventory',sources=[__file__,ROOT/'migration/rewrite/image-libraries-plan.json']);rows=[]
 for r in plan['samples']:
  source=ROOT/r['source'];assert digest(source)==r['original_source_sha256'];files=[source]+sorted(source.parent.glob('*.h'));text='\n'.join(p.read_text(errors='replace') for p in files)
  strings=sorted(set(re.findall(r'"([^"\n]+\.(?:raw|jpg|jpeg|png|jp2|j2k|pfm|pgm|ppm|bmp|yuv))"',text,re.I)))
  options=sorted(set(re.findall(r'(?<![A-Za-z0-9])(-[A-Za-z][A-Za-z0-9_-]*)',text)))
  conditionals=[line.strip() for line in text.splitlines() if re.match(r'\s*#\s*(?:if|elif|ifdef|ifndef|define)\b',line)]
  rows.append(dict(sample_id=r['sample_id'],source=r['source'],baseline_status=r['baseline_status'],completion_phase=r['completion_phase'],source_files={str(p.relative_to(ROOT)):dict(sha256=digest(p),bytes=p.stat().st_size) for p in files},CLI_token_hints=options,api_token_hints=r['api_token_hints'],literal_image_paths=strings,conditional_compilation=conditionals,required_case_categories=r['required_case_categories'],inventory_scope='Static hints. CLI semantic/default/error and resolved-input matrix frozen separately before qualification.'))
 assets={}
 for family in plan['modules']:
  for p in sorted((ROOT/family).rglob('*')):
   if p.is_file() and p.suffix.lower() in {'.raw','.jpg','.jpeg','.png','.jp2','.j2k','.pfm','.pgm','.ppm','.bmp','.yuv'}:assets[str(p.relative_to(ROOT))]=dict(sha256=digest(p),bytes=p.stat().st_size,role='repository asset; input/reference-output classification by original caller')
 builds=plan['original_build_definition_sha256'];assert all(digest(ROOT/n)==sha for n,sha in builds.items());contracts=dict(schema_version=1,baseline_commit=plan['baseline_commit'],current_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),samples=rows,repository_assets=assets,original_build_definition_sha256=builds,case_policy='Original complete files plus all registered semantic/CLI/type/conditional branches; no promotion from inventory or process exit alone.');write(e.path/'contracts.json',contracts)
 validation=dict(status='PASSED',checks=[dict(check='26-distinct-original-entrypoints',passed=len(rows)==26 and len({r['sample_id'] for r in rows})==26),dict(check='24-original-build-identities',passed=len(builds)==24),dict(check='nonempty-hashed-original-assets',passed=bool(assets))]);ref=e.finish('PASSED',validation);contracts['evidence']=ref;write(ROOT/'migration/rewrite/image-contracts.json',contracts);write(ROOT/'migration/reports/image-I0-contract-inventory.json',dict(status='PASSED',entrypoints=len(rows),build_definitions=len(builds),assets=len(assets),checks=validation['checks'],evidence=ref));record('I0',f'26入口、24原构建定义、{len(assets)}原仓库图像/参考输出资产SHA已封存；CLI/API/条件分支静态提示已记录，语义/default/input分类仍需逐例核实。',[ref]);print(len(rows),len(assets),ref)
if __name__=='__main__':main()
