! SPDX-License-Identifier: Apache-2.0
! Port of cuDSS/nvfortran/reordering_phase/reordering_phase.cuf
! Standard Fortran ISO_C_BINDING + HIP replaces CUDA Fortran device attributes.
program main
 use rewrite_sparse_samples
 implicit none
 call run_sparse_sample('reordering_phase')
end program
