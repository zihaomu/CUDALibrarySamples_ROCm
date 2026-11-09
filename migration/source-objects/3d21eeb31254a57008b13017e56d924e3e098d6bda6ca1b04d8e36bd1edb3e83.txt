/*
 * SPDX-FileCopyrightText: Copyright (c) 2021-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
#include <stdio.h>

#include <fstream>

#include <npp.h>

#if __has_include(<nppworkspace.h>)
#include <nppworkspace.h>
#define NPP_HAS_WORKSPACE 1 // NPP 13.2.0.58 (CTK 13.4 and later)
#else
#define NPP_HAS_WORKSPACE 0 // older NPP: the application allocates the scratch buffers
#endif



#ifdef _WIN32

#define WINDOWS_LEAN_AND_MEAN

#define NOMINMAX

#include <windows.h>

#pragma warning(disable:4819)

#endif



// Input/output file paths

const std::string INPUT_PATH = "images/CircuitBoard_2048x1024_8u.raw";

const std::string OUTPUT_LABELS = "images/CircuitBoard_LabelMarkersUF_8Way_2048x1024_32u.raw";

const std::string OUTPUT_COMPRESSED = "images/CircuitBoard_CompressedMarkerLabelsUF_8Way_2048x1024_32u.raw";

const std::string OUTPUT_CONTOURS = "images/CircuitBoard_Contours_8Way_2048x1024_8u.raw";

const std::string OUTPUT_GEOMETRY = "images/CircuitBoard_ContoursReconstructed_8Way_2048x1024_8u.raw";



// Dimensions

constexpr int WIDTH = 2048;

constexpr int HEIGHT = 1024;



// Helper to load raw 8-bit image

int loadImage(Npp8u* dst, const std::string& path, int width, int height) {

    FILE* fp = fopen(path.c_str(), "rb");

    if (!fp) return -1;

    size_t read = fread(dst, 1, width * height, fp);

    fclose(fp);

    return (read == width * height) ? 0 : -1;

}



int main() {

    NppiSize roi = { WIDTH, HEIGHT };

    NppStreamContext ctx = {};

    hipGetDevice(&ctx.nCudaDeviceId);

    hipStreamCreate(&ctx.hStream);

    // Attach an NPP workspace so label generation takes its scratch from a reusable high-water-mark buffer.
#if NPP_HAS_WORKSPACE
    nppiWorkspaceCreate(&ctx);
#endif



    // Allocate device and host memory

    Npp8u* d_input = nullptr; hipMalloc(&d_input, WIDTH * HEIGHT);

    Npp32u* d_labels = nullptr; hipMalloc(&d_labels, WIDTH * HEIGHT * sizeof(Npp32u));

    Npp8u* h_input = (Npp8u*)malloc(WIDTH * HEIGHT);

    Npp32u* h_labels = (Npp32u*)malloc(WIDTH * HEIGHT * sizeof(Npp32u));



    if (loadImage(h_input, INPUT_PATH, WIDTH, HEIGHT) != 0) return -1;

    hipMemcpy2DAsync(d_input, WIDTH, h_input, WIDTH, WIDTH, HEIGHT, hipMemcpyHostToDevice, ctx.hStream);



    // Labeling



    // With an NPP workspace the scratch buffer is NULL; otherwise allocate it here.
    Npp8u* d_scratch = nullptr;

#if !NPP_HAS_WORKSPACE
    int scratchSize = 0;

    NppStatus bufStatus = nppiLabelMarkersUFGetBufferSize_32u_C1R(roi, &scratchSize);

    if (bufStatus != NPP_SUCCESS) {
        fprintf(stderr, "nppiLabelMarkersUFGetBufferSize_32u_C1R failed with status %d\n", (int)bufStatus);
        return 1;
    }

    hipError_t mallocStatus = hipMalloc(&d_scratch, scratchSize > 0 ? scratchSize : 1);

    if (mallocStatus != hipSuccess) {
        fprintf(stderr, "hipMalloc of the label scratch buffer failed: %s\n", hipGetErrorString(mallocStatus));
        return 1;
    }
#endif

    nppiLabelMarkersUF_8u32u_C1R_Ctx(d_input, WIDTH, d_labels, WIDTH * sizeof(Npp32u), roi, nppiNormInf, d_scratch, ctx);

    hipMemcpy2DAsync(h_labels, WIDTH * sizeof(Npp32u), d_labels, WIDTH * sizeof(Npp32u), WIDTH * sizeof(Npp32u), HEIGHT, hipMemcpyDeviceToHost, ctx.hStream);

    hipStreamSynchronize(ctx.hStream);



    FILE* fp = fopen(OUTPUT_LABELS.c_str(), "wb");

    fwrite(h_labels, sizeof(Npp32u), WIDTH * HEIGHT, fp); fclose(fp);



    // Label compression

    int compScratchSize = 0;

    nppiCompressMarkerLabelsGetBufferSize_32u_C1R(WIDTH * HEIGHT, &compScratchSize);

    Npp8u* d_compScratch = nullptr;

    int compressedCount = 0;

    // Try the NPP workspace first (NULL scratch buffer). Libraries without workspace support for this function
    // return NPP_NULL_POINTER_ERROR, in which case allocate the scratch buffer and call again.
    NppStatus compStatus = nppiCompressMarkerLabelsUF_32u_C1IR_Ctx(d_labels, WIDTH * sizeof(Npp32u), roi, WIDTH * HEIGHT, &compressedCount, nullptr, ctx);

    if (compStatus == NPP_NULL_POINTER_ERROR) {
        hipMalloc(&d_compScratch, compScratchSize > 0 ? compScratchSize : 1); // never pass NPP a null buffer outside the workspace path
        nppiCompressMarkerLabelsUF_32u_C1IR_Ctx(d_labels, WIDTH * sizeof(Npp32u), roi, WIDTH * HEIGHT, &compressedCount, d_compScratch, ctx);
    }

    hipMemcpy2DAsync(h_labels, WIDTH * sizeof(Npp32u), d_labels, WIDTH * sizeof(Npp32u), WIDTH * sizeof(Npp32u), HEIGHT, hipMemcpyDeviceToHost, ctx.hStream);

    hipStreamSynchronize(ctx.hStream);



    fp = fopen(OUTPUT_COMPRESSED.c_str(), "wb");

    fwrite(h_labels, sizeof(Npp32u), WIDTH * HEIGHT, fp); fclose(fp);



    // Contour extraction

    Npp8u* d_contours = nullptr; hipMalloc(&d_contours, WIDTH * HEIGHT);

    NppiContourPixelDirectionInfo* d_directions = nullptr; hipMalloc(&d_directions, WIDTH * HEIGHT * sizeof(NppiContourPixelDirectionInfo));

    Npp32u* d_counts = nullptr; hipMalloc(&d_counts, (compressedCount + 4) * sizeof(Npp32u));

    Npp32u* d_found = nullptr; hipMalloc(&d_found, (compressedCount + 4) * sizeof(Npp32u));

    Npp32u* d_offsets = nullptr; hipMalloc(&d_offsets, (compressedCount + 4) * sizeof(Npp32u));

    // The info list needs more room than compressedCount entries; ask NPP for the exact size.
    unsigned int infoListSize = 0;

    nppiCompressedMarkerLabelsUFGetInfoListSize_32u_C1R(compressedCount, &infoListSize);

    NppiCompressedMarkerLabelsInfo* d_info = nullptr; hipMalloc(&d_info, infoListSize);



    // When a contour direction image is requested, NPP also requires the host totals structure and the host
    // pixel-count and starting-offset lists (it returns NPP_NULL_POINTER_ERROR otherwise).
    NppiContourTotalsInfo contourTotals = {};

    Npp32u* h_counts = (Npp32u*)malloc((compressedCount + 4) * sizeof(Npp32u));

    Npp32u* h_offsets = (Npp32u*)malloc((compressedCount + 4) * sizeof(Npp32u));

    NppStatus infoStatus = nppiCompressedMarkerLabelsUFInfo_32u_C1R_Ctx(d_labels, WIDTH * sizeof(Npp32u), roi, compressedCount, d_info, d_contours, WIDTH, d_directions, WIDTH * sizeof(NppiContourPixelDirectionInfo), &contourTotals, d_counts, h_counts, d_offsets, h_offsets, ctx);

    hipStreamSynchronize(ctx.hStream);

    if (infoStatus != NPP_SUCCESS) {
        fprintf(stderr, "nppiCompressedMarkerLabelsUFInfo_32u_C1R_Ctx failed with status %d\n", (int)infoStatus);
        return 1;
    }



    // Copy and write contours

    Npp8u* h_contours = (Npp8u*)malloc(WIDTH * HEIGHT);

    hipMemcpy(h_contours, d_contours, WIDTH * HEIGHT, hipMemcpyDeviceToHost);

    fp = fopen(OUTPUT_CONTOURS.c_str(), "wb");

    fwrite(h_contours, 1, WIDTH * HEIGHT, fp); fclose(fp);



    // Clean up

    hipFree(d_input); hipFree(d_labels); hipFree(d_scratch);

    hipFree(d_compScratch); hipFree(d_contours); hipFree(d_directions);

    hipFree(d_counts); hipFree(d_found); hipFree(d_offsets); hipFree(d_info);

    free(h_input); free(h_labels); free(h_contours); free(h_counts); free(h_offsets);

#if NPP_HAS_WORKSPACE
    nppiWorkspaceDestroy(&ctx);
#endif

    hipStreamDestroy(ctx.hStream);



    printf("Done. Compressed Labels: %d\n", compressedCount);

    printf("Contour pixels: %u\n", (unsigned)contourTotals.nTotalImagePixelContourCount);

    return 0;

}