"""Original profiles and required cases fixed before B4--B8 qualification."""
import json
from catalog import ROOT
plan=json.loads((ROOT/'migration/roadmap.json').read_text())
GROUPS={b['id'].lower():dict.fromkeys(b['sources']) for b in plan['batches'] if b['id'] in ['B4','B5','B6','B7','B8']}
CASES={
 'GemmBatchedEx':['original','nonzero-beta','transpose','changed-values'],
 'CherkEx':['original','nonzero-beta','lower','conjugate'],
 'CsyrkEx':['original','nonzero-beta','lower','transpose'],
 'trttp':['original','lower','padded-lda','odd-size'],
 'tpttr':['original','lower','padded-lda','odd-size'],
 'ormqr':['original','changed-matrix','multiple-rhs','Q-application'],
 'spsv_sell':['original','changed-values','unit-diagonal','upper'],
 'sddmm_bsr':['original','nonzero-beta','changed-pattern','block-column-order'],
 'elementwise_permute_padding':['original','small-asymmetric','small-strided'],
 'einsum':['original','changed-values','non-square'],
 'contraction_trinary':['original','small-nonzero-beta','small-zero-alpha'],
 'contraction_plan_cache':['original','changed-descriptor','corrupt-cache'],
 'Xgetrf':['original','legacy-algorithm','no-pivot','singular-info'],
 'Xsyevdx':['original','value-range','all-range','empty-range'],
 'Xtrtri':['original','lower','unit-diagonal','singular-info'],
 'Xgesvd':['original','rectangular','rank-deficient'],
 'GemmGroupedBatchedEx':['original','negative-alpha','heterogeneous-groups'],
 'GemmExAutoTuning':['original','limited-workspace','changed-values'],
 'LtHSHgemmGroupedSimple':['original','negative-alpha','heterogeneous-groups'],
 'LtSgemmCustomFind':['original','limited-workspace','changed-values'],
 'LtSgemmSimpleAutoTuning':['original','limited-workspace','changed-values'],
 'spmat_convert':['original','base-one','empty-row','changed-values'],
 'spgemm_mem':['original','small-budget','changed-values','empty-row'],
 'spmv_symmetric_csr':['original','upper','changed-values','base-one'],
 'spmvop_csr':['original','changed-values','cancellation'],
 'spmm_csr_op':['original','changed-values','cancellation'],
}
def kind(source):
 from pathlib import PurePosixPath
 p=PurePosixPath(source)
 return p.stem if source.startswith('cuTENSOR/') else p.parent.name
for group in GROUPS.values():
 for source in group:group[source]=CASES[kind(source)]
ALL={s:c for g in GROUPS.values() for s,c in g.items()}
