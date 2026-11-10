"""B9--B11 source profiles and required cases declared before qualification."""
import json,pathlib
from catalog import ROOT
plan=json.loads((ROOT/'migration/roadmap.json').read_text())
GROUPS={b['id'].lower():{} for b in plan['batches'] if b['id'] in ['B9','B10','B11']}
for b in plan['batches']:
 if b['id'].lower() not in GROUPS:continue
 for s in b['sources']:
  if b['id']=='B9':cases=['original','variable-batch','boundary-lengths','random','repeat','corrupt-stream','truncated-stream','cross-library-interop']
  elif b['id']=='B10':cases=['original-corpus','formats-scale','roi-boundary','batch-multi-instance','invalid-cli','postprocess','python-integration']
  else:cases=['original','changed-values','varied-pattern','reorder-natural','pivot-required','singular-info','indefinite','configuration']
  GROUPS[b['id'].lower()][s]=cases
ALL={s:cases for g in GROUPS.values() for s,cases in g.items()}
def kind(s):return pathlib.PurePosixPath(s).stem if s.startswith('nvCOMP/') else pathlib.PurePosixPath(s).parent.name
