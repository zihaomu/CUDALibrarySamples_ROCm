#!/usr/bin/env python3
"""Exact coverage gates for wide indexing, prefix dispatch and large products."""
import copy,json
from experiment import ROOT,Experiment,write
from image_completion_progress import record

REPORTS = dict(wide='image-encoder-wide-runs.json', indices='image-encoder-wide-indices.json',
    dispatch='image-prefix-dispatch-runs.json', holdout='image-prefix-holdout-runs.json',
    capacity='image-encoder-capacity.json', large='image-encoder-large-runs.json',
    cpu='image-jpeg-reference-modes-heldout.json', amendment='image-jpeg-reference-amendment.json')
PROFILES = dict(wide='image-encoder-wide-profile.json',dispatch='image-prefix-dispatch-profile.json',
    holdout='image-prefix-holdout-profile.json',capacity='image-encoder-capacity-profile.json',
    large='image-encoder-large-profile.json',cpu='image-jpeg-reference-modes-profile.json')
NEGATIVE = ROOT/'migration/reports/image-encoder-extension-negatives.json'

def load():
    return {k:json.loads((ROOT/'migration/reports'/n).read_text()) for k,n in REPORTS.items()}

def passed(row):
    return row['status']=='PASSED' and bool(row['checks']) and all(c['passed'] for c in row['checks'])

def checks(data):
    profiles={k:json.loads((ROOT/'migration/rewrite'/n).read_text()) for k,n in PROFILES.items()}
    def group(key, count, extra=()):
        rows=data[key];cases=profiles[key]['cases']
        return len(rows)==count and [r['case'] for r in rows]==[c['id'] for c in cases]+list(extra) and all(passed(r) for r in rows)
    amendment=data['amendment'];large=data['large'];target='entry-1x65500-s2'
    amended_names={'independent-CPU-pixel-reference-'+str(i) for i in range(3)}
    large_good=len(large)==8 and [r['case'] for r in large]==[c['id'] for c in profiles['large']['cases']]
    for row in large:
        products=row['products']
        large_good &= len(products)==3 and {p['name'] for p in products}=={'0.jpg','1.jpg','2.jpg'}
        if row['case']!=target:
            large_good &= passed(row)
        else:
            large_good &= row['status']=='FAILED' and {c['check'] for c in row['checks'] if not c['passed']}==amended_names
            large_good &= (passed(amendment) and amendment['case']==target and amendment['original_status']=='FAILED' and
                set(amendment['amended_checks'])==amended_names and amendment['evidence_references']==[row['evidence']]+[r['evidence'] for r in data['cpu']] and
                len(amendment['products'])==3 and
                [(p['name'],p['sha256'],p['bytes'],p['decoded_rgb_sha256'],p['original_pillow_comparison']) for p in amendment['products']]==
                [(p['name'],p['sha256'],p['bytes'],p['decoded_rgb_sha256'],p['comparison']) for p in products])
    return [dict(check='six-wide-full-array-cases',passed=group('wide',6) and all(len(r['arrays'])==9 for r in data['wide'])),
        dict(check='eighteen-wide-coordinate-cases',passed=passed(data['indices']) and
            [r['case'] for r in data['indices']['results']]==profiles['wide']['coordinate_cases'] and len(data['indices']['results'])==18),
        dict(check='all33-dispatch-measurement-guard-cases',passed=group('dispatch',33)),
        dict(check='all24-frozen-dispatch-heldouts',passed=group('holdout',24,('null-pointer-and-count-guards',))),
        dict(check='all29-capacity-boundaries',passed=passed(data['capacity']) and len(data['capacity']['comparisons'])==29 and
            [r['case'] for r in data['capacity']['comparisons']]==[c['id'] for c in profiles['capacity']['cases']]),
        dict(check='all-six-independent-CPU-mode-heldouts',passed=group('cpu',6)),
        dict(check='all-eight-large-entry-cases-and24-products-with-explicit-amendment',passed=bool(large_good))]

def negative():
    data=load();sources=[__file__,*[ROOT/'migration/reports'/n for n in REPORTS.values()],*[ROOT/'migration/rewrite'/n for n in PROFILES.values()]]
    e=Experiment('I5','encoder-extension-coverage-negatives','CPU-negative',sources=sources)
    results=[dict(check='complete-extended-coverage-accepted',passed=all(r['passed'] for r in checks(data)))]
    for key in ['wide','dispatch','holdout','large','cpu']:
        for mutation in ['missing','duplicate']:
            changed=copy.deepcopy(data)
            if mutation=='missing':changed[key].pop()
            else:changed[key][-1]=copy.deepcopy(changed[key][0])
            results.append(dict(check=key+'-'+mutation+'-rejected',passed=not all(r['passed'] for r in checks(changed))))
    mutations=[('missing-wide-index',lambda d:d['indices']['results'].pop()),
        ('missing-capacity-boundary',lambda d:d['capacity']['comparisons'].pop()),
        ('missing-large-product',lambda d:d['large'][0]['products'].pop()),
        ('missing-amended-product',lambda d:d['amendment']['products'].pop()),
        ('wrong-amended-product-sha',lambda d:d['amendment']['products'][0].update(sha256='0'*64)),
        ('missing-amendment-heldout',lambda d:d['amendment']['evidence_references'].pop()),
        ('amendment-failed',lambda d:d['amendment'].update(status='FAILED')),
        ('unexpected-original-failure',lambda d:next(r for r in d['large'] if r['case']=='entry-1x65500-s2')['checks'].append(dict(check='GPU-broken',passed=False)))]
    for name,mutate in mutations:
        changed=copy.deepcopy(data);mutate(changed)
        results.append(dict(check=name+'-rejected',passed=not all(r['passed'] for r in checks(changed))))
    status='PASSED' if all(r['passed'] for r in results) else 'FAILED'
    row=dict(status=status,checks=results);write(e.path/'result.json',row)
    row['evidence']=e.finish('PASSED' if status=='PASSED' else 'VALIDATOR_GAP',dict(status=status,checks=results));write(NEGATIVE,row)
    record('IMG-01','大索引/prefix/容量/8组大图及CPU参考修订的覆盖反向检查：'+status+'，'+str(len(results))+'项含完整正例。',[row['evidence']]);print(status)
    return int(status!='PASSED')

if __name__=='__main__':raise SystemExit(negative())
