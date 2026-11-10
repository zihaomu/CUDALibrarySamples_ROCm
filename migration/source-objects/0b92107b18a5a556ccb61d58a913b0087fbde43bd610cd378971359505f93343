#!/usr/bin/env python3
import copy,unittest
from unittest.mock import patch
import qualify_sparse_bindings as q
class SparseBindingQualification(unittest.TestCase):
 def checks(self,mutate=None):
  original=q.load
  def load(name):
   if name=='rewrite-R5-review.json':return dict(verdict='APPROVED',source_commit='only independent review binding is mocked')
   value=copy.deepcopy(original(name));return mutate(name,value) if mutate else value
  with patch.object(q,'load',load),patch.object(q.reviews,'review_identity',return_value=True):return q.collect()[2]
 def test_real_evidence(self):
  checks=self.checks();self.assertTrue(all(c['passed'] for c in checks),[c['check'] for c in checks if not c['passed']])
 def test_language_cannot_reuse_other_entry(self):
  def mutate(name,value):
   if name=='rewrite-sparse-binding-rocm.json':value['cuDSS/nvfortran/batch::batch.cuf/original']=copy.deepcopy(value['cuDSS/fortran/batch::batch.f90/original'])
   return value
  self.assertFalse(next(c['passed'] for c in self.checks(mutate) if c['check']=='nvfortran/batch/original/AMD-frozen-case'))
 def test_changed_case_cannot_reuse_original(self):
  def mutate(name,value):
   if name=='rewrite-sparse-binding-rocm.json':value['cuDSS/fortran/batch::batch.f90/changed-values']=copy.deepcopy(value['cuDSS/fortran/batch::batch.f90/original'])
   return value
  self.assertFalse(next(c['passed'] for c in self.checks(mutate) if c['check']=='fortran/batch/changed-values/AMD-frozen-case'))
 def test_unique_fault_lists(self):
  for target,gate in [('rewrite-sparse-binding-negative.json','ten-unique-output-faults'),('rewrite-sparse-binding-runtime.json','eight-unique-Fortran-runtime-rejections')]:
   def mutate(name,value):
    if name==target:value['tests']=[copy.deepcopy(value['tests'][0]) for _ in value['tests']]
    return value
   self.assertFalse(next(c['passed'] for c in self.checks(mutate) if c['check']==gate))
 def test_relabelled_trace_substitution(self):
  def mutate(name,value):
   if name=='rewrite-sparse-binding-traces.json':value['profiles'][2]=dict(value['profiles'][0],profile='reordering_phase')
   return value
  self.assertFalse(next(c['passed'] for c in self.checks(mutate) if c['check']=='trace/reordering_phase'))
 def test_native_singular_difference_cannot_be_hidden(self):
  def mutate(name,value):
   if name=='rewrite-sparse-binding-cuda-validation.json':value['residual/singular-info']['status']='PASSED'
   return value
  self.assertFalse(next(c['passed'] for c in self.checks(mutate) if c['check']=='fortran/residual/singular-info/native-singular-observation'))
if __name__=='__main__':unittest.main()
