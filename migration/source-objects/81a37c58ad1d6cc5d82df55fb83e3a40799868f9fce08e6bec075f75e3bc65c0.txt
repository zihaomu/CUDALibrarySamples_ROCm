/*
 * SPDX-FileCopyrightText: Copyright (c) 1993-2022 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include <hip/hip_runtime.h>
#include <hipsparse.h>
#include <stdio.h>
#include <stdlib.h>

#define CHECK_CUDA(func)                                                       \
{                                                                              \
    hipError_t status = (func);                                               \
    if (status != hipSuccess) {                                               \
        printf("CUDA API failed at line %d with error: %s (%d)\n",             \
               __LINE__, hipGetErrorString(status), status);                  \
        return EXIT_FAILURE;                                                   \
    }                                                                          \
}

#define CHECK_CUSPARSE(func)                                                   \
{                                                                              \
    hipsparseStatus_t status = (func);                                          \
    if (status != HIPSPARSE_STATUS_SUCCESS) {                                   \
        printf("CUSPARSE API failed at line %d with error: %s (%d)\n",         \
               __LINE__, hipsparseGetErrorString(status), status);              \
        return EXIT_FAILURE;                                                   \
    }                                                                          \
}

//               | 1  0  2  3 |
//               | 0  4  0  0 |
// coo matrix:   | 5  0  6  7 |
//               | 0  8  0  9 |
//               | 0 10 11  0 |

int main(void) {
    int    num_rows     = 4;
    int    num_columns  = 4;
    int    nnz          = 11;
    int    h_rows[]    = {3, 2, 0, 3, 0, 4, 1, 0, 4, 2, 2};     // unsorted
    int    h_columns[] = {1, 0, 0, 3, 2, 2, 1, 3, 1, 2, 3};     // unsorted
    double h_values[]  = {8.0, 5.0, 1.0, 9.0, 2.0, 11.0, 4.0, 3.0, 10.0, 6.0,
                          7.0};                                 // unsorted
    double h_values_sorted[11]; // nnz
    int    h_permutation[11];   // nnz
    int    h_rows_ref[]    = {0, 0, 0, 1, 2, 2, 2, 3, 3, 4, 4}; // sorted
    int    h_columns_ref[] = {0, 2, 3, 1, 0, 2, 3, 1, 3, 1, 2}; // sorted
    double h_values_ref[]  = {1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0,
                              10.0, 11.0};                      // sorted
    int    h_permutation_ref[] = {2, 4, 7, 6, 1, 9, 10, 0, 3, 8, 5};
    // sort(h_coo_values)[i] = h_coo_values[h_permutation_ref[i]]
    //--------------------------------------------------------------------------
    // Device memory management
    int    *d_rows, *d_columns, *d_permutation;
    double *d_values, *d_values_sorted;
    void   *d_buffer;
    size_t bufferSize;
    CHECK_CUDA( hipMalloc((void**) &d_rows,          nnz * sizeof(int)) )
    CHECK_CUDA( hipMalloc((void**) &d_columns,       nnz * sizeof(int)) )
    CHECK_CUDA( hipMalloc((void**) &d_values,        nnz * sizeof(double)) )
    CHECK_CUDA( hipMalloc((void**) &d_values_sorted, nnz * sizeof(double)) )
    CHECK_CUDA( hipMalloc((void**) &d_permutation,   nnz * sizeof(int)) )

    CHECK_CUDA( hipMemcpy(d_rows, h_rows, nnz * sizeof(int),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(d_columns, h_columns, nnz * sizeof(int),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(d_values, h_values, nnz * sizeof(double),
                           hipMemcpyHostToDevice) )
    //--------------------------------------------------------------------------
    // CUSPARSE APIs
    hipsparseHandle_t handle = NULL;
    hipsparseSpVecDescr_t vec_permutation;
    hipsparseDnVecDescr_t vec_values;
    CHECK_CUSPARSE( hipsparseCreate(&handle) )
    // Create sparse vector for the permutation
    CHECK_CUSPARSE( hipsparseCreateSpVec(&vec_permutation, nnz, nnz,
                                        d_permutation, d_values_sorted,
                                        HIPSPARSE_INDEX_32I,
                                        HIPSPARSE_INDEX_BASE_ZERO, HIP_R_64F) )
    // Create dense vector for wrapping the original coo values
    CHECK_CUSPARSE( hipsparseCreateDnVec(&vec_values, nnz, d_values,
                                        HIP_R_64F) )

    // Query working space of COO sort
    CHECK_CUSPARSE( hipsparseXcoosort_bufferSizeExt(handle, num_rows,
                                                   num_columns, nnz, d_rows,
                                                   d_columns, &bufferSize) )
    CHECK_CUDA( hipMalloc(&d_buffer, bufferSize) )
    // Setup permutation vector to identity
    CHECK_CUSPARSE( hipsparseCreateIdentityPermutation(handle, nnz,
                                                      d_permutation) )
    CHECK_CUSPARSE( hipsparseXcoosortByRow(handle, num_rows, num_columns, nnz,
                                          d_rows, d_columns, d_permutation,
                                          d_buffer) )
    CHECK_CUSPARSE( hipsparseGather(handle, vec_values, vec_permutation) )
    // destroy matrix/vector descriptors
    CHECK_CUSPARSE( hipsparseDestroySpVec(vec_permutation) )
    CHECK_CUSPARSE( hipsparseDestroyDnVec(vec_values) )
    CHECK_CUSPARSE( hipsparseDestroy(handle) )
    //--------------------------------------------------------------------------
    // device result check
    CHECK_CUDA( hipMemcpy(h_rows, d_rows, nnz * sizeof(int),
                           hipMemcpyDeviceToHost) )
    CHECK_CUDA( hipMemcpy(h_columns, d_columns, nnz * sizeof(int),
                           hipMemcpyDeviceToHost) )
    CHECK_CUDA( hipMemcpy(h_values_sorted, d_values_sorted,
                           nnz * sizeof(double), hipMemcpyDeviceToHost) )
    CHECK_CUDA( hipMemcpy(h_permutation, d_permutation,
                           nnz * sizeof(int), hipMemcpyDeviceToHost) )
    int correct = 1;
    for (int i = 0; i < nnz; i++) {
        if (h_rows[i]          != h_rows_ref[i]    ||
            h_columns[i]       != h_columns_ref[i] ||
            h_values_sorted[i] != h_values_ref[i]  ||
            h_permutation[i]   != h_permutation_ref[i]) {
            correct = 0;
            break;
        }
    }
    if (correct)
        printf("coosort_example test PASSED\n");
    else
        printf("coosort_example test FAILED: wrong result\n");
    //--------------------------------------------------------------------------
    // device memory deallocation
    CHECK_CUDA( hipFree(d_rows) )
    CHECK_CUDA( hipFree(d_columns) )
    CHECK_CUDA( hipFree(d_permutation) )
    CHECK_CUDA( hipFree(d_values) )
    CHECK_CUDA( hipFree(d_values_sorted) )
    CHECK_CUDA( hipFree(d_buffer) )
    return EXIT_SUCCESS;
}