"""Eight user-selected profiles; required inputs declared before execution."""
SPARSE = {
    f'cuSPARSE/{k}/{k}_example.c': ['original', 'small-varied', 'nonzero-initial']
    for k in ['cg', 'bicgstab']
}
SPARSE['cuSPARSE/gpsvInterleavedBatch/gpsvInterleavedBatch_example.c'] = [
    'original', 'changed-rhs', 'diagonal-dominant']
SOLVER = {
    f'cuSOLVER/{k}/cusolver_{k}_example.cu': cases
    for k, cases in {
        'gesvdjBatched': ['original', 'perturbed', 'rank-deficient'],
        'syevjBatched': ['original', 'sorted', 'perturbed'],
        'syevdx': ['original', 'value-range', 'all-range', 'empty-range'],
        'sygvdx': ['original', 'value-range', 'all-range', 'empty-range'],
    }.items()
}
GRAPH = {'cuSPARSE/graph_capture/graph_capture_example.c': [
    'original', 'sparse-small', 'cancellation']}
GROUPS = {'sparse': SPARSE, 'solver': SOLVER, 'graph': GRAPH}
ALL = {s: c for group in GROUPS.values() for s, c in group.items()}
