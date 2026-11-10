#!/usr/bin/env python3
"""Reject stale approval, empty contracts and missing/inapplicable auxiliary proof."""
import copy,json,unittest
from unittest.mock import patch
from experiment import ROOT,git
import qualify_first as q

class QualificationContract(unittest.TestCase):
    def test_review_covers_current_source_and_rejects_original_base(self):
        self.assertTrue(q.review_identity(dict(source_commit=git('rev-parse','HEAD').strip())))
        self.assertFalse(q.review_identity(dict(source_commit='c6c8eac5cbd1966438c8211b89cfb613633f6375')))

    def test_staged_added_source_needs_review(self):
        original=q.git;head=git('rev-parse','HEAD').strip()
        def staged(*args):
            result=original(*args)
            return result+'tools/moat/unreviewed-staged-source.py\n' if args[:2]==('ls-files','--cached') else result
        with patch.object(q,'git',staged):self.assertFalse(q.review_identity(dict(source_commit=head)))

    def test_required_auxiliary_identity(self):
        record=q.load('rewrite-first-negative.json')['checks'][0];run=q.load('rewrite-first-rocm.json')['gemm3m/changed-values']
        args=dict(parent=run['experiment_id'],comparison=run['comparison_id'],input_hash=run['input_manifest_sha256'])
        sources=['tools/moat/first_reference.py','tools/moat/first_negative.py','tools/moat/inputs.py']
        self.assertTrue(q.auxiliary(record['evidence'],sources,**args))
        self.assertFalse(q.auxiliary('migration/reports/nonexistent-proof',sources,**args))
        self.assertFalse(q.auxiliary(record['evidence'],sources+['tools/moat/bootstrap.py'],**args))
        self.assertFalse(q.auxiliary(record['evidence'],sources,**dict(args,parent='wrong-build-or-run')))
        self.assertFalse(q.auxiliary(record['evidence'],sources,**dict(args,input_hash='0'*64)))

    def test_empty_cases_and_missing_negative_cannot_qualify(self):
        profile=json.loads((ROOT/'migration/rewrite/first-eight.json').read_text())['profiles'][0]
        load=q.load
        def fixture(name):
            if name=='rewrite-first-review.json':return dict(source_commit=git('rev-parse','HEAD').strip(),verdict='APPROVED',findings=[])
            data=load(name)
            if name=='rewrite-first-negative.json':
                data=copy.deepcopy(data);data['checks'][0]['evidence']='migration/reports/nonexistent-proof'
            return data
        with patch.object(q,'load',fixture):
            checks,_,_=q.collect(profile)
            self.assertFalse(all(c['passed'] for c in checks))
            self.assertTrue(any(not c['passed'] and 'integrity-and-current-oracle' in c['check'] for c in checks))
            profile=copy.deepcopy(profile);profile['cases']=[]
            checks,_,_=q.collect(profile)
            self.assertFalse(next(c['passed'] for c in checks if c['check']=='frozen-nonempty-complete-case-contract'))

if __name__=='__main__':unittest.main()
