/*
 * SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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


#ifndef CUSOLVERSP2CUDSS_UTILS_HPP
#define CUSOLVERSP2CUDSS_UTILS_HPP

/// std headers
#include <type_traits>
#include <cassert>
#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <algorithm>
#include <memory>
#include <numeric>
#include <complex>
#include <random>
#include <chrono>
#include <cfloat>

#if !defined(DISABLE_CUSPARSE_DEPRECATED)
#define DISABLE_CUSPARSE_DEPRECATED 1
#endif

#include <hip/hip_complex.h>
#include <hip/hip_runtime.h> 
#include <hipsolver.h>
#include "cudss.h"

int parse_cmdline(int argc, char **argv, const std::string &option) {
  char **beg = argv, **end = argv+argc;
  char **iter = std::find(beg, end, option);

  return (iter != end);
}

int parse_cmdline(int argc, char **argv, const std::string &option, char** value) {
  char **beg = argv, **end = argv+argc;
  char **iter = std::find(beg, end, option);

  *value = (iter != end && ++iter != end) ? *iter : nullptr;    

  return (*value != nullptr);;
}

struct timer_measurement_t {
  std::string _label;
  hipStream_t _stream;
  bool _enabled;
  
  std::chrono::time_point<std::chrono::high_resolution_clock> _beg, _end;

  timer_measurement_t(const std::string label, const hipStream_t stream, const bool enabled) {
    _label = label;
    _stream = stream;
    _enabled = enabled;

    if (_enabled) {
      if (hipSuccess == hipStreamSynchronize(_stream)) {             
        _beg = std::chrono::high_resolution_clock::now();
      } else {
        std::cerr << "Error: failed to hipStreamSynchronize, timer_measurement_t\n";
      }
    }
  }
  ~timer_measurement_t() {
    if (_enabled) {
      if (hipSuccess == hipStreamSynchronize(_stream)) {
        _end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(_end - _beg);
        std::cout << "-- " << _label << " = " << (duration.count()/1000.0) << " seconds" << "\n";
      } else {
        std::cerr << "Error: failed to hipStreamSynchronize, ~timer_measurement_t\n";
      }
    }
  }
};


template<typename T>
struct arith_traits_t;

template<> struct arith_traits_t<float> {
  using value_type = float;
  using magnitude_type = float;
  using cuda_value_type = float;
  static constexpr hipDataType cuda_data_type = HIP_R_32F;
  static constexpr bool is_complex = false;
  static constexpr float epsilon = FLT_EPSILON;
};
template<> struct arith_traits_t<double> {
  using value_type = double;
  using magnitude_type = double;
  using cuda_value_type = double;
  static constexpr hipDataType cuda_data_type = HIP_R_64F;
  static constexpr bool is_complex = false;
  static constexpr double epsilon = DBL_EPSILON;    
};
template<> struct arith_traits_t<std::complex<float>> {
  using value_type = std::complex<float>;
  using magnitude_type = float;
  using cuda_value_type = hipComplex;
  static constexpr hipDataType cuda_data_type = HIP_C_32F;  
  static constexpr bool is_complex = true;
  static constexpr float epsilon = FLT_EPSILON;  
};
template<> struct arith_traits_t<std::complex<double>> {
  using value_type = std::complex<double>;
  using magnitude_type = double;
  using cuda_value_type = hipDoubleComplex;
  static constexpr hipDataType cuda_data_type = HIP_C_64F;    
  static constexpr bool is_complex = true;
  static constexpr double epsilon = DBL_EPSILON;  
};

template<typename T>
inline typename std::enable_if<!arith_traits_t<T>::is_complex, T>::type
conjugate(const T &val) {
  return val;
}

template<typename T>
inline typename std::enable_if<arith_traits_t<T>::is_complex, T>::type
conjugate(const T &val) {
  return std::conj(val);
}

template<typename T>
inline typename std::enable_if<!arith_traits_t<T>::is_complex, void>::type
randomize_vector(const ordinal_type m,
                 std::vector<T> &x) {
  std::mt19937 gen(0 /* rd */); /// for reproduceable test, fix the seed
  std::uniform_real_distribution<double> dist(-1.0, 1.0);
  std::generate(x.begin(), x.end(), [&]() { return T(dist(gen)); });  
}

template<typename T>
inline typename std::enable_if<arith_traits_t<T>::is_complex, void>::type
randomize_vector(const ordinal_type m,
                 std::vector<T> &x) {
  std::random_device rd;
  std::mt19937 gen(rd());
  std::uniform_real_distribution<double> dist(-1.0, 1.0);
  std::generate(x.begin(), x.end(), [&]() { return T(dist(gen), dist(gen)); });  
}

template<typename value_type>
double compute_norm(std::vector<value_type> &x) {
  double sum(0);
  for (auto &val : x) {
    sum += std::real(val*conjugate(val));
  }
  return std::sqrt(sum);
}

template<typename value_type>
void compute_b_is_Ax(const ordinal_type m, const ordinal_type n, 
                     std::vector<ordinal_type> &ap,
                     std::vector<ordinal_type> &aj,
                     std::vector<value_type> &ax,
                     std::vector<value_type> &x,
                     std::vector<value_type> &b) {
  /// error check
  assert(ap.size() == (m+1));
  assert(aj.size() == ap[m]);
  assert(ax.size() == ap[m]);
  assert(x.size() == m);
  assert(b.size() == m);

  /// b = Ax
  for (ordinal_type i=0;i<m;++i) {
    const ordinal_type kbeg = ap[i], kend = ap[i+1];
    value_type tmp(0);
    for (ordinal_type k=kbeg;k<kend;++k) {
      const value_type aa = ax[k];
      const value_type xx = x[aj[k]];
      tmp += aa*xx;
    }
    b[i] = tmp;
  }
}

template<typename value_type>
int compute_r_is_Ax_minus_b(const ordinal_type m, const ordinal_type n, 
                            std::vector<ordinal_type> &ap,
                            std::vector<ordinal_type> &aj,
                            std::vector<value_type> &ax,
                            std::vector<value_type> &x,
                            std::vector<value_type> &b,
                            std::vector<value_type> &r) {
  /// error check
  assert(r.size() == m);

  /// r = Ax
  compute_b_is_Ax(m, n,
                  ap, aj, ax,
                  x,
                  r);

  /// r = r - b
  std::transform(r.begin(), r.end(), b.begin(),
                 r.begin(), std::minus<value_type>());
  
  return 0;
}

template<typename value_type>
void perturb_diag_A(const ordinal_type m, const ordinal_type n, 
                    std::vector<ordinal_type> &ap,
                    std::vector<ordinal_type> &aj,
                    std::vector<value_type> &ax,
                    std::vector<value_type> &x) {
  /// error check
  assert(ap.size() == (m+1));
  assert(aj.size() == ap[m]);
  assert(ax.size() == ap[m]);
  assert(x.size() == m);

  /// diag(A) += x
  for (ordinal_type i=0;i<m;++i) {
    const ordinal_type kbeg = ap[i], kend = ap[i+1];
    value_type tmp(0);
    for (ordinal_type k=kbeg;k<kend;++k) {
      const ordinal_type j = aj[k];
      if (i == j) {
        ax[k] += x[i];
      }
    }
  }
}



template<typename value_type>
struct coo_t {
  ordinal_type _i, _j;
  value_type _x;
  coo_t() = default;
  coo_t(const coo_t &b) = default;
  coo_t(const ordinal_type i, const ordinal_type j, const value_type x)
    : _i(i), _j(j), _x(x) {}

  /// compare less, equality for indices only
  bool operator<(const coo_t &y) const {
    const auto r_val = (_i - y._i);
    return (r_val == 0 ? _j < y._j : r_val < 0);
  }
  bool operator==(const coo_t &y) const {
    return (_i == y._i) && (_j == y._j);
  }    
  bool operator!=(const coo_t &y) const {
    return !(*this == y);
  } 
};


template<typename T>
inline typename std::enable_if<!arith_traits_t<T>::is_complex>::type
read_value_from_file(std::ifstream &file, ordinal_type &i, ordinal_type &j, T &x) {
  file >> i >> j >> x;
}

template<typename T>
inline typename std::enable_if<arith_traits_t<T>::is_complex>::type
read_value_from_file(std::ifstream &file, ordinal_type &i, ordinal_type &j, T &x) {
  typename T::value_type a, b;
  file >> i >> j >> a >> b;
  x = T(a,b);
}

template<typename value_type>
int coo_to_csr(const ordinal_type m,
               const ordinal_type nnz,
               std::vector<coo_t<value_type>> &mm,
               std::vector<ordinal_type> &ap,
               std::vector<ordinal_type> &aj,
               std::vector<value_type> &ax,
               bool useZeroBasedIndexing = true) {
  ap.resize(m+1);
  aj.resize(nnz);
  ax.resize(nnz);

  using ijx_type = coo_t<value_type>;

  // Adjust indexing depending on zero-based or one-based indexing.
  int offset = useZeroBasedIndexing ? 0 : 1;

  ordinal_type icnt = 0;
  ordinal_type jcnt = 0;
  ijx_type prev = mm[0];
  
  ap[icnt++] = offset;
  aj[jcnt] = prev._j;
  ax[jcnt++] = prev._x;
  
  for (auto it = (mm.begin() + 1); it < (mm.end()); ++it) {
    const ijx_type aij = (*it);
    
    if (aij._i != prev._i)
      ap[icnt++] = jcnt + offset;
    
    if (aij == prev) {
      aj[jcnt-1] = aij._j;
      ax[jcnt-1] += aij._x;
    } else {
      aj[jcnt] = aij._j;
      ax[jcnt++] = aij._x;
    }
    prev = aij;
  }
  ap[icnt++] = jcnt + offset;

  return 0;
}

template<typename value_type>
int csr_to_coo(const ordinal_type m,
               const ordinal_type nnz,
               std::vector<ordinal_type> &ap,
               std::vector<ordinal_type> &aj,
               std::vector<value_type> &ax,
               std::vector<coo_t<value_type>> &mm) {
  mm.resize(nnz);

  // Adjust indexing depending on zero-based or one-based indexing.
  int offset = 0;
  if (ap.size() > 0) {
    offset = (ap[0] == 0) ? 0 : 1;
  }

  using ijx_type = coo_t<value_type>;  
  for (ordinal_type i=0,cnt=0;i<m;++i) {
    const ordinal_type kbeg = ap[i], kend = ap[i+1];
    for (ordinal_type k=kbeg;k<kend;++k) {
      const ordinal_type j = aj[k-offset]-offset;
      const value_type x = ax[k-offset];
      mm[cnt++] = ijx_type(i + offset, j + offset, x);
    }
  }
  
  return 0;
}

template<typename value_type>
void show_csr(const std::string label,
              const ordinal_type m,
              const ordinal_type n,
              const std::vector<ordinal_type> &ap,
              const std::vector<ordinal_type> &aj,
              const std::vector<value_type> &ax) {
  std::cout << "-- sparse matrix: " << label << " [" << m << " x " << n << "]\n";

  std::cout << "   ap = [ ";
  for (auto &p : ap) {
    std::cout << p << " ";
  }
  std::cout << "]\n";  

  std::cout << "   aj = [ ";
  for (auto &j : aj) {
    std::cout << j << " ";
  }
  std::cout << "]\n";
  
  std::cout << "   ax = [ ";
  for (auto &x : ax) {
    std::cout << x << " ";
  }
  std::cout << "]\n";
}

template<typename value_type>
void show_vector(const std::string label,
                 const ordinal_type m,
                 const std::vector<value_type> &x) {
  std::cout << "-- vector: " << label << " [" << m << "]\n";
  for (ordinal_type i=0;i<m;++i) {
    std::cout << "   " << x[i] << "\n";
  }
}

template<typename value_type>
int read_matrixmarket(std::string filename,
                      ordinal_type &m,
                      ordinal_type &n,
                      std::vector<ordinal_type> &ap,
                      std::vector<ordinal_type> &aj,
                      std::vector<value_type> &ax,
                      const int verbose) {
  std::ifstream file;
  file.open(filename);

  if (file.fail()) {
    throw std::runtime_error("File could not be opened!");
  }
  
  // reading mm header
  ordinal_type nnz;
  bool symmetry = false, hermitian = false;
  {
    std::string header;
    std::getline(file, header);
    while (file.good()) {
      char c = file.peek();
      if (c == '%' || c == '\n') {
        file.ignore(256, '\n');
        continue;
      }
      break;
    }
    std::transform(header.begin(), header.end(), header.begin(), ::tolower);
    symmetry = (header.find("symmetric") != std::string::npos || header.find("hermitian") != std::string::npos);
    hermitian = (header.find("hermitian") != std::string::npos);

    file >> m >> n >> nnz;
  }
  if (m == 0 || n == 0 || nnz == 0) {
    throw std::runtime_error("Matrix must not be empty!");
  }

  if (verbose) {
    std::cout << "-- read matrix market\n";
    std::cout << (symmetry ? "symmetric" :"general") << " " << (hermitian ? "hermitian" : "") << "\n";
    std::cout << m << " " << n << " " << nnz << "\n";  
  }
  
  // read data into coo format  
  using ijx_type = coo_t<value_type>;
  constexpr ordinal_type mm_base = 1;  
  std::vector<ijx_type> mm;
  mm.reserve(nnz * (symmetry ? 2 : 1));
  for (ordinal_type i = 0; i < nnz; ++i) {
    ordinal_type row(0), col(0);
    value_type val;
    
    read_value_from_file(file, row, col, val);
    
    row -= mm_base;
    col -= mm_base;
    
    mm.push_back(ijx_type(row, col, val));
    if (symmetry && row != col) {
      const value_type conj_val = conjugate(val);
      mm.push_back(ijx_type(col, row, hermitian ? conj_val : val));
    }
  }
  std::sort(mm.begin(), mm.end(), std::less<ijx_type>());
  nnz = mm.size();

  if (verbose) {
    for (auto &ijx : mm) 
      std::cout << "   " << ijx._i << " " << ijx._j << " " << ijx._x << "\n"; 
  }
  coo_to_csr(m, nnz, mm, ap, aj, ax);

  return 0;
}


// CUDA API error checking
#define CUDA_CHECK(err)                                             \
  do {                                                              \
    hipError_t err_ = (err);                                       \
    if (err_ != hipSuccess) {                                      \
      printf("CUDA error %d at %s:%d\n", err_, __FILE__, __LINE__); \
      throw std::runtime_error("CUDA error");                       \
    }                                                               \
  } while (0)

// cusolver API error checking
#define CUSOLVER_CHECK(err)                                             \
  do {                                                                  \
    hipsolverStatus_t err_ = (err);                                      \
    if (err_ != HIPSOLVER_STATUS_SUCCESS) {                              \
      printf("cusolver error %d at %s:%d\n", err_, __FILE__, __LINE__); \
      throw std::runtime_error("cusolver error");                       \
    }                                                                   \
  } while (0)

// cusparse API error checking
#define CUSPARSE_CHECK(err)                                             \
  do {                                                                  \
    hipsparseStatus_t err_ = (err);                                      \
    if (err_ != HIPSPARSE_STATUS_SUCCESS) {                              \
      printf("cusparse error %d at %s:%d\n", err_, __FILE__, __LINE__); \
      throw std::runtime_error("cusparse error");                       \
    }                                                                   \
  } while (0)

// cudss API error checking
#define CUDSS_CHECK(err)                                                \
  do {                                                                  \
    cudssStatus_t err_ = (err);                                         \
    if (err_ != CUDSS_STATUS_SUCCESS) {                                 \
      printf("cudss error %d at %s:%d\n", err_, __FILE__, __LINE__);    \
      throw std::runtime_error("cudss error");                          \
    }                                                                   \
  } while (0)

// cublas API error checking
#define CUBLAS_CHECK(err)                                                                          \
    do {                                                                                           \
        hipblasStatus_t err_ = (err);                                                               \
        if (err_ != HIPBLAS_STATUS_SUCCESS) {                                                       \
            printf("cublas error %d at %s:%d\n", err_, __FILE__, __LINE__);                        \
            throw std::runtime_error("cublas error");                                              \
        }                                                                                          \
    } while (0)

///
/// Unified X interface to cusolver APIs
///

hipsolverStatus_t cusolverSpXcsrcholBufferInfo(hipsolverSpHandle_t handle,
                                              int n,
                                              int nnzA,
                                              const hipsparseMatDescr_t descrA,
                                              const float *csrValA,
                                              const int *csrRowPtrA,
                                              const int *csrColIndA,
                                              csrcholInfo_t info,
                                              size_t *internalDataInBytes,
                                              size_t *workspaceInBytes) {
  return cusolverSpScsrcholBufferInfo(handle, n, nnzA, descrA, csrValA, csrRowPtrA, csrColIndA, info, internalDataInBytes, workspaceInBytes);
}
hipsolverStatus_t cusolverSpXcsrcholBufferInfo(hipsolverSpHandle_t handle,
                                              int n,
                                              int nnzA,
                                              const hipsparseMatDescr_t descrA,
                                              const double *csrValA,
                                              const int *csrRowPtrA,
                                              const int *csrColIndA,
                                              csrcholInfo_t info,
                                              size_t *internalDataInBytes,
                                              size_t *workspaceInBytes) {
  return cusolverSpDcsrcholBufferInfo(handle, n, nnzA, descrA, csrValA, csrRowPtrA, csrColIndA, info, internalDataInBytes, workspaceInBytes);
}

hipsolverStatus_t cusolverSpXcsrcholBufferInfo(hipsolverSpHandle_t handle,
                                              int n,
                                              int nnzA,
                                              const hipsparseMatDescr_t descrA,
                                              const hipComplex *csrValA,
                                              const int *csrRowPtrA,
                                              const int *csrColIndA,
                                              csrcholInfo_t info,
                                              size_t *internalDataInBytes,
                                              size_t *workspaceInBytes) {
  return cusolverSpCcsrcholBufferInfo(handle, n, nnzA, descrA, csrValA, csrRowPtrA, csrColIndA, info, internalDataInBytes, workspaceInBytes);
}
hipsolverStatus_t cusolverSpXcsrcholBufferInfo(hipsolverSpHandle_t handle,
                                              int n,
                                              int nnzA,
                                              const hipsparseMatDescr_t descrA,
                                              const hipDoubleComplex *csrValA,
                                              const int *csrRowPtrA,
                                              const int *csrColIndA,
                                              csrcholInfo_t info,
                                              size_t *internalDataInBytes,
                                              size_t *workspaceInBytes) {
  return cusolverSpZcsrcholBufferInfo(handle, n, nnzA, descrA, csrValA, csrRowPtrA, csrColIndA, info, internalDataInBytes, workspaceInBytes);
}


hipsolverStatus_t cusolverSpXcsrcholFactor(hipsolverSpHandle_t handle,
                                          int n,
                                          int nnzA,
                                          const hipsparseMatDescr_t descrA,
                                          const float *csrValA,
                                          const int *csrRowPtrA,
                                          const int *csrColIndA,
                                          csrcholInfo_t info,
                                          void *pBuffer) {
  return cusolverSpScsrcholFactor(handle, n, nnzA, descrA, csrValA, csrRowPtrA, csrColIndA, info, pBuffer);
}

hipsolverStatus_t cusolverSpXcsrcholFactor(hipsolverSpHandle_t handle,
                                          int n,
                                          int nnzA,
                                          const hipsparseMatDescr_t descrA,
                                          const double *csrValA,
                                          const int *csrRowPtrA,
                                          const int *csrColIndA,
                                          csrcholInfo_t info,
                                          void *pBuffer) {
  return cusolverSpDcsrcholFactor(handle, n, nnzA, descrA, csrValA, csrRowPtrA, csrColIndA, info, pBuffer);
}
hipsolverStatus_t cusolverSpXcsrcholFactor(hipsolverSpHandle_t handle,
                                          int n,
                                          int nnzA,
                                          const hipsparseMatDescr_t descrA,
                                          const hipComplex *csrValA,
                                          const int *csrRowPtrA,
                                          const int *csrColIndA,
                                          csrcholInfo_t info,
                                          void *pBuffer) {
  return cusolverSpCcsrcholFactor(handle, n, nnzA, descrA, csrValA, csrRowPtrA, csrColIndA, info, pBuffer);
}
hipsolverStatus_t cusolverSpXcsrcholFactor(hipsolverSpHandle_t handle,
                                          int n,
                                          int nnzA,
                                          const hipsparseMatDescr_t descrA,
                                          const hipDoubleComplex *csrValA,
                                          const int *csrRowPtrA,
                                          const int *csrColIndA,
                                          csrcholInfo_t info,
                                          void *pBuffer) {
  return cusolverSpZcsrcholFactor(handle, n, nnzA, descrA, csrValA, csrRowPtrA, csrColIndA, info, pBuffer);
}


hipsolverStatus_t cusolverSpXcsrcholSolve(hipsolverSpHandle_t handle,
                                         int n,
                                         const float *b,
                                         float *x,
                                         csrcholInfo_t info,
                                         void *pBuffer) {
  return cusolverSpScsrcholSolve(handle, n, b, x, info, pBuffer);
}
hipsolverStatus_t cusolverSpXcsrcholSolve(hipsolverSpHandle_t handle,
                                         int n,
                                         const double *b,
                                         double *x,
                                         csrcholInfo_t info,
                                         void *pBuffer) {
  return cusolverSpDcsrcholSolve(handle, n, b, x, info, pBuffer);
}
hipsolverStatus_t cusolverSpXcsrcholSolve(hipsolverSpHandle_t handle,
                                         int n,
                                         const hipComplex *b,
                                         hipComplex *x,
                                         csrcholInfo_t info,
                                         void *pBuffer) {
  return cusolverSpCcsrcholSolve(handle, n, b, x, info, pBuffer);
}
hipsolverStatus_t cusolverSpXcsrcholSolve(hipsolverSpHandle_t handle,
                                         int n,
                                         const hipDoubleComplex *b,
                                         hipDoubleComplex *x,
                                         csrcholInfo_t info,
                                         void *pBuffer) {
  return cusolverSpZcsrcholSolve(handle, n, b, x, info, pBuffer);
}

hipsolverStatus_t cusolverSpXcsrlsvchol(hipsolverSpHandle_t handle,
                                       int m,
                                       int nnz,
                                       const hipsparseMatDescr_t descrA,
                                       const float *csrVal,
                                       const int *csrRowPtr,
                                       const int *csrColInd,
                                       const float *b,
                                       float tol,
                                       int reorder,
                                       float *x,
                                       int *singularity) {
  return hipsolverSpScsrlsvchol(handle, m, nnz, descrA, csrVal, csrRowPtr, csrColInd, b, tol, reorder, x, singularity);
}

hipsolverStatus_t cusolverSpXcsrlsvchol(hipsolverSpHandle_t handle,
                                       int m,
                                       int nnz,
                                       const hipsparseMatDescr_t descrA,
                                       const double *csrVal,
                                       const int *csrRowPtr,
                                       const int *csrColInd,
                                       const double *b,
                                       double tol,
                                       int reorder,
                                       double *x,
                                       int *singularity) {
  return hipsolverSpDcsrlsvchol(handle, m, nnz, descrA, csrVal, csrRowPtr, csrColInd, b, tol, reorder, x, singularity);
}

hipsolverStatus_t cusolverSpXcsrlsvchol(hipsolverSpHandle_t handle,
                                       int m,
                                       int nnz,
                                       const hipsparseMatDescr_t descrA,
                                       const hipComplex *csrVal,
                                       const int *csrRowPtr,
                                       const int *csrColInd,
                                       const hipComplex *b,
                                       float tol,
                                       int reorder,
                                       hipComplex *x,
                                       int *singularity) {
  return cusolverSpCcsrlsvchol(handle, m, nnz, descrA, csrVal, csrRowPtr, csrColInd, b, tol, reorder, x, singularity);
}  

hipsolverStatus_t cusolverSpXcsrlsvchol(hipsolverSpHandle_t handle,
                                       int m,
                                       int nnz,
                                       const hipsparseMatDescr_t descrA,
                                       const hipDoubleComplex *csrVal,
                                       const int *csrRowPtr,
                                       const int *csrColInd,
                                       const hipDoubleComplex *b,
                                       double tol,
                                       int reorder,
                                       hipDoubleComplex *x,
                                       int *singularity) {
  return cusolverSpZcsrlsvchol(handle, m, nnz, descrA, csrVal, csrRowPtr, csrColInd, b, tol, reorder, x, singularity); 
}

hipsolverStatus_t cusolverSpXcsrlsvluHost(hipsolverSpHandle_t handle,
                                         int n,
                                         int nnzA,
                                         const hipsparseMatDescr_t descrA,
                                         const float * csrValA,
                                         const int * csrRowPtrA,
                                         const int * csrColIndA,
                                         const float * b,
                                         float tol,
                                         int reorder,
                                         float * x,
                                         int * singularity) {
  return cusolverSpScsrlsvluHost(handle, n, nnzA, descrA, csrValA, csrRowPtrA, csrColIndA, b, tol, reorder, x, singularity);
}

hipsolverStatus_t cusolverSpXcsrlsvluHost(hipsolverSpHandle_t handle,
                                         int n,
                                         int nnzA,
                                         const hipsparseMatDescr_t descrA,
                                         const double * csrValA,
                                         const int * csrRowPtrA,
                                         const int * csrColIndA,
                                         const double * b,
                                         double tol,
                                         int reorder,
                                         double * x,
                                         int * singularity) {
  return cusolverSpDcsrlsvluHost(handle, n, nnzA, descrA, csrValA, csrRowPtrA, csrColIndA, b, tol, reorder, x, singularity);
}

hipsolverStatus_t cusolverSpXcsrlsvluHost(hipsolverSpHandle_t handle,
                                         int n,
                                         int nnzA,
                                         const hipsparseMatDescr_t descrA,
                                         const hipComplex * csrValA,
                                         const int * csrRowPtrA,
                                         const int * csrColIndA,
                                         const hipComplex * b,
                                         float tol,
                                         int reorder,
                                         hipComplex * x,
                                         int * singularity) {
  return cusolverSpCcsrlsvluHost(handle, n, nnzA, descrA, csrValA, csrRowPtrA, csrColIndA, b, tol, reorder, x, singularity);
}

hipsolverStatus_t cusolverSpXcsrlsvluHost(hipsolverSpHandle_t handle,
                                         int n,
                                         int nnzA,
                                         const hipsparseMatDescr_t descrA,
                                         const hipDoubleComplex * csrValA,
                                         const int * csrRowPtrA,
                                         const int * csrColIndA,
                                         const hipDoubleComplex * b,
                                         double tol,
                                         int reorder,
                                         hipDoubleComplex * x,
                                         int * singularity) {
  return cusolverSpZcsrlsvluHost(handle, n, nnzA, descrA, csrValA, csrRowPtrA, csrColIndA, b, tol, reorder, x, singularity);
}

hipsolverStatus_t cusolverSpXcsrluExtractHost(hipsolverSpHandle_t handle,
                                             int * P,
                                             int * Q,
                                             const hipsparseMatDescr_t descrL,
                                             float * csrValL,
                                             int * csrRowPtrL,
                                             int * csrColIndL,
                                             const hipsparseMatDescr_t descrU,
                                             float * csrValU,
                                             int * csrRowPtrU,
                                             int * csrColIndU,
                                             csrluInfoHost_t info,
                                             void * pBuffer) {
  return cusolverSpScsrluExtractHost(handle, P, Q, descrL, csrValL, csrRowPtrL, csrColIndL, descrU, csrValU, csrRowPtrU, csrColIndU, info, pBuffer);
}

hipsolverStatus_t cusolverSpXcsrluExtractHost(hipsolverSpHandle_t handle,
                                             int * P,
                                             int * Q,
                                             const hipsparseMatDescr_t descrL,
                                             double * csrValL,
                                             int * csrRowPtrL,
                                             int * csrColIndL,
                                             const hipsparseMatDescr_t descrU,
                                             double * csrValU,
                                             int * csrRowPtrU,
                                             int * csrColIndU,
                                             csrluInfoHost_t info,
                                             void * pBuffer) {
  return cusolverSpDcsrluExtractHost(handle, P, Q, descrL, csrValL, csrRowPtrL, csrColIndL, descrU, csrValU, csrRowPtrU, csrColIndU, info, pBuffer);
}

hipsolverStatus_t cusolverSpXcsrluExtractHost(hipsolverSpHandle_t handle,
                                             int * P,
                                             int * Q,
                                             const hipsparseMatDescr_t descrL,
                                             hipComplex * csrValL,
                                             int * csrRowPtrL,
                                             int * csrColIndL,
                                             const hipsparseMatDescr_t descrU,
                                             hipComplex * csrValU,
                                             int * csrRowPtrU,
                                             int * csrColIndU,
                                             csrluInfoHost_t info,
                                             void * pBuffer) {
  return cusolverSpCcsrluExtractHost(handle, P, Q, descrL, csrValL, csrRowPtrL, csrColIndL, descrU, csrValU, csrRowPtrU, csrColIndU, info, pBuffer);
}

hipsolverStatus_t cusolverSpXcsrluExtractHost(hipsolverSpHandle_t handle,
                                             int * P,
                                             int * Q,
                                             const hipsparseMatDescr_t descrL,
                                             hipDoubleComplex * csrValL,
                                             int * csrRowPtrL,
                                             int * csrColIndL,
                                             const hipsparseMatDescr_t descrU,
                                             hipDoubleComplex * csrValU,
                                             int * csrRowPtrU,
                                             int * csrColIndU,
                                             csrluInfoHost_t info,
                                             void * pBuffer) {
  return cusolverSpZcsrluExtractHost(handle, P, Q, descrL, csrValL, csrRowPtrL, csrColIndL, descrU, csrValU, csrRowPtrU, csrColIndU, info, pBuffer);
}

hipsolverStatus_t cusolverSpXcsrluBufferInfoHost(hipsolverSpHandle_t handle,
                                                int n,
                                                int nnzA,
                                                const hipsparseMatDescr_t descrA,
                                                const float * csrValA,
                                                const int * csrRowPtrA,
                                                const int * csrColIndA,
                                                csrluInfoHost_t info,
                                                size_t * internalDataInBytes,
                                                size_t * bufferSizeInBytes) {
  return cusolverSpScsrluBufferInfoHost(handle, n, nnzA, descrA, csrValA, csrRowPtrA, csrColIndA, info, internalDataInBytes, bufferSizeInBytes);
}

hipsolverStatus_t cusolverSpXcsrluBufferInfoHost(hipsolverSpHandle_t handle,
                                                int n,
                                                int nnzA,
                                                const hipsparseMatDescr_t descrA,
                                                const double * csrValA,
                                                const int * csrRowPtrA,
                                                const int * csrColIndA,
                                                csrluInfoHost_t info,
                                                size_t * internalDataInBytes,
                                                size_t * bufferSizeInBytes) {
  return cusolverSpDcsrluBufferInfoHost(handle, n, nnzA, descrA, csrValA, csrRowPtrA, csrColIndA, info, internalDataInBytes, bufferSizeInBytes);
}

hipsolverStatus_t cusolverSpXcsrluBufferInfoHost(hipsolverSpHandle_t handle,
                                                int n,
                                                int nnzA,
                                                const hipsparseMatDescr_t descrA,
                                                const hipComplex * csrValA,
                                                const int * csrRowPtrA,
                                                const int * csrColIndA,
                                                csrluInfoHost_t info,
                                                size_t * internalDataInBytes,
                                                size_t * bufferSizeInBytes) {
  return cusolverSpCcsrluBufferInfoHost(handle, n, nnzA, descrA, csrValA, csrRowPtrA, csrColIndA, info, internalDataInBytes, bufferSizeInBytes);
}

hipsolverStatus_t cusolverSpXcsrluBufferInfoHost(hipsolverSpHandle_t handle,
                                                int n,
                                                int nnzA,
                                                const hipsparseMatDescr_t descrA,
                                                const hipDoubleComplex * csrValA,
                                                const int * csrRowPtrA,
                                                const int * csrColIndA,
                                                csrluInfoHost_t info,
                                                size_t * internalDataInBytes,
                                                size_t * bufferSizeInBytes) {
  return cusolverSpZcsrluBufferInfoHost(handle, n, nnzA, descrA, csrValA, csrRowPtrA, csrColIndA, info, internalDataInBytes, bufferSizeInBytes);
}

hipsolverStatus_t cusolverSpXcsrluFactorHost(hipsolverSpHandle_t handle,
                                            int n,
                                            int nnzA,
                                            const hipsparseMatDescr_t descrA,
                                            const float * csrValA,
                                            const int * csrRowPtrA,
                                            const int * csrColIndA,
                                            csrluInfoHost_t info,
                                            float pivot_threshold,
                                            void * pBuffer) {
  return cusolverSpScsrluFactorHost(handle, n, nnzA, descrA, csrValA, csrRowPtrA, csrColIndA, info, pivot_threshold, pBuffer);
}

hipsolverStatus_t cusolverSpXcsrluFactorHost(hipsolverSpHandle_t handle,
                                            int n,
                                            int nnzA,
                                            const hipsparseMatDescr_t descrA,
                                            const double * csrValA,
                                            const int * csrRowPtrA,
                                            const int * csrColIndA,
                                            csrluInfoHost_t info,
                                            double pivot_threshold,
                                            void * pBuffer) {
  return cusolverSpDcsrluFactorHost(handle, n, nnzA, descrA, csrValA, csrRowPtrA, csrColIndA, info, pivot_threshold, pBuffer);
}

hipsolverStatus_t cusolverSpXcsrluFactorHost(hipsolverSpHandle_t handle,
                                            int n,
                                            int nnzA,
                                            const hipsparseMatDescr_t descrA,
                                            const hipComplex * csrValA,
                                            const int * csrRowPtrA,
                                            const int * csrColIndA,
                                            csrluInfoHost_t info,
                                            float pivot_threshold,
                                            void * pBuffer) {
  return cusolverSpCcsrluFactorHost(handle, n, nnzA, descrA, csrValA, csrRowPtrA, csrColIndA, info, pivot_threshold, pBuffer);
}

hipsolverStatus_t cusolverSpXcsrluFactorHost(hipsolverSpHandle_t handle,
                                            int n,
                                            int nnzA,
                                            const hipsparseMatDescr_t descrA,
                                            const hipDoubleComplex * csrValA,
                                            const int * csrRowPtrA,
                                            const int * csrColIndA,
                                            csrluInfoHost_t info,
                                            double pivot_threshold,
                                            void * pBuffer) {
  return cusolverSpZcsrluFactorHost(handle, n, nnzA, descrA, csrValA, csrRowPtrA, csrColIndA, info, pivot_threshold, pBuffer);
}

hipsolverStatus_t cusolverSpXcsrluSolveHost(hipsolverSpHandle_t handle,
                                           int n,
                                           const float * b,
                                           float * x,
                                           csrluInfoHost_t info,
                                           void * pBuffer) {
  return cusolverSpScsrluSolveHost(handle, n, b, x, info, pBuffer);
}

hipsolverStatus_t cusolverSpXcsrluSolveHost(hipsolverSpHandle_t handle,
                                           int n,
                                           const double * b,
                                           double * x,
                                           csrluInfoHost_t info,
                                           void * pBuffer) {
  return cusolverSpDcsrluSolveHost(handle, n, b, x, info, pBuffer);
}

hipsolverStatus_t cusolverSpXcsrluSolveHost(hipsolverSpHandle_t handle,
                                           int n,
                                           const hipComplex * b,
                                           hipComplex * x,
                                           csrluInfoHost_t info,
                                           void * pBuffer) {
  return cusolverSpCcsrluSolveHost(handle, n, b, x, info, pBuffer);
}

hipsolverStatus_t cusolverSpXcsrluSolveHost(hipsolverSpHandle_t handle,
                                           int n,
                                           const hipDoubleComplex * b,
                                           hipDoubleComplex * x,
                                           csrluInfoHost_t info,
                                           void * pBuffer) {
  return cusolverSpZcsrluSolveHost(handle, n, b, x, info, pBuffer);
}

#endif