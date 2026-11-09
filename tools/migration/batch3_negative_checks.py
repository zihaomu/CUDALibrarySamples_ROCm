#!/usr/bin/env python3
"""Corrupt actual outputs and graph metadata to check the independent gates."""
import datetime,json,pathlib,shutil
from catalog import ROOT
from batch3_spec import ALL
from batch3_reference import validate,np
from run import evidence_directory,digest

def main():
    rows=json.loads((ROOT/'migration/reports/batch3-rocm.json').read_text())
    out=ROOT/'artifacts'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')/'batch3-negative'
    out.mkdir(parents=True);checks=[]
    for r in rows:
        source=r['source'];kind=pathlib.PurePosixPath(source).parent.name
        case='small-varied' if kind in ['cg','bicgstab'] else 'sparse-small' if kind=='graph_capture' else 'original'
        original=evidence_directory(next(c['evidence'] for c in r['runs'] if c['case']==case))
        targets={'gpsvInterleavedBatch':'solution_interleaved','gesvdjBatched':'U','syevjBatched':'V','syevdx':'V','sygvdx':'V','graph_capture':'replay_0'}
        mutations=['finite-corruption','NaN']
        extras={'syevjBatched':['unpaired-W'],'syevdx':['wrong-meig'],'sygvdx':['wrong-meig'],
                'graph_capture':['empty-graph','no-kernel-nodes','zero-captured-calls','stale-replays','single-replay']}
        for mutation in mutations+extras.get(kind,[]):
            d=out/(kind+'-'+mutation);d.mkdir()
            shutil.copyfile(original/'run.log',d/'run.log')
            for p in original.glob('*.bin'):shutil.copyfile(p,d/p.name)
            if kind in ['cg','bicgstab']:
                p=d/'solution.bin';v=np.fromfile(p,np.float64);v[0]=np.nan if mutation=='NaN' else v[0]+1.;v.tofile(p)
            else:
                lines=[]
                for line in (d/'run.log').read_text().splitlines():
                    if line.startswith('{"observe"'):
                        obj=json.loads(line);name=obj['observe'];v=obj['values']
                        if mutation in ['finite-corruption','NaN'] and name==targets[kind]:v[0]=None if mutation=='NaN' else v[0]+1.
                        if mutation=='unpaired-W' and name=='W':v[0],v[1]=v[1],v[0]
                        if mutation=='wrong-meig' and name=='meig':v[0]+=1
                        if mutation=='empty-graph' and name=='graph_nodes':v[0]=0
                        if mutation=='no-kernel-nodes' and name=='graph_kernels':v[0]=0
                        if mutation=='zero-captured-calls' and name=='capture_calls':v[0]=0
                        if mutation=='stale-replays' and name.startswith('replay_') and name!='replay_count':v[0]=1.
                        if mutation=='single-replay' and name=='replay_count':v[0]=1
                        line=json.dumps(obj,separators=(',',':'))
                    lines.append(line)
                (d/'run.log').write_text('\n'.join(lines)+'\n')
            try:
                result=validate(source,case,d);rejected=result['status']=='FAILED'
                failed=[c['check'] for c in result['checks'] if not c['passed']]
            except (ValueError,KeyError,TypeError) as e:rejected=True;failed=[str(e)]
            checks.append({'source':source,'case':case,'mutation':mutation,'rejected':rejected,
                           'failed_checks':failed,'evidence':str(d.relative_to(ROOT)),'log_sha256':digest(d/'run.log')})
    result={'status':'PASSED' if len(checks)==24 and all(c['rejected'] for c in checks) else 'FAILED','checks':checks}
    (ROOT/'migration/reports/batch3-negative-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'],sum(c['rejected'] for c in checks),'/',len(checks),'corruptions rejected')
    return result['status']!='PASSED'
if __name__=='__main__':raise SystemExit(main())
