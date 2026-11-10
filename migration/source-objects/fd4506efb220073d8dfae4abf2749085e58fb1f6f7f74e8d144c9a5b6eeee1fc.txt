#!/usr/bin/env python3
"""Reject mutated carry-forward proofs and unrelated recorder changes."""
import copy,json,unittest
from unittest.mock import patch
from experiment import ROOT
import selected_proofs as q

class SelectedQualification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.samples=json.loads((ROOT/'migration/samples.yaml').read_text())['samples']
        cls.sample=next(s for s in cls.samples if (s.get('selected_validation') or {}).get('kind')=='gemm3m')
    def test_current_closure_accepts_and_identity_mutations_reject(self):
        self.assertEqual(q.inspect(self.sample)['status'],'PASSED')
        for mutate in ['hash','dependency','sample','empty','case']:
            s=copy.deepcopy(self.sample);v=s['selected_validation']
            if mutate=='hash':v['implementation_sha256']='0'*64
            elif mutate=='dependency':v['dependencies'].pop(next(k for k in v['dependencies'] if k!=v['implementation']))
            elif mutate=='sample':v['sample_id']='different-entry'
            elif mutate=='case':v['case_ids']=v['case_ids'][:-1]
            else:v['checks']=[]
            self.assertEqual(q.inspect(s)['status'],'FAILED',mutate)
    def test_evidence_corruption_rejects(self):
        original=q.check;target=self.sample['selected_validation']['evidence_references'][0]
        with patch.object(q,'check',side_effect=lambda p:['altered'] if p==ROOT/target else original(p)):
            self.assertEqual(q.inspect(self.sample)['status'],'FAILED')
    def test_recorder_exception_is_limited_to_exact_additive_guard(self):
        path=ROOT/self.sample['selected_validation']['evidence'];source=json.loads((path/'source.json').read_text())
        old=(ROOT/source['source_objects']['tools/moat/experiment.py']).read_text();new=(ROOT/'tools/moat/experiment.py').read_text()
        self.assertTrue(q.recorder_guard_only(old,new))
        self.assertFalse(q.recorder_guard_only(old,new.replace("if outcome == 'PASSED':","if outcome == 'NEVER':")))
        self.assertFalse(q.recorder_guard_only(old,new+'\nx=1\n'))
if __name__=='__main__':unittest.main()
