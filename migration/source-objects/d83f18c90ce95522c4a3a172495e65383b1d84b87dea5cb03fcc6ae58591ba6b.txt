#!/usr/bin/env python3
"""Exercise real sealed evidence and reject duplicate or substituted identities."""
import copy,unittest
from unittest.mock import patch
import qualify_crc32 as q

class CRC32Qualification(unittest.TestCase):
 def checks(self,mutate=None):
  original=q.load
  def load(name):
   if name=='rewrite-R4-review.json':return dict(verdict='APPROVED',source_commit='review gate is the only mocked gate')
   value=copy.deepcopy(original(name))
   return mutate(name,value) if mutate else value
  with patch.object(q,'load',load),patch.object(q.review_gate,'review_identity',return_value=True):return q.collect()[2]
 def test_real_evidence(self):
  checks=self.checks();self.assertTrue(all(c['passed'] for c in checks),[c['check'] for c in checks if not c['passed']])
 def test_case_substitution(self):
  def mutate(name,value):
   if name in {'rewrite-crc32-rocm.json','rewrite-crc32-rocm-validation.json'}:value['changed-values']=copy.deepcopy(value['original'])
   return value
  self.assertFalse(next(c['passed'] for c in self.checks(mutate) if c['check']=='changed-values/rocm/frozen-run-identity'))
 def test_unique_faults_and_cli(self):
  for target,gate in [('rewrite-crc32-negative.json','complete-unique-negative-modes'),('rewrite-crc32-runtime.json','complete-unique-CLI-contract')]:
   def mutate(name,value):
    if name==target:value['tests']=[copy.deepcopy(value['tests'][0]) for _ in value['tests']]
    return value
   self.assertFalse(next(c['passed'] for c in self.checks(mutate) if c['check']==gate))
 def test_relabelled_duplicate_fault(self):
  def mutate(name,value):
   if name=='rewrite-crc32-negative.json':value['tests']=[dict(value['tests'][0],mode=r['mode'],case=r['case']) for r in value['tests']]
   return value
  self.assertFalse(next(c['passed'] for c in self.checks(mutate) if c['check']=='negative/CRC32C-polynomial'))
 def test_trace_count_cannot_be_fabricated(self):
  def mutate(name,value):
   if name=='rewrite-crc32-trace.json':value['crc_kernel_dispatches']=6
   return value
  self.assertFalse(next(c['passed'] for c in self.checks(mutate) if c['check']=='actual-five-CRC32-GPU-kernel-dispatches'))
 def test_empty_input_must_remain_rejected(self):
  def mutate(name,value):
   if name=='rewrite-crc32-rocm.json':value['empty-only']['return_code']=0
   return value
  self.assertFalse(next(c['passed'] for c in self.checks(mutate) if c['check']=='empty-only/rocm/process-semantics'))

if __name__=='__main__':unittest.main()
