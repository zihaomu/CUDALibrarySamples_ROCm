! SPDX-License-Identifier: Apache-2.0
! Port of cuDSS/fortran/reordering_phase/reordering_phase.f90
! Standard Fortran ISO_C_BINDING + HIP replaces CUDA Fortran device attributes.
program main
 use rewrite_sparse_samples
 implicit none
 call run_sparse_sample('reordering_phase')
end program
