#!/usr/bin/env python3
"""Reject incomplete stages, partial-element bytes and unsealed SDK failures."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import image_canny_stages_reference as stages
import image_native_gradient_compare as native
import image_sdk_setup as sdk
from image_validation import coverage,array_check
from experiment import ROOT,write,digest

class DummyExperiment:
    finished=[]
    def __init__(self,*args,**kwargs):
        self.path=DummyExperiment.root/('attempt-'+str(len(DummyExperiment.finished)))
        self.path.mkdir(exist_ok=True)
    def command(self,*args,**kwargs):return 1
    def finish(self,outcome,*args,**kwargs):
        self.finished.append(outcome);return 'self-test/mock-evidence'

class ImageValidation(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=ROOT/'build');self.root=Path(self.temp.name)
        self.addCleanup(self.temp.cleanup);self.fixture=self.root/'inputs';self.fixture.mkdir()
        (self.fixture/'input.bin').write_bytes(bytes(6))
        (self.fixture/'params.txt').write_text('3 2 1 3 0 0 3 2 72 256 8\n')
        write(self.fixture/'config.json',dict(width=3,height=2,channels=1,pitch=3,output_pitch=8,low=72,high=256))
        write(self.fixture/'manifest.json',dict(files={p.name:dict(bytes=p.stat().st_size,sha256=digest(p)) for p in self.fixture.iterdir()}))
        self.case=dict(case='probe',manifest_sha256=digest(self.fixture/'manifest.json'))
        self.out=self.root/'outputs';self.out.mkdir();self.expected=np.zeros((2,3),np.int16)
        for name in ['dx','dy','magnitude','suppressed']:self.expected.tofile(self.out/(name+'.bin'))
        self.row=dict(case='probe',return_code=0,inputs=str(self.fixture.relative_to(ROOT)),outputs=str(self.out.relative_to(ROOT)),
                      output_sha256={p.name:digest(p) for p in self.out.iterdir()})
        DummyExperiment.finished=[];DummyExperiment.root=self.root

    def test_positive_complete_stage(self):self.assertEqual(stages.validate_run(self.row,self.case)['status'],'PASSED')
    def test_failed_process_is_not_skipped(self):
        self.row['return_code']=7;self.assertEqual(stages.validate_run(self.row,self.case)['status'],'FAILED')
    def test_missing_case_rejected(self):self.assertFalse(coverage([self.row],[self.case,dict(case='second')])['passed'])
    def test_duplicate_case_rejected(self):self.assertFalse(coverage([self.row,self.row],[self.case])['passed'])
    def test_trailing_byte_even_with_updated_hash(self):
        p=self.out/'dx.bin';p.write_bytes(p.read_bytes()+b'x');self.row['output_sha256'][p.name]=digest(p)
        self.assertEqual(stages.validate_run(self.row,self.case)['status'],'FAILED')
    def test_extra_output_even_with_updated_hash_map(self):
        p=self.out/'extra.bin';p.write_bytes(b'extra');self.row['output_sha256'][p.name]=digest(p)
        self.assertEqual(stages.validate_run(self.row,self.case)['status'],'FAILED')
    def test_missing_output_rejected(self):
        (self.out/'dy.bin').unlink();self.assertEqual(stages.validate_run(self.row,self.case)['status'],'FAILED')
    def test_missing_hash_rejected(self):
        self.row['output_sha256']['dx.bin']=None;self.assertEqual(stages.validate_run(self.row,self.case)['status'],'FAILED')
    def test_changed_input_rejected(self):
        (self.fixture/'input.bin').write_bytes(b'x'*6);self.assertEqual(stages.validate_run(self.row,self.case)['status'],'FAILED')

    def prepare_native(self):
        for p in self.out.iterdir():p.unlink()
        for name in ['x','y','magnitude']:self.expected.tofile(self.out/('native-'+name+'.bin'))
        np.zeros((2,3),np.float32).tofile(self.out/'native-angle.bin')
        (self.out/'output.bin').write_bytes(bytes(16));(self.out/'native.json').write_text('{}')
        write(self.root/'sealed.json',dict(files={'outputs/'+p.name:dict(sha256=digest(p),bytes=p.stat().st_size) for p in self.out.iterdir()}))
        write(self.root/'migration/rewrite/image-native-gradient-cases.json',dict(vendors={'NPP':[self.case],'NPP+':[self.case]}))
        row=dict(case='probe',return_code=0,input_snapshot='inputs',output='outputs')
        for suffix in ['', '-plus']:write(self.root/('migration/reports/image-I0-Canny-native-probes'+suffix+'-gradients.json'),[row])

    def native_main(self):
        with patch.object(native,'ROOT',self.root),patch.object(native,'Experiment',DummyExperiment),patch.object(native,'record'),patch('builtins.print'):
            return native.main()

    def test_native_positive_exit(self):
        self.prepare_native();self.assertEqual(self.native_main(),0)
    def test_native_wrong_pixels_fail_exit(self):
        self.prepare_native();p=self.out/'native-x.bin';p.write_bytes(b'\x01\x00'+p.read_bytes()[2:])
        seal=json.loads((self.root/'sealed.json').read_text());seal['files']['outputs/'+p.name]['sha256']=digest(p);write(self.root/'sealed.json',seal)
        self.assertEqual(self.native_main(),1)
    def test_native_partial_element_fail_exit(self):
        self.prepare_native();p=self.out/'native-x.bin';p.write_bytes(p.read_bytes()+b'x')
        seal=json.loads((self.root/'sealed.json').read_text());seal['files']['outputs/'+p.name]['sha256']=digest(p);write(self.root/'sealed.json',seal)
        self.assertEqual(self.native_main(),1)
    def test_native_incomplete_case_fail_exit(self):
        self.prepare_native();write(self.root/'migration/reports/image-I0-Canny-native-probes-gradients.json',[])
        self.assertEqual(self.native_main(),1)
    def test_native_failed_process_fail_exit(self):
        self.prepare_native();p=self.root/'migration/reports/image-I0-Canny-native-probes-gradients.json'
        rows=json.loads(p.read_text());rows[0]['return_code']=9;write(p,rows)
        self.assertEqual(self.native_main(),1)

    def test_sdk_existing_prefix_reuses_and_mismatch_seals(self):
        manifests={};previous=[]
        for name,key,variant in [('nvjpeg2000','libnvjpeg_2k','cuda13'),('nppplus','libnpp_plus','cuda12')]:
            prefix=self.root/'build/image-cuda-sdk'/name;prefix.mkdir(parents=True)
            p=prefix/'fixture.h';p.write_text('test SDK identity')
            manifests[name]=dict(manifest={key:dict(version='v',**{'linux-x86_64':{variant:dict(relative_path='fixture',size='1',sha256='a'*64)}})})
            previous.append(dict(SDK=name,version='v',variant=variant,vendor_sha256='a'*64,evidence='old-evidence',files={'fixture.h':dict(bytes=p.stat().st_size,sha256=digest(p))}))
        write(self.root/'migration/reports/image-I0-SDK-manifests.json',dict(results=manifests))
        write(self.root/'migration/reports/image-I0-private-SDKs.json',previous)
        with patch.object(sdk,'ROOT',self.root),patch.object(sdk,'Experiment',DummyExperiment),patch.object(sdk,'record'),patch('builtins.print'):
            self.assertEqual(sdk.main(),0)
            self.assertEqual(DummyExperiment.finished,['OBSERVED','OBSERVED'])
            (self.root/'build/image-cuda-sdk/nvjpeg2000/fixture.h').write_text('changed')
            DummyExperiment.finished=[]
            self.assertEqual(sdk.main(),1)
            self.assertEqual(DummyExperiment.finished,['SDK_UNAVAILABLE','OBSERVED'])
    def test_sdk_download_failure_seals_all_attempts(self):
        manifests={}
        for name,key,variant in [('nvjpeg2000','libnvjpeg_2k','cuda13'),('nppplus','libnpp_plus','cuda12')]:
            manifests[name]=dict(manifest={key:dict(version='v',**{'linux-x86_64':{variant:dict(relative_path='fixture',size='1',sha256='a'*64)}})})
        write(self.root/'migration/reports/image-I0-SDK-manifests.json',dict(results=manifests))
        with patch.object(sdk,'ROOT',self.root),patch.object(sdk,'Experiment',DummyExperiment),patch.object(sdk,'record'),patch('builtins.print'):
            self.assertEqual(sdk.main(),1)
            self.assertEqual(DummyExperiment.finished,['SDK_UNAVAILABLE','SDK_UNAVAILABLE'])

if __name__=='__main__':unittest.main()
