#!/usr/bin/env python3
"""Explicit, narrowly identified NPPPlus reference differences; no pixel tolerance."""
import argparse,hashlib,json
import numpy as np
from scipy.ndimage import minimum_filter
from experiment import ROOT,Experiment,digest,write
from image_encoder_math_binding import sealed
from image_completion_progress import record
import image_watershed_completion_binding as binding
PATH=ROOT/'migration/rewrite/image-watershed-native-reference-amendment.json'
DIAG=ROOT/'migration/reports/image-watershed-monotone-reference.json'
STRICT=ROOT/'migration/reports/image-watershed-completion-reference-padded.json'
IDS=('heldout-ramp-x','heldout-ramp-y','heldout-ramp-diagonal')
MODES=('segments','black','white','contrast','boundaries')

def analytic_zero(image):
    return image.dtype==np.uint8 and image.ndim==2 and image.size>0 and bool(np.all((image==0)|(minimum_filter(image,size=3,mode='constant',cval=255)<image)))

def expected_exceptions(contract):
    by_id={r['id']:r for r in contract['inputs']}
    return [dict(id=name,width=by_id[name]['width'],height=by_id[name]['height'],sha256=by_id[name]['sha256'],vendor='NPPPlus',library_version='12.4.0',modes=list(MODES),repeat_ids=[0,1],null_marker_modes=['contrast','boundaries']) for name in IDS]

def validate_payload(row,contract):
    binding.need(row['status']=='FROZEN_AMENDMENT' and row['amendment_id']=='NPPPlus-12.4-monotone-three-inputs-v1','amendment identity')
    binding.need(row['base_contract_sha256']==digest(binding.CONTRACT),'amendment base contract')
    binding.need(row['exceptions']==expected_exceptions(contract),'exact three exception identities/modes/version')
    binding.need(row['policy']=='CPU and NPP remain EXACT for every input; NPPPlus remains EXACT for the other57 inputs. The three named NPPPlus comparisons remain NATIVE_MISMATCH; no pixel tolerance or additional implicit exception.','amendment scope')

def load():
    contract=binding.contract();row=json.loads(PATH.read_text());sealed(row,'amendment.json');validate_payload(row,contract)
    diagnostic=json.loads(DIAG.read_text());sealed(diagnostic);binding.need(diagnostic['status']=='PASSED' and diagnostic['checks'] and all(c['passed'] is True for c in diagnostic['checks']),'analytic confirmation gates')
    strict=json.loads(STRICT.read_text());sealed(strict)
    failures={c['check'] for c in strict['checks'] if not c['passed']}
    binding.need(strict['status']=='NUMERIC_MISMATCH' and failures=={name+'-NPPPlus-12-native-images' for name in IDS},'original strict failure preserved')
    binding.need(row['original_strict_evidence']==strict['evidence'] and row['diagnostic_evidence']==diagnostic['evidence'],'amendment proof identity')
    return row

def permits(row,item,vendor,image,expected,cpu_exact,npp_exact):
    if vendor!='NPPPlus' or item['id'] not in IDS:return False
    exception=next((x for x in row['exceptions'] if x['id']==item['id']),None)
    if exception is None or image.shape!=(exception['height'],exception['width']):return False
    if hashlib.sha256(image.tobytes()).hexdigest()!=exception['sha256'] or item['sha256']!=exception['sha256']:return False
    if not analytic_zero(image) or not cpu_exact or not npp_exact:return False
    return all(expected[name].tobytes()==bytes([255 if name=='boundaries' else 0])*image.size for name in MODES)

def freeze():
    if PATH.exists():raise ValueError('reference amendment already frozen')
    contract=binding.contract();diagnostic=json.loads(DIAG.read_text());sealed(diagnostic);strict=json.loads(STRICT.read_text());sealed(strict)
    binding.need(diagnostic['status']=='PASSED' and all(c['passed'] is True for c in diagnostic['checks']),'complete bound analytic diagnostic required')
    binding.need(strict['status']=='NUMERIC_MISMATCH' and {c['check'] for c in strict['checks'] if not c['passed']}=={name+'-NPPPlus-12-native-images' for name in IDS},'only the three preserved native disagreements')
    row=dict(status='FROZEN_AMENDMENT',amendment_id='NPPPlus-12.4-monotone-three-inputs-v1',base_contract_sha256=digest(binding.CONTRACT),exceptions=expected_exceptions(contract),original_strict_evidence=strict['evidence'],diagnostic_evidence=diagnostic['evidence'],policy='CPU and NPP remain EXACT for every input; NPPPlus remains EXACT for the other57 inputs. The three named NPPPlus comparisons remain NATIVE_MISMATCH; no pixel tolerance or additional implicit exception.',justification='Every nonzero pixel in each identified image has a strictly lower neighbor and all terminal minima are zero. Strict descent must terminate at zero. Independent CPU, actual HIP and NPP agree. NPPPlus has measured nonzero residuals in both pitches; repeated calls still change them. No claim about proprietary internal cause.',required_gates=['sealed original strict NUMERIC_MISMATCH retained','exact input ID/dimensions/SHA and NPPPlus12.4.0','analytic terminal-minimum-zero invariant','every CPU product exact','all12 corresponding NPP image products exact','bound24 analytic confirmation inputs, complete products, both native pitches, native call/padding success, cross-pitch identity and nonincreasing changing NPPPlus chains','reject fourth exception, same-name replacement, false analytic invariant, failed second native oracle'],review='Independent MOAT review accepted the direction subject to these automatic gates. The24 extra inputs were frozen before diagnostic execution, not blind tests created after this amendment.',evidence_references=[contract['evidence'],strict['evidence'],diagnostic['evidence']])
    validate_payload(row,contract)
    e=Experiment('I3','watershed-explicit-native-reference-amendment','CPU-contract',sources=[__file__,binding.CONTRACT,binding.SPEC,DIAG,STRICT,ROOT/'tools/moat/image_watershed_completion_binding.py',ROOT/'tools/moat/image_encoder_math_binding.py',*[ROOT/i['path'] for i in contract['inputs'] if i['id'] in IDS]])
    write(e.path/'amendment.json',row);row['evidence']=e.finish('OBSERVED');write(PATH,row)
    record('IMG-02','明确封存NPP+12.4.0三个坡度输入参考修订：锁定ID/尺寸/SHA/全部模式；原严格失败保持NUMERIC_MISMATCH、三项原生保持NATIVE_MISMATCH，CPU/NPP精确及解析/24确认门禁不可豁免，其余57项NPP+仍EXACT。',[row['evidence']]);print(row['evidence'])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze']);p.parse_args();freeze()
