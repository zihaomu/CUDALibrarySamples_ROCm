#!/usr/bin/env python3
"""Exercise failed processes, timeouts, seal refusal and evidence tampering."""
import shutil,sys,unittest,json,subprocess,time,os,signal
from unittest.mock import patch
from experiment import Experiment,ROOT,digest,recorder_alive
from audit import check

class RecorderContract(unittest.TestCase):
    def test_observed_rejection_schema_and_unknown_outcomes(self):
        import jsonschema
        record=json.loads((ROOT/'migration/reports/rewrite-first-runtime-checks.json').read_text())['tests'][0]
        manifest=json.loads((ROOT/record['evidence']/'manifest.json').read_text());schema=json.loads((ROOT/'migration/moat/schema/experiment.schema.json').read_text())
        jsonschema.validate(manifest,schema)
        manifest['experiment_outcome']='UNRECORDED_NUMERIC_SUCCESS'
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(manifest,schema)
    def test_failure_cannot_be_promoted_and_streams_survive(self):
        e=Experiment('P0','recorder-failure-contract','host',sources=[__file__])
        rc=e.command([sys.executable,'-c','import sys;print("stdout-proof");print("stderr-proof",file=sys.stderr);sys.exit(7)'],'deliberate-exit')
        self.assertEqual(rc,7)
        self.assertIn('stdout-proof',(e.path/e.commands[0]['stdout']).read_text())
        self.assertIn('stderr-proof',(e.path/e.commands[0]['stderr']).read_text())
        with self.assertRaises(ValueError):e.finish('PASSED',dict(checks=[dict(check='dummy',passed=True)]))
        with self.assertRaises(ValueError):e.finish('UNRECORDED_NUMERIC_SUCCESS')
        e.finish('COMMAND_FAILED',reason='Deliberate CPU process exit for recorder self-test')
        with self.assertRaises(RuntimeError):e.command([sys.executable,'-c','pass'],'after-seal')
        self.assertEqual(check(e.path),[])
        copy=ROOT/'build/moat-recorder-tamper'/e.id;shutil.copytree(e.path,copy)
        (copy/'summary.md').write_text('corrupted')
        self.assertIn('summary.md',check(copy))

    def test_timeout_is_preserved(self):
        e=Experiment('P0','recorder-timeout-contract','host',sources=[__file__])
        rc=e.command([sys.executable,'-c','import time;time.sleep(5)'],'deliberate-timeout',timeout=.1)
        self.assertEqual(rc,124);self.assertTrue(e.commands[0]['timed_out'])
        e.finish('TIMEOUT',reason='Deliberate CPU timeout for recorder self-test')
        self.assertEqual(check(e.path),[])

    def test_external_source_object_is_mandatory(self):
        e=Experiment('P0','recorder-object-contract','host',sources=[__file__])
        e.finish('EXECUTED')
        obj=next(iter(json.loads((e.path/'source.json').read_text())['source_objects'].values()))
        from pathlib import Path
        original=Path.is_file
        with patch.object(Path,'is_file',lambda p:False if p==ROOT/obj else original(p)):
            self.assertTrue(any(x.startswith('source-object:') for x in check(e.path)))
        self.assertEqual(check(e.path),[])

    def test_sigkill_recorder_recovers_streams(self):
        code='from experiment import Experiment;import sys;e=Experiment("P0","recorder-killed-contract","host",sources=[]);print(e.path,flush=True);e.command([sys.executable,"-u","-c","import time;print(\\\"child-stream-proof\\\",flush=True);time.sleep(120)"],"interrupted-child")'
        proc=subprocess.Popen([sys.executable,'-c',code],cwd=ROOT/'tools/moat',stdout=subprocess.PIPE,text=True)
        from pathlib import Path
        target=Path(proc.stdout.readline().strip())
        for _ in range(100):
            logs=list((target/'logs').glob('*.stdout.log'))
            if logs and 'child-stream-proof' in logs[0].read_text():break
            time.sleep(.02)
        self.assertTrue(recorder_alive(json.loads((target/'manifest.json').read_text())))
        denied=subprocess.run([sys.executable,str(ROOT/'tools/moat/recover.py'),'--target',str(target),'--reason','test active refusal'],capture_output=True)
        self.assertNotEqual(denied.returncode,0)
        os.kill(proc.pid,signal.SIGKILL);proc.wait();proc.stdout.close()
        self.assertFalse(recorder_alive(json.loads((target/'manifest.json').read_text())))
        recovered=subprocess.run([sys.executable,str(ROOT/'tools/moat/recover.py'),'--target',str(target),'--reason','Deliberate recorder SIGKILL for recovery contract'],capture_output=True,text=True)
        self.assertEqual(recovered.returncode,0,recovered.stderr)
        self.assertEqual(json.loads((target/'manifest.json').read_text())['experiment_outcome'],'INTERRUPTED')
        self.assertIn('child-stream-proof',logs[0].read_text());self.assertEqual(check(target),[])

    def test_finished_child_with_missing_start_identity_can_recover(self):
        code='from experiment import Experiment;import sys,time;e=Experiment("P0","recorder-short-child-contract","host");e.command([sys.executable,"-c","pass"],"short-child");print(e.path,flush=True);time.sleep(120)'
        proc=subprocess.Popen([sys.executable,'-c',code],cwd=ROOT/'tools/moat',stdout=subprocess.PIPE,text=True)
        from pathlib import Path
        from experiment import write
        target=Path(proc.stdout.readline().strip());child=json.loads((target/'subprocess.json').read_text())
        child['start_ticks']=None;write(target/'subprocess.json',child)
        os.kill(proc.pid,signal.SIGKILL);proc.wait();proc.stdout.close()
        recovered=subprocess.run([sys.executable,str(ROOT/'tools/moat/recover.py'),'--target',str(target),'--reason','Fault injection: completed short child with unavailable start ticks'],capture_output=True,text=True)
        self.assertEqual(recovered.returncode,0,recovered.stderr);self.assertEqual(check(target),[])

if __name__=='__main__':unittest.main()
