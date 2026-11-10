#!/usr/bin/env python3
"""Carry immutable qualifications forward only for unchanged numerical closures."""
import ast,json,sys,functools
from pathlib import Path
from experiment import ROOT,digest,write
from audit import check as _check
check=functools.lru_cache(maxsize=None)(_check)

def recorder_guard_only(old,new):
    """Recognize the sole historical recorder change, not arbitrary exclusions."""
    a=ast.parse(old);b=ast.parse(new)
    assignments=[n for n in b.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='OUTCOMES' for t in n.targets)]
    if len(assignments)!=1:return False
    b.body.remove(assignments[0]);removed=0
    for n in ast.walk(b):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=='finish':
            for stmt in list(n.body):
                if isinstance(stmt,ast.If) and ast.unparse(stmt.test)=="outcome not in OUTCOMES or outcome == 'RUNNING'":
                    if len(stmt.body)!=1 or not isinstance(stmt.body[0],ast.Raise) or stmt.orelse:return False
                    n.body.remove(stmt);removed+=1
    return removed==1 and ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False)

def inspect(sample):
    q=sample['selected_validation'];errors=[];annotations=[]
    def require(ok,why):
        if not ok:errors.append(why)
    path=ROOT/q['evidence'];require(not check(path),'qualification seal')
    m=json.loads((path/'manifest.json').read_text());sealed=json.loads((path/'qualification.json').read_text())
    require(m['sample_id']==sample['id'] and m['experiment_id']==q['qualification_id'] and m['experiment_outcome']=='PASSED','qualification identity/outcome')
    require(all(k in q and q[k]==v for k,v in sealed.items()),'selected fields differ from sealed qualification')
    require(q['status']=='PASSED' and bool(q['checks']) and all(c.get('passed') is True for c in q['checks']),'qualification checks')
    require(q['sample_id']==sample['id'] and q['implementation']==sample['implementation'],'selected implementation')
    require(digest(ROOT/q['implementation'])==q['implementation_sha256'],'current implementation')
    require(bool(q['dependencies']) and sample['implementation'] in q['dependencies'],'nonempty dependency closure')
    for n,h in q['dependencies'].items():require((ROOT/n).is_file() and digest(ROOT/n)==h,'current compiled dependency '+n)
    src=json.loads((path/'source.json').read_text())
    for n,h in src['dependencies'].items():
        if (ROOT/n).exists() and digest(ROOT/n)==h:continue
        obj=ROOT/src['source_objects'][n]
        if n=='migration/rewrite/first-eight.json' and json.loads(obj.read_text())==json.loads((ROOT/n).read_text()):
            annotations.append('First-eight JSON formatting only; complete JSON equality checked')
        elif n=='tools/moat/experiment.py' and recorder_guard_only(obj.read_text(),(ROOT/n).read_text()):
            annotations.append('Recorder adds terminal-outcome validation only; AST equality after removing exactly the added guard and enum')
        else:require(False,'qualification oracle/spec dependency '+n)
    refs=set(q.get('evidence_references',[]))
    if q['kind'] in ['sparse-binding','sparse24','sparse24_advanced']:
        report=ROOT/'migration/reports'/('rewrite-R5-qualification.json' if q['kind']=='sparse-binding' else 'rewrite-R7-qualification.json')
        group=json.loads(report.read_text());profiles=group.get('qualified_profiles',group.get('qualifications',[]))
        require(group['status']=='PASSED' and q in profiles,'aggregate qualification matches selected profile')
        refs.update(group.get('evidence_references',[]))
    require(bool(refs),'nonempty evidence references')
    for ref in refs:require(not check(ROOT/ref),'referenced seal '+ref)
    require(q.get('case_count',0)>0 and q['case_count']==len(q.get('case_ids',[])),'case contract')
    devices=q.get('devices',[]);require(bool(devices) and all(d['physical_id']!=3 for d in devices),'physical device identity')
    return dict(sample_id=sample['id'],status='PASSED' if not errors else 'FAILED',errors=errors,annotations=annotations,qualification=q['evidence'],source_commit=q['source_commit'],dependencies=q['dependencies'])

def main():
    samples=json.loads((ROOT/'migration/samples.yaml').read_text())['samples'];rows=[inspect(s) for s in samples if s.get('reason_code')=='VALIDATED_MOAT_REWRITE' and s['status']=='PASSED']
    result=dict(status='PASSED' if rows and all(r['status']=='PASSED' for r in rows) else 'FAILED',qualified_samples=len(rows),scope='Current compiled numerical dependencies and immutable selected qualifications; historical attempts remain historical',rows=rows)
    write(ROOT/'migration/reports/rewrite-selected-proof-audit.json',result);print(json.dumps({k:v for k,v in result.items() if k!='rows'}));return int(result['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
