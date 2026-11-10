#!/usr/bin/env python3
import copy,unittest
from unittest.mock import patch
import qualify_sparse24 as q
class Sparse24Qualification(unittest.TestCase):
 def checks(self,mutate=None):
  original=q.load
  def load(name):
   if name=='rewrite-R7-review.json':return dict(verdict='APPROVED',source_commit='only approval content binding is mocked')
   data=copy.deepcopy(original(name));return mutate(name,data) if mutate else data
  with patch.object(q,'load',load),patch.object(q.reviews,'review_identity',return_value=True):return q.collect()[2]
 def test_real_evidence_satisfies_all_nonapproval_gates(self):
  checks=self.checks();self.assertTrue(all(c['passed'] for c in checks),[c['check'] for c in checks if not c['passed']])
 def test_changed_case_cannot_use_original(self):
  def mutate(name,data):
   if name=='rewrite-extension-rocm.json':data['sparse24/changed-values']=copy.deepcopy(data['sparse24/original'])
   return data
  self.assertFalse(next(c['passed'] for c in self.checks(mutate) if c['check']=='sparse24/changed-values/rocm/frozen-actual-run'))
 def test_header_dependency_cannot_be_cropped(self):
  target='rocm/backends/sparse/sparse24.hpp';original=q.digest
  def crop(data):
   if isinstance(data,dict):
    if 'dependencies' in data:data['dependencies'].pop(target,None)
    for child in data.values():crop(child)
   elif isinstance(data,list):
    for child in data:crop(child)
  def mutate(name,data):crop(data);return data
  with patch.object(q,'digest',side_effect=lambda path:'f'*64 if str(path)==str(q.ROOT/target) else original(path)):
   self.assertFalse(next(c['passed'] for c in self.checks(mutate) if c['check']=='sparse24/sealed-complete-current-build'))
 def test_native_build_cannot_use_run_evidence(self):
  fake=copy.deepcopy(q.load('rewrite-sparse24-native-build.json'));fake['evidence']=q.load('rewrite-sparse24-cuda.json')['sparse24/original']['evidence']
  def mutate(name,data):
   if name=='rewrite-sparse24-native-build.json':return fake
   if name=='rewrite-sparse24-cuda.json':
    for row in data.values():row['build']=fake
   if name=='rewrite-sparse24-cuda-validation.json':
    for row in data.values():row['run']['build']=fake
   return data
  self.assertFalse(next(c['passed'] for c in self.checks(mutate) if c['check']=='actual-native-build-and-derived-input-bundle'))
 def test_duplicate_negative_list_rejects(self):
  def mutate(name,data):
   if name=='rewrite-sparse24-negative.json':data['tests']=[copy.deepcopy(data['tests'][0]) for _ in data['tests']]
   return data
  self.assertFalse(next(c['passed'] for c in self.checks(mutate) if c['check']=='seventeen-unique-semantic-faults'))
 def test_unrelated_profile_trace_rejects(self):
  def mutate(name,data):
   if name=='rewrite-sparse24-traces.json':data['profiles'][0]=dict(data['profiles'][1],kind='sparse24')
   return data
  self.assertFalse(next(c['passed'] for c in self.checks(mutate) if c['check']=='trace/sparse24/prune-compress-check-sparse-only-matmul'))
 def test_derived_input_parent_cannot_be_relabelled(self):
  def mutate(name,data):
   if name=='rewrite-sparse24-cuda.json':data['sparse24/changed-values']['derived']=copy.deepcopy(data['sparse24/original']['derived'])
   return data
  self.assertFalse(next(c['passed'] for c in self.checks(mutate) if c['check']=='sparse24/changed-values/cuda/frozen-actual-run'))
 def test_native_original_source_cannot_be_relabelled(self):
  def mutate(name,data):
   if name=='rewrite-sparse24-original-cuda.json':data['profiles'][0]['original_sha256']='f'*64
   return data
  self.assertFalse(next(c['passed'] for c in self.checks(mutate) if c['check']=='sparse24/actual-original-native-program'))
 def test_native_original_output_cannot_be_redirected(self):
  def mutate(name,data):
   if name=='rewrite-sparse24-original-cuda.json':
    for row in data['profiles']:row['output']='artifacts/nonexistent-original-output'
   if name=='rewrite-sparse24-original-validation.json':
    for row in data['profiles']:row['run']['output']='artifacts/nonexistent-original-output'
   return data
  checks=self.checks(mutate)
  for kind in q.KINDS:
   for gate in ['actual-original-native-program','original-native-DP-and-mathematical-CPU']:self.assertFalse(next(c['passed'] for c in checks if c['check']==kind+'/'+gate))
 def test_original_CPU_summary_cannot_substitute_unsealed_result(self):
  def mutate(name,data):
   if name=='rewrite-sparse24-original-validation.json':data['profiles'][0]['max_fp16_ulp']=2
   return data
  self.assertFalse(next(c['passed'] for c in self.checks(mutate) if c['check']=='sparse24/original-native-DP-and-mathematical-CPU'))
if __name__=='__main__':unittest.main()
