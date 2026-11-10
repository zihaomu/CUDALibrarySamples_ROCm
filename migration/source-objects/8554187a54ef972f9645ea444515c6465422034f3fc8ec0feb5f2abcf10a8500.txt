#!/usr/bin/env python3
"""Reject duplicated cases/checks and an unrelated sealed solver trace."""
import copy,unittest
from unittest.mock import patch
import qualify_r3 as q

class R3QualificationContract(unittest.TestCase):
 def loader(self,mutate=None):
  original=q.load
  def load(name):
   if name=='rewrite-R3-review.json':return dict(verdict='APPROVED',source_commit='only-reviewed-content-gate-mocked')
   data=copy.deepcopy(original(name))
   return mutate(name,data) if mutate else data
  return load
 def collect(self,kind,mutate=None):
  with patch.object(q,'load',self.loader(mutate)),patch.object(q.gates,'review_identity',return_value=True):return q.collect(kind)[2]
 def test_real_evidence_satisfies_nonapproval_gates(self):
  for kind in ['ncc','svd']:
   checks=self.collect(kind);self.assertTrue(all(c['passed'] for c in checks),[c['check'] for c in checks if not c['passed']])
 def test_original_cannot_substitute_changed_values(self):
  def duplicate(name,data):
   if name in ['rewrite-extension-rocm.json','rewrite-extension-cuda.json','rewrite-extension-rocm-validation.json','rewrite-extension-cuda-validation.json']:data['svd/changed-values']=copy.deepcopy(data['svd/original'])
   return data
  checks=self.collect('svd',duplicate);self.assertFalse(next(c['passed'] for c in checks if c['check']=='changed-values/rocm/frozen-case-identity'))
 def test_ncc_original_cannot_substitute_changed_values(self):
  def duplicate(name,data):
   if name in ['rewrite-ncc-rocm.json','rewrite-ncc-cuda.json']:data['changed-values']=copy.deepcopy(data['original'])
   return data
  checks=self.collect('ncc',duplicate);self.assertFalse(next(c['passed'] for c in checks if c['check']=='changed-values/rocm/frozen-case-identity'))
 def test_duplicate_negative_and_CLI_lists_reject(self):
  for target,key in [('rewrite-ncc-negative.json','negative-complete-unique-modes'),('rewrite-ncc-runtime.json','runtime-complete-unique-tests')]:
   def duplicate(name,data):
    if name==target:data['tests']=[copy.deepcopy(data['tests'][0]) for _ in data['tests']]
    return data
   checks=self.collect('ncc',duplicate);self.assertFalse(next(c['passed'] for c in checks if c['check']==key))
 def test_relabeling_duplicate_evidence_still_rejects(self):
  for target,key,field in [('rewrite-ncc-negative.json','negative/annotation','mode'),('rewrite-ncc-runtime.json','CLI/short-template','test')]:
   def duplicate(name,data):
    if name==target:
     baseline=copy.deepcopy(data['tests'][0]);data['tests']=[dict(baseline,**{field:r[field]}) for r in data['tests']]
    return data
   checks=self.collect('ncc',duplicate);self.assertFalse(next(c['passed'] for c in checks if c['check']==key))
 def test_unrelated_sealed_trace_rejects(self):
  rows=q.load('rewrite-solver-backend-traces.json')['profiles'];row=copy.deepcopy(next(r for r in rows if r['name']=='rank-svd'));build=q.load('rewrite-extension-builds.json')['svd'];self.assertTrue(q.trace_identity(row,build));row['evidence']=next(r['evidence'] for r in rows if r['name']=='cusolver_Xgeev_example1');self.assertFalse(q.trace_identity(row,build))

if __name__=='__main__':unittest.main()
