// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif
/* FP64 CSR; base 0/1; type 0 GENERAL/FULL or 1 SPD/UPPER. */
int rw_sparse_create(int n,int nnz,const int*rows,const int*cols,const double*values,
                     int base,int type,int reorder,void**handle);
int rw_sparse_analyze(void*handle,int*row_perm,int*column_perm,size_t*bytes);
int rw_sparse_set_values(void*handle,int nnz,const double*values);
int rw_sparse_solve(void*handle,int nrhs,const double*b,int ldb,double*x,int ldx,int*info);
int rw_sparse_export(void*handle,const char*label);
int rw_sparse_destroy(void*handle);
#ifdef __cplusplus
}
#endif
