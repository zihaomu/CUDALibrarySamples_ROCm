#!/usr/bin/env python3
"""Produce reviewable HIPIFY drafts while preserving manually corrected ports."""
import argparse,concurrent.futures,hashlib,json,pathlib,subprocess
from catalog import ROOT,BASE

def main():
 p=argparse.ArgumentParser();p.add_argument('--families',nargs='+',default=['cuBLAS','cuBLASLt','cuSPARSE','cuSOLVER','cuFFT','cuRAND']);a=p.parse_args()
 path=ROOT/'migration/conversions.json';old=json.loads(path.read_text()) if path.exists() else {};record={v['source']:v for v in old.get('files',[])}
 names=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],cwd=ROOT,text=True).splitlines()
 files=[n for n in names if any(n.startswith(f+'/') for f in a.families) and pathlib.Path(n).suffix in {'.c','.cu','.cpp','.h','.hpp','.cuh','.hxx','.inl'}]
 def one(name):
  src=ROOT/name;dst=ROOT/'rocm/ported'/name;sha=hashlib.sha256(src.read_bytes()).hexdigest();prior=record.get(name)
  if prior and dst.exists():
   if hashlib.sha256(dst.read_bytes()).hexdigest()!=prior['generated_sha256']:return {**prior,'manual_edit_preserved':True}
   if prior['source_sha256']==sha:return prior
  dst.parent.mkdir(parents=True,exist_ok=True)
  run=subprocess.run(['hipify-perl','-experimental',str(src)],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  dst.write_text(run.stdout)
  return {'source':name,'source_sha256':sha,'ported_source':str(dst.relative_to(ROOT)),'generated_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'tool':'hipify-perl -experimental','return_code':run.returncode,'warnings':run.stderr}
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for item in pool.map(one,files):record[item['source']]=item
 path.write_text(json.dumps({'upstream_commit':BASE,'files':list(record.values())},indent=2)+'\n');print('Converted/protected files:',len(files),flush=True)
if __name__=='__main__':main()
