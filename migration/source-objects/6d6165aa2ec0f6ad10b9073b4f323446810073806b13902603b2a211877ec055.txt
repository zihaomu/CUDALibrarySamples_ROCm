"""Dispatch to a batch-specific independent reference with separately sealed source."""
import importlib
from batches4_8_spec import GROUPS
from validate_blas import np
def validate(source,case,d):
 group=next(g for g,rows in GROUPS.items() if source in rows)
 return importlib.import_module('batch'+group[1:]+'_reference').validate(source,case,d)
