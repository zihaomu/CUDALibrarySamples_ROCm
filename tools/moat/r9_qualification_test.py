#!/usr/bin/env python3
"""Mutation tests for R9 promotion; modify copied report data, never sealed evidence."""
import copy,functools,json,unittest
from unittest.mock import patch
import qualify_r9 as q
from experiment import ROOT

class Promotion(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.profile=json.loads((ROOT/'migration/rewrite/helpers-benchmark.json').read_text())['helpers'][0]
  cls.review=q.load('rewrite-R9-helper-review.json');cls.review['verdict']='APPROVED';cls.review['reviewers']=[{'verdict':'APPROVED'}]
  cls.original_load=staticmethod(q.load)
  # Re-read every byte once, then reuse the independent CPU result for report
  # mutations; no GPU rerun and no evidence file changes occur in these tests.
  cls.cached_crc=staticmethod(functools.lru_cache(maxsize=None)(lambda path,case_text,backend:q.crc_cpu_original(path,json.loads(case_text),backend)))
  q.crc_cpu_original=q.crc_cpu
 def helper(self,name=None,change=None):
  def load(n):
   data=copy.deepcopy(self.original_load(n))
   if n==name:change(data)
   return data
  with patch.object(q,'load',load),patch.object(q,'review_ok',return_value=True):return q.helpers(copy.deepcopy(self.profile),self.review)[0]
 def crc(self,name=None,change=None):
  def load(n):
   data=copy.deepcopy(self.original_load(n))
   if n==name:change(data)
   return data
  def cpu(path,case,backend='rocm'):return self.cached_crc(str(path),json.dumps(case,sort_keys=True),backend)
  with patch.object(q,'load',load),patch.object(q,'review_ok',return_value=True),patch.object(q,'crc_cpu',cpu):return q.crc_benchmark(self.review)[0]
 def rejected(self,checks):self.assertTrue(any(not c['passed'] for c in checks))
 def test_complete_helper_proof(self):self.assertTrue(all(c['passed'] for c in self.helper()))
 def test_missing_helper_case(self):self.rejected(self.helper('rewrite-R9-helper-rocm.json',lambda rows:rows.pop(0)))
 def test_helper_output_redirect(self):self.rejected(self.helper('rewrite-R9-helper-rocm.json',lambda rows:rows[0].update(output='nonexistent-output')))
 def test_helper_binary_identity(self):self.rejected(self.helper('rewrite-R9-helper-build.json',lambda b:b['binaries'][0].update(binary_sha256='0'*64)))
 def test_helper_dependency_loss(self):self.rejected(self.helper('rewrite-R9-helper-build.json',lambda b:b['dependencies'].pop('rocm/adapters/helpers/matrix_helpers.cpp')))
 def test_helper_native_binary_identity(self):self.rejected(self.helper('rewrite-R9-helper-native-build.json',lambda b:b['binary_sha256'].update(dense_matrix_helpers='0'*64)))
 def test_helper_ABI_summary(self):self.rejected(self.helper('rewrite-R9-helper-runtime.json',lambda b:b['ABI']['checks'].pop()))
 def test_helper_fault_set(self):self.rejected(self.helper('rewrite-R9-helper-negative.json',lambda b:b['checks'].pop(0)))
 def test_Fortran_inventory_cannot_use_ROCm_build(self):
  self.profile=json.loads((ROOT/'migration/rewrite/helpers-benchmark.json').read_text())['helpers'][3]
  self.rejected(self.helper('rewrite-R9-helper-originals.json',lambda r:r.update(Fortran_toolchain_evidence=self.original_load('rewrite-R9-helper-build.json')['evidence'])))
 def test_validation_dependency_review_closure(self):
  with patch.object(q,'review_ok',return_value=True):
   sources=q.helpers(self.profile,self.review)[2]
  self.assertTrue({'tools/moat/audit.py','tools/moat/qualification_common.py','tools/moat/experiment.py'}<=set(sources))
  original=q.digest
  for name in ['tools/moat/audit.py','tools/moat/qualification_common.py']:
   with patch.object(q,'digest',side_effect=lambda p,n=name:'0'*64 if str(p)==str(ROOT/n) else original(p)):
    self.assertFalse(q.review_ok(self.review,[name]))
 def test_unsealed_qualification_beside_ordinary_run_is_rejected(self):
  import publish_r9
  run=self.original_load('rewrite-R9-helper-rocm.json')[0]
  forged=dict(sample_id=self.profile['sample_id'],evidence=run['evidence'],qualification_id=run['experiment_id'],status='PASSED',case_ids=['original'],case_count=1,evidence_references=[],checks=[dict(check='invented-qualification',passed=True)])
  original=type(ROOT).read_text
  def read(path,*args,**kwargs):
   if path.name=='qualification.json':return json.dumps(forged)
   return original(path,*args,**kwargs)
  with patch.object(type(ROOT),'read_text',read):
   with self.assertRaisesRegex(ValueError,'unsealed composite qualification'):publish_r9.validate_qualification(forged,dict(id=self.profile['sample_id']),self.profile,self.review)
 def test_publisher_binds_actual_source_language(self):
  import publish_r9
  p=json.loads((ROOT/'migration/rewrite/helpers-benchmark.json').read_text())['helpers'][3]
  qrow=dict(kind='matrix-helper/'+p['language']+'/'+p['kind'],implementation=p['implementation'],implementation_sha256=q.digest(ROOT/p['implementation']))
  publish_r9.profile_identity(qrow,p)
  for field,value in [('kind','matrix-helper/cpp/'+p['kind']),('implementation',self.profile['implementation']),('implementation_sha256','0'*64)]:
   wrong=dict(qrow);wrong[field]=value
   with self.assertRaisesRegex(ValueError,'source-language/profile identity'):publish_r9.profile_identity(wrong,p)
 def test_actual_published_composite_is_accepted(self):
  import publish_r9
  row=self.original_load('rewrite-R9-helper-qualification.json')['qualifications'][0]
  sample=next(s for s in json.loads((ROOT/'migration/samples.yaml').read_text())['samples'] if s['id']==self.profile['sample_id'])
  publish_r9.validate_qualification(row,sample,self.profile,self.original_load('rewrite-R9-helper-review.json'))
 def test_complete_crc_proof(self):self.assertTrue(all(c['passed'] for c in self.crc()))
 def test_crc_output_redirect(self):self.rejected(self.crc('rewrite-R9-crc-benchmark-rocm.json',lambda r:r['original-auto'].update(output='nonexistent-output')))
 def test_crc_native_binary_identity(self):self.rejected(self.crc('rewrite-R9-crc-benchmark-native-build.json',lambda b:b.update(binary_sha256='0'*64)))
 def test_crc_native_remote_receipt(self):self.rejected(self.crc('rewrite-R9-crc-benchmark-cuda.json',lambda r:r['original-auto'].update(remote_output='/tmp/other-output')))
 def test_crc_trace_count(self):self.rejected(self.crc('rewrite-R9-crc-benchmark-trace.json',lambda t:t.update(segment_dispatches=3)))
 def test_crc_fault_set(self):self.rejected(self.crc('rewrite-R9-crc-benchmark-checks.json',lambda a:a['negative'].pop()))
 def test_pending_review_rejected(self):self.assertFalse(q.review_ok(dict(source_commit=self.review['source_commit'],verdict='PENDING',reviewers=[]),[]))
 def test_unpublished_seal_rejected(self):
  prior=q.TRUSTED_COMMIT;q.TRUSTED_COMMIT='8b0573b11d183d9b3a36cd2955aa31c16cc61b95';q.sealed.cache_clear()
  try:
   with self.assertRaises(Exception):q.sealed(self.original_load('rewrite-R9-helper-build.json')['evidence'])
  finally:q.TRUSTED_COMMIT=prior;q.sealed.cache_clear()
if __name__=='__main__':unittest.main()
