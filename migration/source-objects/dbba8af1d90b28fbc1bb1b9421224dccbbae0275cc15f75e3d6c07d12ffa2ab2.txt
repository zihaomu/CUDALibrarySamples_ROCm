! SPDX-License-Identifier: Apache-2.0
! Port of cuDSS/nvfortran/uniform_batch/uniform_batch.cuf
! Standard Fortran ISO_C_BINDING + HIP replaces CUDA Fortran device attributes.
program main
 use rewrite_sparse_samples
 implicit none
 call run_sparse_sample('uniform_batch')
end program
