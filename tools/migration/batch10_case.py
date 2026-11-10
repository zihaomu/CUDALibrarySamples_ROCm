#!/usr/bin/env python3
"""Drive the real GPU JPEG CLI; retain every command, output and exit code."""
import argparse,json,pathlib,os,subprocess,sys
from catalog import ROOT
p=argparse.ArgumentParser();p.add_argument('--binary',required=True);p.add_argument('--source',required=True);p.add_argument('--case',required=True);p.add_argument('--output',required=True);a=p.parse_args();d=pathlib.Path(a.output);fixture=ROOT/'tests/fixtures/batch10';corpus=ROOT/'nvJPEG/nvJPEG-Decoder/input_images';post='/Image-Resize' in a.source;water='WaterMark' in a.source;calls=[];outputs=[]
def invoke(args,code=0,meta=None):
 i=len(calls);out=d/('call'+str(i));out.mkdir();args=[str(x) for x in args];cmd=[a.binary]+args
 if '-o' not in args and code==0:cmd+=['-o',str(out/'output')]
 r=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=180);log=r.stdout+r.stderr;(out/'run.log').write_text(log);record=dict(command=cmd,expected_return_code=code,return_code=r.returncode,log=str((out/'run.log').relative_to(d)),passed=r.returncode==code and ('RESULT status=PASS' not in log if code else 'Usage:' in log or 'RESULT status=PASS' in log),parameters=meta or {});calls.append(record)
 if not record['passed']:raise RuntimeError(json.dumps(record)+'\n'+log[-1200:])
 for raw in out.rglob('*.raw'):
  metadata=raw.with_name(raw.name+'.json');outputs.append(dict(raw=str(raw.relative_to(d)),metadata=json.loads(metadata.read_text()),parameters=meta or {}))
 return log
try:
 case=a.case
 if case=='original-corpus':invoke(['-i',corpus,'-fmt','rgbi','-b',3],meta=dict(original_corpus=True))
 elif case=='formats-scale':
  for scale in [1,2,4,8]:
   formats=['rgbi'] if post else ['y','yuv','nv12','rgb','rgbi','bgr','bgri','unchanged','yuy2']
   for fmt in formats:invoke(['-i',fixture/('422.jpg' if fmt=='yuy2' else '420.jpg'),'-fmt',fmt,'-scale',scale],meta=dict(format=fmt,scale=scale))
  if not post:
   for scale in [1,2,4,8]:invoke(['-i',fixture/'gray.jpg','-fmt','yuv','-scale',scale],meta=dict(gray37=True,scale=scale))
 elif case=='roi-boundary':
  for roi in ['1,2,37,29','127,95,2,2','0,0,129,97']:invoke(['-i',fixture/'444.jpg','-fmt','rgbi','-roi',roi],meta=dict(roi=[int(x) for x in roi.split(',')]))
  for roi in ['-1,0,10,10','128,96,2,2']:invoke(['-i',fixture/'444.jpg','-fmt','rgbi','-roi',roi],2)
 elif case=='batch-multi-instance':
  log=invoke(['-i',corpus,'-fmt','rgbi','-b',3,'-t',17,'-j',2,'-w',1],meta=dict(expected_decoded=17,instances=2));assert 'decoded=17' in log and 'instances=2' in log
 elif case=='invalid-cli':
  invoke(['-h'])
  for args in [[],['-i'],['-i','x','-fmt','bad'],['-i','x','-scale',3],['-i','x','-t',0],['-i','x','-t','1x'],['-i','x','-device',-1],['-i','x','-t','999999999999999999999'],['-bad','x']]:invoke(args,2)
  invoke(['-i',fixture/'bad.jpg'],1);invoke(['-i',fixture/'missing.jpg'],1);invoke(['-backend','hardware','-i',fixture/'progressive.jpg'],3)
  if not post:invoke(['-backend','hardware','-i',fixture/'444.jpg','-fmt','nv12'],3)
 elif case=='postprocess':
  if post:
   for alpha in ([0,50,255] if water else [50]):invoke(['-i',fixture/'444.jpg','-fmt','rgbi','-rw',40,'-rh',32,'-alpha',alpha,'-q',91],meta=dict(resize=[40,32],alpha=alpha,quality=91))
  else:invoke(['-i',fixture/'444.jpg'],meta=dict(bmp_output=True))
 elif case=='python-integration' and post:
  invoke(['-i',fixture/'444.jpg','-fmt','rgbi','-rw',40,'-rh',32,'-q',91],meta=dict(resize=[40,32],quality=91,python_file_roundtrip=True))
 elif case=='python-integration':
  # Every original unittest runs against an actual compiled ROCm decoder CLI.
  script=ROOT/'rocm/ported/nvJPEG/nvJPEG-Decoder/tests/test_decoder.py'
  if not script.exists():script=ROOT/'nvJPEG/nvJPEG-Decoder/tests/test_decoder.py'
  cmd=[sys.executable,str(script),a.binary];r=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=300);(d/'python.log').write_text(r.stdout+r.stderr);calls.append(dict(command=cmd,return_code=r.returncode,expected_return_code=0,passed=r.returncode==0,log='python.log'));assert r.returncode==0,(r.stdout+r.stderr)[-4500:]
 else:raise ValueError(case)
 (d/'case.json').write_text(json.dumps(dict(status='PASSED',source=a.source,case=case,calls=calls,outputs=outputs),indent=2)+'\n');print('GPU CLI integration passed',case,len(calls),'calls',len(outputs),'outputs')
except Exception as e:
 (d/'case.json').write_text(json.dumps(dict(status='FAILED',source=a.source,case=a.case,reason=str(e),calls=calls,outputs=outputs),indent=2)+'\n');print(str(e));raise SystemExit(1)
