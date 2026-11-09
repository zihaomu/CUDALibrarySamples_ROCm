/*
 * SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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


#include "hip/hip_runtime.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>

#include <mpi.h>

#include <cusolverMp.h>

#include "helpers.h"

/* print matrix */
static void print_host_matrix(const int64_t m, const int64_t n, const double* A, const int64_t lda, const char* msg)
{
    printf("print_host_matrix : %s\n", msg);

    for (int64_t i = 0; i < m; i++)
    {
        for (int64_t j = 0; j < n; j++)
            printf("%.6e  ", A[i + j * lda]);
        printf("\n");
    }
}

/* set random matrix A, dim(A) = [m,n] */
static void generate_random_matrix(const int64_t m, const int64_t n, double* A, const int64_t lda)
{
    for (int64_t j = 0; j < n; ++j)
    {
        for (int64_t i = 0; i < m; ++i)
        {
            A[i + j * lda] = (double)(rand()) / RAND_MAX;
        }
    }
}

/* compute error for A X = B, dim(A) = [m,n], dim(B) = [m,nrhs], dim(X) = [n,nrhs] */
static void compute_rhs(const int64_t m,
                        const int64_t n,
                        const int64_t nrhs,
                        const double* A,
                        const int64_t lda,
                        const double* X,
                        const int64_t ldx,
                        double*       B,
                        const int64_t ldb)
{
    for (int64_t j = 0; j < nrhs; ++j)
    {
        for (int64_t i = 0; i < m; ++i)
        {
            double tmp = 0;
            for (int64_t k = 0; k < n; ++k)
            {
                tmp += A[i + k * lda] * X[k + j * ldx];
            }
            B[i + j * ldb] = tmp;
        }
    }
}

/* compute two norm of matrix A */
static double compute_norm2(const int64_t m, const int64_t n, const double* A, const int64_t lda)
{
    double norm_A = 0;
    for (int64_t j = 0; j < n; ++j)
    {
        for (int64_t i = 0; i < m; ++i)
        {
            const double val = A[i + j * lda];
            norm_A += val * val;
        }
    }
    return sqrt(norm_A);
}

/* compute error for A X = B, dim(A) = [m,n], dim(B) = [m,nrhs], dim(X) = [n,nrhs] */
static double compute_error(const int64_t m,
                            const int64_t n,
                            const int64_t nrhs,
                            const double* A,
                            const int64_t lda,
                            const double* X,
                            const int64_t ldx,
                            double*       B,
                            const int64_t ldb)
{
    /// | AX-B | / max(m,n) |A| |X|
    const double norm_A = compute_norm2(m, n, A, lda);
    const double norm_X = compute_norm2(n, nrhs, X, ldx);

    for (int64_t j = 0; j < nrhs; ++j)
    {
        for (int64_t i = 0; i < m; ++i)
        {
            double tmp = 0;
            for (int64_t k = 0; k < n; ++k)
            {
                tmp += A[i + k * lda] * X[k + j * ldx];
            }
            B[i + j * ldb] -= tmp;
        }
    }
    const double norm_R = compute_norm2(m, nrhs, B, ldb);

    return (norm_R / fmax(m, n) / norm_A / norm_X);
}


int main(int argc, char* argv[])
{
    Options opts = { .m           = 20,
                     .n           = 8,
                     .nrhs        = 8,
                     .mbA         = 2,
                     .nbA         = 2,
                     .mbB         = 2,
                     .nbB         = 2,
                     .mbQ         = 1,
                     .nbQ         = 1,
                     .ia          = 3,
                     .ja          = 1,
                     .ib          = 3,
                     .jb          = 1,
                     .iq          = 1,
                     .jq          = 1,
                     .p           = 1,
                     .q           = 2,
                     .grid_layout = 'C',
                     .verbose     = false };

    parse(&opts, argc, argv);
    validate(&opts);

    int sample_ok = 1;

    /* Initialize MPI library */
    MPI_Init(NULL, NULL);

    /* Use MPI_COMM_WORLD for process coordination. */
    MPI_Comm mpi_global_comm = MPI_COMM_WORLD;

    /* Get MPI rank id and communicator size. */
    int commSize, rank;
    MPI_Comm_size(mpi_global_comm, &commSize);
    MPI_Comm_rank(mpi_global_comm, &rank);

    if (rank == 0) print(&opts);

    /* Define dimensions, block sizes and offsets of A and B matrices */
    const int64_t m    = opts.m;
    const int64_t n    = opts.n;
    const int64_t nrhs = opts.nrhs;

    /* Current implementation supports over-determined system without transpose (m >= n) case */
    SAMPLE_ASSERT(m >= n);

    /* Offsets of A and B matrices (base-1) */
    const int64_t ia = opts.ia;
    const int64_t ja = opts.ja;
    const int64_t ib = opts.ib;
    const int64_t jb = opts.jb;

    /* Tile sizes */
    const int64_t mbA = opts.mbA;
    const int64_t nbA = opts.nbA;
    const int64_t mbB = opts.mbB;
    const int64_t nbB = opts.nbB;

    /* Define grid of processors */
    const int nprow = opts.p;
    const int npcol = opts.q;

    /* Convert grid layout to cusolverMp grid mapping */
    const cusolverMpGridMapping_t gridLayout =
            (opts.grid_layout == 'C' || opts.grid_layout == 'c' ? CUSOLVERMP_GRID_MAPPING_COL_MAJOR
                                                                : CUSOLVERMP_GRID_MAPPING_ROW_MAJOR);

    /* Current implementation only allows RSRC,CSRC=(0,0) */
    const uint32_t rsrca = 0;
    const uint32_t csrca = 0;
    const uint32_t rsrcb = 0;
    const uint32_t csrcb = 0;

    /*
     * Initialize device context for this process
     */
    int         localRank = getLocalRank();
    hipError_t cudaStat  = hipSetDevice(localRank);
    SAMPLE_ASSERT(cudaStat == hipSuccess);
    cudaStat = hipFree(0);
    SAMPLE_ASSERT(cudaStat == hipSuccess);

    /* Error codes */
    hipsolverStatus_t cusolverStat = HIPSOLVER_STATUS_SUCCESS;
    ncclResult_t     ncclStat     = ncclSuccess;

    /* Create communicator */
    ncclComm_t ncclComm = createNcclComm(commSize, rank);

    /* Create local stream */
    hipStream_t stream = NULL;
    cudaStat            = hipStreamCreate(&stream);
    SAMPLE_ASSERT(cudaStat == hipSuccess);

    /* Initialize cusolverMp library handle */
    cusolverMpHandle_t handle = NULL;
    cusolverStat              = cusolverMpCreate(&handle, localRank, stream);
    SAMPLE_ASSERT(cusolverStat == HIPSOLVER_STATUS_SUCCESS);

    /* cusolverMp grids */
    cusolverMpGrid_t gridA = NULL;
    cusolverMpGrid_t gridB = NULL;

    /* cusolverMp matrix descriptors */
    cusolverMpMatrixDescriptor_t descA = NULL;
    cusolverMpMatrixDescriptor_t descB = NULL;

    /* Distributed matrices A X = B */
    void* d_A = NULL;
    void* d_B = NULL;

    /* Distributed device workspace */
    void* d_gelsWork = NULL;

    /* Distributed host workspace */
    void* h_gelsWork = NULL;

    /* size of workspace on device */
    size_t gelsWorkspaceInBytesOnDevice = 0;

    /* size of workspace on host */
    size_t gelsWorkspaceInBytesOnHost = 0;

    /* error codes from cusolverMp (device) */
    int* d_gelsInfo = NULL;

    /* error codes from cusolverMp (host) */
    int h_gelsInfo = 0;

    /* =========================================== */
    /*          Create inputs on master rank       */
    /* =========================================== */

    /* Single process per device */
    SAMPLE_ASSERT((nprow * npcol) == commSize);

    /* =========================================== */
    /*          Create inputs on master rank       */
    /* =========================================== */

    const int64_t m_global_A = (ia - 1) + m;
    const int64_t n_global_A = (ja - 1) + n;
    const int64_t m_global_B = (ib - 1) + m;
    const int64_t n_global_B = (jb - 1) + nrhs;

    double* h_A = NULL;
    double* h_B = NULL;
    double* h_X = NULL;

    if (rank == 0)
    {
        /* allocate host workspace */
        h_A = (double*)malloc(m_global_A * n_global_A * sizeof(double));
        h_B = (double*)malloc(m_global_B * n_global_B * sizeof(double));
        h_X = (double*)malloc(m_global_B * n_global_B * sizeof(double));

        /* reset host workspace */
        memset(h_A, 0xFF, m_global_A * n_global_A * sizeof(double));
        memset(h_B, 0xFF, m_global_B * n_global_B * sizeof(double));
        memset(h_X, 0xFF, m_global_B * n_global_B * sizeof(double));

        /* Set A random */
        double* ptr_A = &h_A[(ia - 1) + (ja - 1) * m_global_A];
        double* ptr_B = &h_B[(ib - 1) + (jb - 1) * m_global_B];
        double* ptr_X = &h_X[(ib - 1) + (jb - 1) * m_global_B];

        generate_random_matrix(m, n, ptr_A, m_global_A);
        generate_random_matrix(n, nrhs, ptr_X, m_global_B);
        compute_rhs(m, n, nrhs, ptr_A, m_global_A, ptr_X, m_global_B, ptr_B, m_global_B);

        /* print input matrices */
        if (opts.verbose)
        {
            print_host_matrix(m_global_A, n_global_A, h_A, m_global_A, "Input matrix A");
            print_host_matrix(m_global_B, n_global_B, h_B, m_global_B, "Input matrix B");
        }
    }

    /* compute process grid index */
    int myRowRank, myColRank;
    if (gridLayout == CUSOLVERMP_GRID_MAPPING_COL_MAJOR)
    {
        myRowRank = rank % nprow;
        myColRank = rank / nprow;
    }
    else
    {
        myRowRank = rank / npcol;
        myColRank = rank % npcol;
    }

    /* compute the load leading dimension of the device buffers */
    const int64_t m_local_A = cusolverMpNUMROC(m_global_A, mbA, myRowRank, rsrca, nprow);
    const int64_t n_local_A = cusolverMpNUMROC(n_global_A, nbA, myColRank, csrca, npcol);

    const int64_t m_local_B = cusolverMpNUMROC(m_global_B, mbB, myRowRank, rsrcb, nprow);
    const int64_t n_local_B = cusolverMpNUMROC(n_global_B, nbB, myColRank, csrcb, npcol);

    /* Allocate global d_A */
    cudaStat = hipMalloc((void**)&d_A, m_local_A * n_local_A * sizeof(double));
    SAMPLE_ASSERT(cudaStat == hipSuccess);

    /* Allocate global d_B */
    cudaStat = hipMalloc((void**)&d_B, m_local_B * n_local_B * sizeof(double));
    SAMPLE_ASSERT(cudaStat == hipSuccess);

    /* =========================================== */
    /*          CREATE GRID DESCRIPTORS            */
    /* =========================================== */
    cusolverStat = cusolverMpCreateDeviceGrid(handle, &gridA, ncclComm, nprow, npcol, gridLayout);
    SAMPLE_ASSERT(cusolverStat == HIPSOLVER_STATUS_SUCCESS);

    cusolverStat = cusolverMpCreateDeviceGrid(handle, &gridB, ncclComm, nprow, npcol, gridLayout);
    SAMPLE_ASSERT(cusolverStat == HIPSOLVER_STATUS_SUCCESS);

    /* =========================================== */
    /*        CREATE MATRIX DESCRIPTORS            */
    /* =========================================== */
    cusolverStat = cusolverMpCreateMatrixDesc(
            &descA, gridA, HIP_R_64F, m_global_A, n_global_A, mbA, nbA, rsrca, csrca, m_local_A);

    SAMPLE_ASSERT(cusolverStat == HIPSOLVER_STATUS_SUCCESS);

    cusolverStat = cusolverMpCreateMatrixDesc(
            &descB, gridB, HIP_R_64F, m_global_B, n_global_B, mbB, nbB, rsrcb, csrcb, m_local_B);
    SAMPLE_ASSERT(cusolverStat == HIPSOLVER_STATUS_SUCCESS);

    /* =========================================== */
    /*             ALLOCATE D_INFO                 */
    /* =========================================== */

    cudaStat = hipMalloc((void**)&d_gelsInfo, sizeof(int));
    SAMPLE_ASSERT(cudaStat == hipSuccess);

    /* =========================================== */
    /*                RESET D_INFO                 */
    /* =========================================== */

    cudaStat = hipMemset(d_gelsInfo, 0, sizeof(int));
    SAMPLE_ASSERT(cudaStat == hipSuccess);

    /* =========================================== */
    /*     QUERY WORKSPACE SIZE FOR MP ROUTINES    */
    /* =========================================== */

    cusolverStat = cusolverMpGels_bufferSize(handle,
                                             HIPBLAS_OP_N,
                                             m,
                                             n,
                                             nrhs,
                                             d_A,
                                             ia,
                                             ja,
                                             descA,
                                             d_B,
                                             ib,
                                             jb,
                                             descB,
                                             HIP_R_64F,
                                             &gelsWorkspaceInBytesOnDevice,
                                             &gelsWorkspaceInBytesOnHost);
    SAMPLE_ASSERT(cusolverStat == HIPSOLVER_STATUS_SUCCESS);

    /* =========================================== */
    /*         ALLOCATE GELS WORKSPACE             */
    /* =========================================== */

    cudaStat = hipMalloc((void**)&d_gelsWork, gelsWorkspaceInBytesOnDevice);
    SAMPLE_ASSERT(cudaStat == hipSuccess);

    h_gelsWork = (void*)malloc(gelsWorkspaceInBytesOnHost);
    SAMPLE_ASSERT(h_gelsWork != NULL);

    /* =========================================== */
    /*      SCATTER MATRICES A AND B FROM MASTER   */
    /* =========================================== */
    cusolverStat = cusolverMpMatrixScatterH2D(handle,
                                              m_global_A,
                                              n_global_A,
                                              (void*)d_A,
                                              1,
                                              1,
                                              descA,
                                              0, /* root rank */
                                              (void*)h_A,
                                              m_global_A);
    SAMPLE_ASSERT(cusolverStat == HIPSOLVER_STATUS_SUCCESS);

    cusolverStat = cusolverMpMatrixScatterH2D(handle,
                                              m_global_B,
                                              n_global_B,
                                              (void*)d_B,
                                              1,
                                              1,
                                              descB,
                                              0, /* root rank */
                                              (void*)h_B,
                                              m_global_B);
    SAMPLE_ASSERT(cusolverStat == HIPSOLVER_STATUS_SUCCESS);

    /* sync wait for data to arrive to device */
    cudaStat = hipStreamSynchronize(stream);
    SAMPLE_ASSERT(cudaStat == hipSuccess);

    /* =========================================== */
    /*                   CALL PGELS                */
    /* =========================================== */

    cusolverStat = cusolverMpGels(handle,
                                  HIPBLAS_OP_N,
                                  m,
                                  n,
                                  nrhs,
                                  d_A,
                                  ia,
                                  ja,
                                  descA,
                                  d_B,
                                  ib,
                                  jb,
                                  descB,
                                  HIP_R_64F,
                                  d_gelsWork,
                                  gelsWorkspaceInBytesOnDevice,
                                  h_gelsWork,
                                  gelsWorkspaceInBytesOnHost,
                                  d_gelsInfo);
    SAMPLE_ASSERT(cusolverStat == HIPSOLVER_STATUS_SUCCESS);

    /* sync after PGELS */
    cudaStat = hipStreamSynchronize(stream);
    SAMPLE_ASSERT(cudaStat == hipSuccess);

    /* copy d_gelsInfo to host */
    cudaStat = hipMemcpyAsync(&h_gelsInfo, d_gelsInfo, sizeof(int), hipMemcpyDeviceToHost, stream);
    SAMPLE_ASSERT(cudaStat == hipSuccess);

    /* wait for d_gelsInfo copy */
    cudaStat = hipStreamSynchronize(stream);
    SAMPLE_ASSERT(cudaStat == hipSuccess);

    /* check return value of cusolverMpgels */
    SAMPLE_ASSERT(h_gelsInfo == 0);

    /* =================================== */
    /*      GATHER MATRICES B TO MASTER    */
    /* =================================== */

    /* Copy solution to h_X */
    cusolverStat = cusolverMpMatrixGatherD2H(handle,
                                             m_global_B,
                                             n_global_B,
                                             (void*)d_B,
                                             1,
                                             1,
                                             descB,
                                             0, /* master rank, destination */
                                             (void*)h_X,
                                             m_global_B);
    SAMPLE_ASSERT(cusolverStat == HIPSOLVER_STATUS_SUCCESS);

    /* sync wait for data to arrive to host */
    cudaStat = hipStreamSynchronize(stream);
    SAMPLE_ASSERT(cudaStat == hipSuccess);

    /* =========================================== */
    /*            CHECK RESIDUAL ON MASTER         */
    /* =========================================== */
    if (rank == 0)
    {
        /* print input matrices */
        if (opts.verbose)
        {
            print_host_matrix(m_global_B, n_global_B, h_X, m_global_B, "Output matrix X");
        }

        /* pointers to matrices A, B, and X */
        double* ptr_A = &h_A[(ia - 1) + (ja - 1) * m_global_A];
        double* ptr_B = &h_B[(ib - 1) + (jb - 1) * m_global_B];
        double* ptr_X = &h_X[(ib - 1) + (jb - 1) * m_global_B];

        /* compute error, B is overwritten with residual, B = B - AX */
        const double rel_err = compute_error(m, n, nrhs, ptr_A, m_global_A, ptr_X, m_global_B, ptr_B, m_global_B);
        const double tol     = 1.0e-10;
        const int    ok      = (rel_err < tol);

        /* relative error is around machine zero  */
        printf("|b - A*x|/(max(m,n)*|A|*|x|) = %E\n\n", rel_err);
        printf("  GELS check: %s  (threshold: %E)\n", ok ? "PASS" : "FAIL", tol);
        sample_ok = sample_ok && ok;
    }


    /* =========================================== */
    /*        CLEAN UP HOST WORKSPACE ON MASTER    */
    /* =========================================== */
    if (rank == 0)
    {
        if (h_A)
        {
            free(h_A);
            h_A = NULL;
        }

        if (h_B)
        {
            free(h_B);
            h_B = NULL;
        }

        if (h_X)
        {
            free(h_X);
            h_X = NULL;
        }
    }

    /* =========================================== */
    /*           DESTROY MATRIX DESCRIPTORS        */
    /* =========================================== */

    cusolverStat = cusolverMpDestroyMatrixDesc(descA);
    SAMPLE_ASSERT(cusolverStat == HIPSOLVER_STATUS_SUCCESS);

    cusolverStat = cusolverMpDestroyMatrixDesc(descB);
    SAMPLE_ASSERT(cusolverStat == HIPSOLVER_STATUS_SUCCESS);

    /* =========================================== */
    /*             DESTROY MATRIX GRIDS            */
    /* =========================================== */

    cusolverStat = cusolverMpDestroyGrid(gridA);
    SAMPLE_ASSERT(cusolverStat == HIPSOLVER_STATUS_SUCCESS);

    cusolverStat = cusolverMpDestroyGrid(gridB);
    SAMPLE_ASSERT(cusolverStat == HIPSOLVER_STATUS_SUCCESS);

    /* =========================================== */
    /*          DEALLOCATE DEVICE WORKSPACE        */
    /* =========================================== */

    if (d_A)
    {
        cudaStat = hipFree(d_A);
        SAMPLE_ASSERT(cudaStat == hipSuccess);
        d_A = NULL;
    }

    if (d_B)
    {
        cudaStat = hipFree(d_B);
        SAMPLE_ASSERT(cudaStat == hipSuccess);
        d_B = NULL;
    }

    if (d_gelsWork)
    {
        cudaStat = hipFree(d_gelsWork);
        SAMPLE_ASSERT(cudaStat == hipSuccess);
        d_gelsWork = NULL;
    }

    if (d_gelsInfo)
    {
        cudaStat = hipFree(d_gelsInfo);
        SAMPLE_ASSERT(cudaStat == hipSuccess);
        d_gelsInfo = NULL;
    }

    /* =========================================== */
    /*         DEALLOCATE HOST WORKSPACE           */
    /* =========================================== */
    if (h_gelsWork)
    {
        free(h_gelsWork);
        h_gelsWork = NULL;
    }

    /* =========================================== */
    /*                      CLEANUP                */
    /* =========================================== */

    /* Destroy cusolverMp handle */
    cusolverStat = cusolverMpDestroy(handle);
    SAMPLE_ASSERT(cusolverStat == HIPSOLVER_STATUS_SUCCESS);

    /* sync before ncclCommDestroy */
    cudaStat = hipStreamSynchronize(stream);
    SAMPLE_ASSERT(cudaStat == hipSuccess);

    /* destroy nccl communicator */
    ncclStat = ncclCommDestroy(ncclComm);
    SAMPLE_ASSERT(ncclStat == ncclSuccess);

    /* destroy user stream */
    cudaStat = hipStreamDestroy(stream);
    SAMPLE_ASSERT(cudaStat == hipSuccess);

    /* MPI barrier before MPI_Finalize */
    MPI_Barrier(MPI_COMM_WORLD);
    sample_ok = sample_all_ranks_succeeded(sample_ok);

    /* Finalize MPI environment */
    MPI_Finalize();

    if (rank == 0)
    {
        printf("%s\n", sample_ok ? "[SUCCEEDED]" : "[FAILED]");
    }

    return sample_ok ? 0 : 1;
}
