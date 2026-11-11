#!/usr/bin/env python3
"""Run the actual original C++ workflows and batch counts, including CLI errors."""
import argparse,json,os,shutil
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
from image_ccl_build import dependencies
from image_progress import record
def main():
 p=argparse.ArgumentParser();p.add_argument('--cli',action='store_true');a=p.parse_args();b=json.loads((ROOT/'migration/reports/image-ccl-build.json').read_text());spec=json.loads((ROOT/'migration/rewrite/image-ccl-profile.json').read_text());assert b['status']=='BUILT' and digest(ROOT/b['library'])==b['library_sha256'] and all(digest(ROOT/n)==sha for n,sha in b['dependencies'].items());rows=[]
 for binary in b['binaries']:
  assert digest(ROOT/binary['binary'])==binary['sha256'];family=binary['family'];base=ROOT/family/'batchedLabelMarkersAndCompression/images';cases=[str(n) for n in range(1,6)] if not a.cli else ['default-directory','help','missing-b','zero','negative','above-five','noninteger','duplicate','unknown-option','missing-input','truncated-input','unwritable-output','no-GPU']
  for case in cases:
   e=Experiment('I2','CCL-original-'+family,'rocm-CLI' if a.cli else 'rocm-original',case=binary['mode']+'/'+case,sources=[__file__,*dependencies()],parent=b['experiment_id']);write(e.path/'backend.observed.json',capture());inp=e.path/'images';out=e.path/'outputs';cwd=e.path/'work';inp.mkdir();out.mkdir();cwd.mkdir()
   for x in spec['originals']:
    if x['source'].startswith(family+'/'):shutil.copyfile(ROOT/x['source'],inp/(ROOT/x['source']).name)
   command=[str(ROOT/binary['binary'])];env={};expected=0
   if not a.cli:command+=['-b',case,'--input-dir',str(inp),'--output-dir',str(out)]
   elif case=='default-directory':out=inp
   elif case=='help':command+=['--help']
   else:
    command+=['--input-dir',str(inp),'--output-dir',str(out)];expected=1
    flags={'missing-b':['-b'],'zero':['-b','0'],'negative':['-b','-1'],'above-five':['-b','6'],'noninteger':['-b','2x'],'duplicate':['-b','1','-b','2'],'unknown-option':['--unknown']};command+=flags.get(case,[])
    first=inp/'lena_512x512_8u.raw'
    if case=='missing-input':first.unlink()
    elif case=='truncated-input':first.write_bytes(first.read_bytes()[:-1])
    elif case=='unwritable-output':out.rmdir();out.write_text('file blocks output directory')
    elif case=='no-GPU':env['HIP_VISIBLE_DEVICES']=''
   rc=e.command(command,'actual-C++-'+case,cwd=cwd,env=env,timeout=300);r=dict(family=family,mode=binary['mode'],case=case,return_code=rc,expected_return_code=expected,outputs=str(out.relative_to(ROOT)),inputs=str(inp.relative_to(ROOT)),experiment_id=e.id,binary=binary,build=b,stdout=e.commands[-1]['stdout'],stderr=e.commands[-1]['stderr']);write(e.path/'run.json',r);r['evidence']=e.finish('EXECUTED' if rc==expected else 'CLI_GAP' if a.cli else 'RUNTIME_ERROR');rows.append(r);write(ROOT/('migration/reports/image-ccl-cli.json' if a.cli else 'migration/reports/image-ccl-originals.json'),rows);record('I2',family+'/'+binary['mode']+'/'+case+'完整C++ '+('CLI' if a.cli else '输入/文件')+'执行rc='+str(rc)+'；全文件集合/像素/实际诊断后验检查。',[r['evidence']]);print(family,binary['mode'],case,rc,flush=True)
 return 0
if __name__=='__main__':raise SystemExit(main())
