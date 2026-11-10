#!/usr/bin/env python3
"""Exercise failed processes, timeouts, seal refusal and evidence tampering."""
import shutil,sys,unittest
from experiment import Experiment,ROOT
from audit import check

class RecorderContract(unittest.TestCase):
    def test_failure_cannot_be_promoted_and_streams_survive(self):
        e=Experiment('P0','recorder-failure-contract','host',sources=[__file__])
        rc=e.command([sys.executable,'-c','import sys;print("stdout-proof");print("stderr-proof",file=sys.stderr);sys.exit(7)'],'deliberate-exit')
        self.assertEqual(rc,7)
        self.assertIn('stdout-proof',(e.path/e.commands[0]['stdout']).read_text())
        self.assertIn('stderr-proof',(e.path/e.commands[0]['stderr']).read_text())
        with self.assertRaises(ValueError):e.finish('PASSED',dict(checks=[dict(check='dummy',passed=True)]))
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

if __name__=='__main__':unittest.main()
