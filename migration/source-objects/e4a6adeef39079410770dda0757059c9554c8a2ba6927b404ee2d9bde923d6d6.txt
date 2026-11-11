#!/usr/bin/env python3
"""Check real qualification metadata bindings independently of numeric reruns."""
import copy,unittest
from unittest.mock import patch
import qualify_canny_color as q

class MetadataBindings(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.original=q.load;cls.cache={n:cls.original(n) for n in ['fixture-replay','build','native-build','native','rocm','originals','validation','originals-validation','runtime','runtime-validation','trace','trace-validation','cpp-runtime','cpp-runtime-validation','checks','original-cuda-cpp','original-cuda-validation','original-cuda-python','cli','cli-validation','cold']}
 def collect(self,mutate=None):
  values=copy.deepcopy(self.cache)
  if mutate:mutate(values)
  def numeric(name):return {k:v for k,v in self.cache[name].items() if k not in {'evidence','parent'}}
  with __import__('contextlib').ExitStack() as stack:
   stack.enter_context(patch.object(q,'load',side_effect=lambda name:copy.deepcopy(values[name])))
   for fn,name in [('validate_masks','validation'),('validate_originals','originals-validation'),('cpp_validate','cpp-runtime-validation'),('native_original_validate','original-cuda-validation'),('cli_validate','cli-validation')]:stack.enter_context(patch.object(q,fn,side_effect=lambda *args,_name=name,**kw:numeric(_name)))
   stack.enter_context(patch.object(q,'runtime_validate',side_effect=lambda r,trace=False:numeric('trace-validation' if trace else 'runtime-validation')))
   return q.collect('cpp')[0]
 def rejected(self,mutate,name):self.assertFalse(next(c['passed'] for c in self.collect(mutate) if c['check']==name))
 def test_real_metadata_baseline(self):
  self.assertEqual([c['check'] for c in self.collect() if not c['passed']],['three-distinct-scopes-review-current-source-and-proof-set'])
 def test_wrong_compiled_binary(self):self.rejected(lambda d:d['build'].update(binary_sha256='0'*64),'current-C-ABI-library-and-real-C++-binary-build')
 def test_wrong_SDK_manifest(self):self.rejected(lambda d:d['build'].update(SDK_manifest_sha256='0'*64),'actual-private-OpenCV-headers-and-SO-identities')
 def test_missing_native_case(self):self.rejected(lambda d:d['native'].pop(),'native-22-unique-cases')
 def test_duplicate_native_case(self):self.rejected(lambda d:d['native'].append(copy.deepcopy(d['native'][0])),'native-22-unique-cases')
 def test_nonzero_GPU_process(self):self.rejected(lambda d:d['rocm'][0].update(return_code=1),'actual-guarded-GPU-22-mask-producer')
 def test_missing_language_entry(self):self.rejected(lambda d:d['originals'].pop(),'all-ten-original-language-workflows')
 def test_wrong_runtime_code(self):self.rejected(lambda d:d['runtime'].update(return_code=1),'runtime/actual-guarded-current-library')
 def test_wrong_CPP_probe_binary(self):self.rejected(lambda d:d['cpp-runtime'].update(binary_sha256='0'*64),'actual-C++-class-ROI-errors-and-independent-instances')
 def test_misreported_Python_baseline(self):self.rejected(lambda d:d['original-cuda-python'].update(status='READY'),'original-CUDA-Python-prerequisite-status-distinct')
 def test_empty_mutation_inventory(self):self.rejected(lambda d:d['checks'].update(checks=[]),'complete-39-validator-positive-and-negative-experiments')
 def test_missing_CLI_case(self):self.rejected(lambda d:d['cli'].pop(),'all-ten-CLI-and-no-device-branches')
 def test_fake_successful_default_CLI(self):self.rejected(lambda d:d['cli'][0].update(return_code=9),'CLI/cpp/default-image/actual-entry-and-device-mask')
if __name__=='__main__':unittest.main()
