/*
 * SPDX-FileCopyrightText: Copyright (c) 2020-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

#include <algorithm>
#include <cassert>
#include <cstdint>
#include <functional>
#include <vector>
#include <array>

#include <hip/hip_runtime.h>
#include <hip/hip_fp16.h>
#include <hip/hip_complex.h>
#include "hiptensor.h"

#define HANDLE_ERROR(x) { const auto err = x;\
    if (err == HIPTENSOR_STATUS_NOT_SUPPORTED) { return false; }\
    if (err != HIPTENSOR_STATUS_SUCCESS) {printf("hiptensor: Error %s in line %d\n", hiptensorGetErrorString(err), __LINE__); return false; } }

template<typename U>
struct CuTensorTypeTraits;

template<>
struct CuTensorTypeTraits<double> {
  static hiptensorDataType_t getDataType() {return HIPTENSOR_R_64F;}
  static const hiptensorComputeDescriptor_t getComputeDesc() {return HIPTENSOR_COMPUTE_DESC_64F;}
  typedef double ScalarType;
};

template<>
struct CuTensorTypeTraits<float> {
  static hiptensorDataType_t getDataType() {return HIPTENSOR_R_32F;}
  static const hiptensorComputeDescriptor_t getComputeDesc() {return HIPTENSOR_COMPUTE_DESC_32F;}
  typedef float ScalarType;
};

template<>
struct CuTensorTypeTraits<hipDoubleComplex> {
  static hiptensorDataType_t getDataType() {return HIPTENSOR_C_64F;}
  static const hiptensorComputeDescriptor_t getComputeDesc() {return HIPTENSOR_COMPUTE_DESC_64F;}
  typedef hipDoubleComplex ScalarType;
};

template<>
struct CuTensorTypeTraits<hipComplex> {
  static hiptensorDataType_t getDataType() {return HIPTENSOR_C_32F;}
  static const hiptensorComputeDescriptor_t getComputeDesc() {return HIPTENSOR_COMPUTE_DESC_32F;}
  typedef hipComplex ScalarType;
};

template<>
struct CuTensorTypeTraits<__half> {
  static hiptensorDataType_t getDataType() {return HIPTENSOR_R_16F;}
  static const hiptensorComputeDescriptor_t getComputeDesc() {return HIPTENSOR_COMPUTE_DESC_16F;}
  typedef float ScalarType;
};


template<typename ComputeType,
         typename IntType, int kMaxNumModes_>
struct Einsum
{
    static const std::vector<IntType> emptyVec;

    Einsum(const std::string &equation,
           const std::vector<IntType> &A_shape,
           const std::vector<IntType> &B_shape = emptyVec,
           const hiptensorOperator_t opA = HIPTENSOR_OP_IDENTITY,
           const hiptensorOperator_t opB = HIPTENSOR_OP_IDENTITY
           ) :
        numModesA_(A_shape.size()),
        numModesB_(B_shape.size()),
        numModesC_(0),
        opA_(opA),
        opB_(opB),
        isInitialized_(false)
    {
        const auto arrow_pos = equation.find("->");
        const auto comma_pos = equation.find(",");
        const auto dots = equation.find("...");
        const bool isBroadcast = (dots != std::string::npos);
        const bool isImplicit = (arrow_pos == std::string::npos);
        if (isBroadcast) // TODO
        {
            return;
        }
        const bool usesB = (comma_pos != std::string::npos);
        if (! usesB)
        {
            numModesB_ = 0;
        }

        size_t a_start = 0;
        size_t a_end = isImplicit ? ((comma_pos == std::string::npos) ? equation.size() : comma_pos) : 
                                    ((comma_pos == std::string::npos) ? arrow_pos : comma_pos);
        size_t b_start = usesB ? comma_pos + 1 : 0;
        size_t b_end   = usesB ? (isImplicit ? equation.size() : arrow_pos) : 0;
        size_t c_start = isImplicit ? equation.size() : arrow_pos + 2;
        size_t c_end = equation.size();


        char modeA[kMaxNumModes_ + 2];
        uint32_t numModesA = 0;
        for (int i = a_start; i < a_end && numModesA < kMaxNumModes_ + 2; ++i){
            if (equation.at(i) != ' ') // skip spaces
            {
                modeA[numModesA++] = equation.at(i);
            }
        }

        char modeB[kMaxNumModes_ + 2];
        uint32_t numModesB = 0;
        for (int i = b_start; i < b_end && numModesB < kMaxNumModes_ + 2; ++i){
            if (equation.at(i) != ' ') // skip spaces
            {
                modeB[numModesB++] = equation.at(i);
            }
        }

        char modeC[kMaxNumModes_ + 2];
        uint32_t numModesC = 0;
        for (int i = c_start; i < c_end && numModesC < kMaxNumModes_ + 2; ++i){
            if (equation.at(i) != ' ') // skip spaces
            {
                modeC[numModesC++] = equation.at(i);
            }
        }

        if ((numModesA != numModesA_) || (numModesB != numModesB_))
        {
            // substring size and shape don't match
            return;
        }
        if (numModesA_ > kMaxNumModes_ || numModesB_ > kMaxNumModes_)
        {
            // too many modes
            return;
        }

        /**
         * Copy all modes from modeA to modeC if they don't appear in modeB
         */
        auto copyModesIf = [](const char* modeA, uint32_t numModesA,
                const char* modeB, uint32_t numModesB,
                char* modeC, uint32_t &numModesC)
        {
            for (uint32_t i = 0; i < numModesA; i++)
            {
                auto mode = modeA[i];
                bool found = false;
                for(uint32_t j=0; j < numModesB; ++j){
                    if(mode == modeB[j])
                    {
                        found = true;
                        break;
                    }
                }

                if (!found) // is non-contracted mode
                {
                    modeC[numModesC++] = mode;
                    if (numModesC > kMaxNumModes_)
                    {
                        // too many modes
                        return false;
                    }
                }
            }
            return true;
        };


        std::array<char, kMaxNumModes_+1> implicitModeC;
        char* redirectModeC;
        if (isImplicit)
        {
            // we have to copy all non-contracted modes from A over to C
            if (copyModesIf(modeA, numModesA_, modeB, numModesB_, implicitModeC.data(), numModesC_) == false)
            {
                return;
            }
            // we have to copy all non-contracted modes from B over to C
            if (copyModesIf(modeB, numModesB_, modeA, numModesA_, implicitModeC.data(), numModesC_) == false)
            {
                return;
            }
            std::sort(implicitModeC.begin(), std::next(implicitModeC.begin(), numModesC_)); // modes are sorted w.r.t. lexical order
            implicitModeC[numModesC_] = '\0';
            redirectModeC = implicitModeC.data();
        }
        else
        {
            redirectModeC = modeC;
            numModesC_ = numModesC;
        }

        for (uint32_t i = 0; i < numModesA_; i++)
        {
            modesA_[i] = modeA[numModesA_ - i - 1];
            extentA_[i] = A_shape[numModesA_ - i - 1];
        }

        for (uint32_t i = 0; i < numModesB_; i++)
        {
            modesB_[i] = modeB[numModesB_ - i - 1];
            extentB_[i] = B_shape[numModesB_ - i - 1];
        }

        for (uint32_t i = 0; i < numModesC_; i++)
        {
            const auto mode = redirectModeC[numModesC_ - i - 1];
            modesC_[i] = mode;
            bool found = false;
            for (uint32_t j=0; j < numModesA_; ++j)
            {
                if (modesA_[j] == mode)
                {
                    extentC_[i] = extentA_[j];
                    found = true;
                    break;
                }
            }
            for (uint32_t j=0; !found && j < numModesB_; ++j)
            {
                if (modesB_[j] == mode)
                {
                    extentC_[i] = extentB_[j];
                    break;
                }
            }
        }

        isInitialized_ = true;
    }

    uint64_t getWorksize()  
    {
        if (!workspaceSet_)
        {
            std::cerr << "hiptensor: Error, workspace size has not been determined, create plan first";
        }
        return kWorksize_; 
    }

    std::vector<IntType> getOutputShape() const
    {
        if (!isInitialized_) return {};
        std::vector<IntType> extentC(numModesC_);
        for (int i=0; i < numModesC_; ++i)
        {
            extentC[i] = extentC_.at(numModesC_ - i - 1);
        }

        return extentC;
    }

    /**
     * create the contraction plan according to the workspace size provided
     *
     * \param[in] handle cuTensor handle
     * \param[in] workspaceSizeProvided size of the workspace provided by the user
     */
    bool plan(const hiptensorHandle_t handle, hiptensorWorksizePreference_t worksizePref, bool jit_pref)
    {
        if (!isInitialized_) return false;

        hiptensorDataType_t cutensorType = CuTensorTypeTraits<ComputeType>::getDataType();
        const hiptensorComputeDescriptor_t descCompute = CuTensorTypeTraits<ComputeType>::getComputeDesc();

        const uint32_t kAlignment = 128;
        hiptensorTensorDescriptor_t descA;
        HANDLE_ERROR(hiptensorCreateTensorDescriptor(handle,
                    &descA,
                    numModesA_,
                    extentA_.data(),
                    NULL,/*stride*/
                    cutensorType, kAlignment));

        hiptensorTensorDescriptor_t descC;
        HANDLE_ERROR(hiptensorCreateTensorDescriptor(handle,
                    &descC,
                    numModesC_,
                    extentC_.data(),
                    NULL,/*stride*/
                    cutensorType, kAlignment));

        hiptensorOperationDescriptor_t desc;
        hiptensorTensorDescriptor_t descB = nullptr;

        if (numModesB_ > 0)
        {
            // dispatch to contraction

            HANDLE_ERROR(hiptensorCreateTensorDescriptor(handle,
                    &descB,
                    numModesB_,
                    extentB_.data(),
                    NULL,/*stride*/
                    cutensorType, kAlignment));

            /*******************************
             * Create Contraction Descriptor
             *******************************/

            HANDLE_ERROR(hiptensorCreateContraction(handle, 
                        &desc,
                        descA, modesA_.data(), /* unary operator A*/opA_,
                        descB, modesB_.data(), /* unary operator B*/opB_,
                        descC, modesC_.data(), /* unary operator C*/HIPTENSOR_OP_IDENTITY,
                        descC, modesC_.data(),
                        descCompute));
        }
        else
        {
            /*******************************
             * Create Contraction Descriptor
             *******************************/
            HANDLE_ERROR(hiptensorCreateReduction(
                 handle, &desc,
                 descA, modesA_.data(), HIPTENSOR_OP_IDENTITY,
                 descC, modesC_.data(), HIPTENSOR_OP_IDENTITY,
                 descC, modesC_.data(),
                 HIPTENSOR_OP_ADD, descCompute));
        }

        /**************************
         * Set the algorithm to use
         ***************************/
        hiptensorPlanPreference_t planPref;
        
        if (jit_pref==true) {
        HANDLE_ERROR(hiptensorCreatePlanPreference(
                    handle,
                    &planPref,
                    HIPTENSOR_ALGO_DEFAULT,
                    HIPTENSOR_JIT_MODE_DEFAULT));
                    
        } 
        else 
        {
        HANDLE_ERROR(hiptensorCreatePlanPreference(
                    handle,
                    &planPref,
                    HIPTENSOR_ALGO_DEFAULT,
                    HIPTENSOR_JIT_MODE_NONE));

        }
        /**********************
         * Query workspace estimate
         **********************/
        uint64_t workspaceSizeEstimate = 0;
        const hiptensorWorksizePreference_t workspacePref = worksizePref;
        HANDLE_ERROR(hiptensorEstimateWorkspaceSize(handle,
                                                  desc,
                                                  planPref,
                                                  workspacePref,
                                                  &workspaceSizeEstimate));

        /**************************
         * Create Contraction Plan
         **************************/
        HANDLE_ERROR(hiptensorCreatePlan(handle,
                    &plan_,
                    desc,
                    planPref,
                    workspaceSizeEstimate));

        uint64_t actualWorkspaceSize = 0;
        HANDLE_ERROR(hiptensorPlanGetAttribute(handle,
                                             plan_,
                                             HIPTENSOR_PLAN_REQUIRED_WORKSPACE,
                                             &actualWorkspaceSize,
                                             sizeof(actualWorkspaceSize)));


        //set workspace to actually used workspace size
        workspaceSet_ = true;
        kWorksize_ = actualWorkspaceSize;

        HANDLE_ERROR(hiptensorDestroyOperationDescriptor(desc));
        HANDLE_ERROR(hiptensorDestroyTensorDescriptor(descA));
        HANDLE_ERROR(hiptensorDestroyTensorDescriptor(descB));
        HANDLE_ERROR(hiptensorDestroyTensorDescriptor(descC));
        return true;
    }


    /**
     * Computes the einsum call A,B->C
     *
     * \param[in] A_raw device pointer of A
     * \param[in] B_raw device pointer of B
     * \param[out] C_raw device pointer of C
     * \param[out] wor_raw device pointer to the scratchpad memory
     * Dispatch to contraction
     */
    bool execute(const hiptensorHandle_t handle,
                 const void* A_raw,
                 const void* B_raw,
                 void* C_raw,
                 void *work_raw, hipStream_t stream) const
    {
        const uint32_t kAlignment = 128; // Alignment of the global-memory device pointers (bytes)
        assert(uintptr_t(A_raw) % kAlignment == 0);
        assert(uintptr_t(B_raw) % kAlignment == 0);
        assert(uintptr_t(C_raw) % kAlignment == 0);

        typename CuTensorTypeTraits<ComputeType>::ScalarType alpha = 1;
        typename CuTensorTypeTraits<ComputeType>::ScalarType beta = 0;

        if (numModesB_ > 0)
        {
            HANDLE_ERROR(hiptensorContract(handle,
                               plan_,
                               (void*) &alpha, A_raw, B_raw,
                               (void*) &beta,  C_raw, C_raw, 
                               work_raw, kWorksize_, stream));
        }
        else
        {
            // dispatch to reduction
            HANDLE_ERROR(hiptensorReduce(handle, plan_,
                    (const void*)&alpha, A_raw,
                    (const void*)&beta,  C_raw, 
                    C_raw, work_raw, kWorksize_, stream));
        }
        return true;
    }

    bool isInitialized() const { return isInitialized_; }

    ~Einsum()
    {
        if (isInitialized_)
        {
            hiptensorDestroyPlan(plan_);
        }
    }

    private:
    bool workspaceSet_ = false;
    uint64_t kWorksize_ = 0;
    hiptensorPlan_t plan_;
    uint32_t numModesA_;
    uint32_t numModesB_;
    uint32_t numModesC_;
    bool isInitialized_;
    std::array<int, kMaxNumModes_> modesA_;
    std::array<int, kMaxNumModes_> modesB_;
    std::array<int, kMaxNumModes_> modesC_;
    std::array<int64_t, kMaxNumModes_> extentA_;
    std::array<int64_t, kMaxNumModes_> extentB_;
    std::array<int64_t, kMaxNumModes_> extentC_;
    hiptensorOperator_t opA_ = HIPTENSOR_OP_IDENTITY;
    hiptensorOperator_t opB_ = HIPTENSOR_OP_IDENTITY;
};

class CutensorLib
{
public:
    CutensorLib()
    {
        hiptensorCreate(&handle);
    }
    ~CutensorLib()
    {
        hiptensorDestroy(handle);
    }

    static hiptensorHandle_t getCutensorHandle()
    {
        static CutensorLib lib;
        return lib.getHandle();
    }

    hiptensorHandle_t getHandle() const { return handle; }

    CutensorLib(CutensorLib const&) = delete;
    void operator=(CutensorLib const&) = delete;

private:
    hiptensorHandle_t handle;
};

inline hiptensorHandle_t GetCuTensorHandle() {
  hipFree(0);
  return CutensorLib::getCutensorHandle();
}

