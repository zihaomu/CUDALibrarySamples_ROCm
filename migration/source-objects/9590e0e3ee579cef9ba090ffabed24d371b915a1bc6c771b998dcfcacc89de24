#!/usr/bin/env python3
import argparse,json,shutil,struct,sys
from pathlib import Path
from experiment import ROOT,Experiment,write
from sparse_binding_reference import validate
p=argparse.ArgumentParser();p.add_argument('--single',nargs=3);args=p.parse_args()
if args.single:
 src,out,report=args.single
 try:r=validate(src,out)
 except Exception as error:r=dict(status='FAILED',error=str(error),checks=[dict(check='complete-parse',passed=False)])
 write(report,r);raise SystemExit(0 if r['status']=='FAILED' else 1)
run=json.loads((ROOT/'migration/reports/rewrite-sparse-binding-rocm.json').read_text())['cuDSS/fortran/residual::residual.f90/layout'];modes=['solution','padding','permutation','query-byte-count','missing-solve-phase','factor-values','RHS-mutated','info','trailing-byte','truncated-Fortran-X'];results=[]
for mode in modes:
 e=Experiment('R5','sparse-binding-negative/'+mode,'cpu-negative',case=run['case'],sources=[__file__,ROOT/'tools/moat/sparse_binding_reference.py'],parent=run['experiment_id'],comparison_id=run['comparison_id']);shutil.copytree(ROOT/run['input_snapshot'],e.path/'inputs');shutil.copytree(ROOT/run['output'],e.path/'outputs');out=e.path/'outputs'
 if validate(e.path/'inputs',out)['status']!='PASSED':raise RuntimeError('injection needs valid baseline')
 field={'solution':'solution','padding':'solution','permutation':'permutation','query-byte-count':'fortran_query_bytes','missing-solve-phase':'phase','factor-values':'factor_values','RHS-mutated':'B_after','info':'info','trailing-byte':'solution','truncated-Fortran-X':'fortran_X'}[mode];path=out/('b0_'+field+'.bin');data=bytearray(path.read_bytes())
 if mode in ['solution','padding','factor-values','RHS-mutated']:
  offset=5*8 if mode=='padding' else 0;struct.pack_into('<d',data,offset,struct.unpack_from('<d',data,offset)[0]+1)
 elif mode=='missing-solve-phase':data=data[:-4]
 elif mode=='trailing-byte':data+=b'\0'
 elif mode=='truncated-Fortran-X':data=data[:-1]
 elif mode=='query-byte-count':struct.pack_into('<Q',data,0,0)
 elif mode=='info':struct.pack_into('<i',data,0,1)
 else:struct.pack_into('<i',data,0,-1)
 path.write_bytes(data);rc=e.command([sys.executable,__file__,'--single',str(e.path/'inputs'),str(out),str(e.path/'rejection.json')],'reject-'+mode);row=dict(mode=mode,passed=rc==0,parent_run=run['experiment_id']);row['evidence']=e.finish('PASSED' if rc==0 else 'VALIDATOR_GAP',dict(checks=[dict(check=mode,passed=rc==0)]));results.append(row);print(mode,rc,flush=True)
write(ROOT/'migration/reports/rewrite-sparse-binding-negative.json',dict(tests=results,status='PASSED' if all(r['passed'] for r in results) else 'FAILED'))
