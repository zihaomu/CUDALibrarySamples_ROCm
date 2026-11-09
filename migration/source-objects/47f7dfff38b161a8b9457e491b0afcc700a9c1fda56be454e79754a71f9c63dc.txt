"""The 17 user-selected profiles and required cases, defined before qualification."""
SPARSE={f'cuSPARSE/{name}/{name}_example.c':['original','changed-values'] for name in ['spvv','spgemm','spgemm_reuse']}
BLAS={f'cuBLAS/Level-1/{name}/cublas_{name}_example.cu':cases for name,cases in {
 'amax':['original','ties','empty'], 'amin':['original','ties','empty'],
 'rotg':['original','zero','negative'], 'rotm':['original','flag-minus2','flag-minus1','flag-zero'],
 'rotmg':['original','zero','negative','rescale','rescale-large','rescale-asymmetric']}.items()}
BLAS.update({f'cuBLAS/Level-3/{name}/cublas_{name}_example.cu':['original','negative-alpha'] for name in ['gemmBatched','gemmGroupedBatched','trsmBatched']})
TENSOR={f'cuTENSOR/{name}.cu':['original','small-nonzero','small-zero'] for name in ['elementwise_binary','elementwise_permute','elementwise_trinary','reduction']}
SOLVER={f'cuSOLVER/{name}/cusolver_{name}_example.cu':['original'] for name in ['Xgeqrf','Xpotrf']}
GROUPS={'sparse':SPARSE,'blas':BLAS,'tensor':TENSOR,'solver':SOLVER}
ALL={source:cases for group in GROUPS.values() for source,cases in group.items()}
