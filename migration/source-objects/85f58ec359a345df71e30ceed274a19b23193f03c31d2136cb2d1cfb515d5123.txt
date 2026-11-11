#!/usr/bin/env python3
"""Review approval must bind distinct investigators and the executable file set."""
import copy,unittest
from unittest.mock import patch
from experiment import git
import qualify_canny_plus as q

class ReviewIdentity(unittest.TestCase):
 def review(self):
  return dict(source_commit=git('rev-parse','HEAD').strip(),verdict='APPROVED',reviewers=[dict(reviewer_id=str(i),scope=s,verdict='APPROVED') for i,s in enumerate(sorted(q.REVIEW_SCOPES))])
 def test_three_distinct_scoped_reviewers(self):
  r=self.review()
  with patch.object(q.review_gate,'review_identity',return_value=True):
   self.assertTrue(q.reviewed(r,[],[]))
   for fault in ['duplicate','anonymous','missing-scope','rejected','missing-reviewer']:
    bad=copy.deepcopy(r)
    if fault=='duplicate':bad['reviewers'][1]['reviewer_id']=bad['reviewers'][0]['reviewer_id']
    elif fault=='anonymous':bad['reviewers'][0].pop('reviewer_id')
    elif fault=='missing-scope':bad['reviewers'][0].pop('scope')
    elif fault=='rejected':bad['reviewers'][0]['verdict']='REQUEST_CHANGES'
    else:bad['reviewers'].pop()
    self.assertFalse(q.reviewed(bad,[],[]),fault)
 def test_current_tree(self):self.assertTrue(q.reviewed(self.review(),[],[]))
 def test_untracked_import_hook_is_rejected(self):
  original=q.review_gate.git
  def changed(*args):
   if args[:2]==('ls-files','--others'):return 'rocm/python/sitecustomize.py\n'
   return original(*args)
  with patch.object(q.review_gate,'git',changed):self.assertFalse(q.reviewed(self.review(),[],[]))
 def test_staged_added_source_is_rejected(self):
  original=q.review_gate.git
  def changed(*args):
   answer=original(*args)
   return answer+'rocm/python/sitecustomize.py\n' if args[:2]==('ls-files','--cached') else answer
  with patch.object(q.review_gate,'git',changed):self.assertFalse(q.reviewed(self.review(),[],[]))
 def test_changed_current_bytes_is_rejected(self):
  with patch.object(q.review_gate,'review_identity',return_value=False):self.assertFalse(q.reviewed(self.review(),[],[]))
if __name__=='__main__':unittest.main()
