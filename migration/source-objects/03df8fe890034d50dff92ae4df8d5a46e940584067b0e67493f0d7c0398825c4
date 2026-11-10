#!/usr/bin/env python3
"""Regression checks for resumable control setup and lossless inventory refresh."""
import json,shutil,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from experiment import ROOT,write,digest
import bootstrap,inventory

class InfrastructureContract(unittest.TestCase):
    def test_cold_checkout_restores_saved_control(self):
        with tempfile.TemporaryDirectory(prefix='moat-cold-bootstrap-') as folder:
            root=Path(folder)/'CUDALibrarySamples_ROCm';(root/'migration/moat').mkdir(parents=True)
            for name in ['lock.json','control.bundle']:shutil.copyfile(ROOT/'migration/moat'/name,root/'migration/moat'/name)
            lock=json.loads((root/'migration/moat/lock.json').read_text());control=(root/lock['control_checkout']).resolve();run=subprocess.run
            def local_clone(argv,**kwargs):
                if argv[:3]==['git','clone','--no-checkout']:
                    clone=list(argv);clone[3]=str(ROOT.parent/'MOAT_CUDALibrarySamples_ROCm');result=run(clone,**kwargs)
                    run(['git','remote','set-url','origin',lock['upstream_url']],cwd=control,check=True,capture_output=True)
                    return result
                return run(argv,**kwargs)
            self.assertFalse(control.exists())
            with patch.object(bootstrap.subprocess,'run',local_clone):self.assertEqual(bootstrap.ensure(root),control)
            self.assertEqual(bootstrap.validate_existing(root),control)

    def test_inventory_preserves_recorded_state(self):
        with tempfile.TemporaryDirectory(prefix='moat-inventory-') as folder:
            root=Path(folder)
            for name in ['migration/samples.yaml','migration/moat/tasks.json','migration/moat/lock.json','migration/rewrite/first-eight.json','migration/libraries.json']:
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,p)
            for _,_,name in inventory.TARGETS:
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,p)
            task=json.loads((root/'migration/moat/tasks.json').read_text());task['tasks'][0].update(state='IN_PROGRESS',experiments=['preservation-proof'],prerequisites=['frozen-prerequisite']);write(root/'migration/moat/tasks.json',task)
            spec=json.loads((root/'migration/rewrite/first-eight.json').read_text());spec['profiles'][0]['state']='REVIEW_REQUESTED';write(root/'migration/rewrite/first-eight.json',spec)
            libs=json.loads((root/'migration/libraries.json').read_text());libs['libraries'][0]['version']='observed-version-proof';write(root/'migration/libraries.json',libs)
            lock=digest(root/'migration/moat/lock.json')
            with patch.object(inventory,'ROOT',root),patch.object(bootstrap,'validate_existing'):
                inventory.main();inventory.main()
            new=json.loads((root/'migration/moat/tasks.json').read_text())
            self.assertEqual(new['tasks'][0]['experiments'],['preservation-proof']);self.assertEqual(new['tasks'][0]['state'],'IN_PROGRESS')
            self.assertEqual(new['tasks'][0]['prerequisites'],['frozen-prerequisite']);self.assertEqual(task['baseline_catalog_sha256'],new['baseline_catalog_sha256'])
            self.assertEqual(digest(root/'migration/moat/lock.json'),lock)
            self.assertEqual(json.loads((root/'migration/rewrite/first-eight.json').read_text())['profiles'][0]['state'],'REVIEW_REQUESTED')
            self.assertEqual(json.loads((root/'migration/libraries.json').read_text())['libraries'][0]['version'],'observed-version-proof')

    def test_partial_checkout_resumes_and_unsafe_remotes_refuse(self):
        with tempfile.TemporaryDirectory(prefix='moat-bootstrap-') as folder:
            root=Path(folder)/'CUDALibrarySamples_ROCm';(root/'migration/moat').mkdir(parents=True)
            for name in ['lock.json','control.bundle']:shutil.copyfile(ROOT/'migration/moat'/name,root/'migration/moat'/name)
            lock=json.loads((root/'migration/moat/lock.json').read_text());control=(root/lock['control_checkout']).resolve()
            def git(*args):return subprocess.run(['git',*map(str,args)],cwd=control,check=True,capture_output=True,text=True)
            subprocess.run(['git','clone','--no-checkout',str(ROOT.parent/'MOAT_CUDALibrarySamples_ROCm'),str(control)],check=True,capture_output=True)
            git('checkout','-B','bootstrap-test',lock['upstream_commit']);git('remote','set-url','origin',lock['upstream_url'])
            self.assertEqual(bootstrap.ensure(root),control);self.assertEqual(bootstrap.ensure(root),control)
            src=control/'projects'/lock['project']/'src';src.unlink();src.symlink_to(root.parent/'unrelated')
            with self.assertRaisesRegex(RuntimeError,'source'):bootstrap.ensure(root)
            src.unlink();src.symlink_to(root)
            git('remote','set-url','origin','https://example.invalid/forbidden.git')
            with self.assertRaisesRegex(RuntimeError,'origin'):bootstrap.ensure(root)

if __name__=='__main__':unittest.main()
