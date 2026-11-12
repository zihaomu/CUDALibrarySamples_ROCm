/*
 * SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

// Straight-line detection using project HIP Canny and Hough accumulator kernels.
//
//     gray image --nppiFilterCannyBorder_8u_C1R_Ctx--> binary edge image
//                --nppiFilterHoughLine_8u32f_C1R_Ctx--> list of lines (rho, theta) in device memory
//
// By default the sample draws a synthetic image with five lines of known position and orientation (plus noise), so the
// detections can be checked against the truth.  A real 8-bit gray RAW image can be used instead with -i/-w/-h, in which
// case the detected lines are only drawn.
//
// HIP returns each peak as {rho index, theta degrees, votes}.  theta is in degrees.  rho is an accumulator index: the signed
// distance of the line from the image centre in pixels is rho - accumulatorHeight/2, with
//     x*cos(theta) + y*sin(theta) = rho_signed     (x, y measured from the image centre).
// This sample uses the recommended discretization nDelta = {1.0, 1.0} (1 pixel, 1 degree).

#include <hip/hip_runtime.h>
#include "../../../common/image/canny.h"
#include "../../../common/image/hough.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>

#define CHECK_CUDA(call)                                                                      \
    do {                                                                                      \
        hipError_t e_ = (call);                                                              \
        if (e_ != hipSuccess) {                                                              \
            fprintf(stderr, "CUDA error %s at %s:%d\n", hipGetErrorString(e_), __FILE__, __LINE__); \
            exit(EXIT_FAILURE);                                                               \
        }                                                                                     \
    } while (0)

static const double kPi = 3.14159265358979323846;

struct Line { double rho, theta; }; // rho: signed distance from the image centre (pixels), theta: degrees

// Synthetic test image: dark gray background, five 3-pixel-wide bright lines, light noise.
static const Line kTruth[5] = {{-150, 30}, {80, 100}, {200, 75}, {-60, 160}, {0, 45}};

static void makeSyntheticImage(std::vector<uint8_t>& img, int W, int H)
{
    img.assign((size_t)W * H, 40);
    const double cx = W >> 1, cy = H >> 1;
    for (const Line& l : kTruth) {
        const double t = l.theta * kPi / 180.0, c = std::cos(t), s = std::sin(t);
        for (int y = 0; y < H; ++y)
            for (int x = 0; x < W; ++x)
                if (std::fabs((x - cx) * c + (y - cy) * s - l.rho) < 1.5) img[(size_t)y * W + x] = 220;
    }
    srand(7);
    for (auto& p : img) p = (uint8_t)std::min(255, std::max(0, (int)p + (rand() % 7) - 3));
}

// Draw one line (rho signed from the centre, theta degrees) into an RGB image, clipped to the image.
static void drawLine(std::vector<uint8_t>& rgb, int W, int H, const Line& l)
{
    const double cx = W >> 1, cy = H >> 1, t = l.theta * kPi / 180.0, c = std::cos(t), s = std::sin(t);
    auto put = [&](int x, int y) {
        if (x >= 0 && x < W && y >= 0 && y < H) { uint8_t* p = &rgb[((size_t)y * W + x) * 3]; p[0] = 255; p[1] = 40; p[2] = 40; }
    };
    if (l.theta >= 45 && l.theta <= 135) {
        for (int x = 0; x < W; ++x) put(x, (int)std::lround((l.rho - (x - cx) * c) / s + cy));
    } else {
        for (int y = 0; y < H; ++y) put((int)std::lround((l.rho - (y - cy) * s) / c + cx), y);
    }
}

int main(int argc, char** argv)
{
    int         W = 1024, H = 768, threshold = 300, maxLines = 500, iterations = 50;
    int         cannyLow = 60, cannyHigh = 120;
    std::string imagePath;
    for (int i = 1; i < argc; ++i) {
        std::string a = argv[i];
        auto next = [&]() { return (i + 1 < argc) ? argv[++i] : (char*)"0"; };
        if (a == "-i") imagePath = next();
        else if (a == "-w") W = atoi(next());
        else if (a == "-h") H = atoi(next());
        else if (a == "-t") threshold = atoi(next());
        else if (a == "-m") maxLines = atoi(next());
        else if (a == "-n") iterations = atoi(next());
        else if (a == "-cl") cannyLow = atoi(next());
        else if (a == "-ch") cannyHigh = atoi(next());
        else {
            printf("Usage: %s [-t vote-threshold] [-m max-lines] [-n timing-iterations] [-cl canny-low] [-ch canny-high]\n"
                   "          [-i image.raw -w width -h height]\n"
                   "  Without -i a synthetic 1024x768 image with five known lines is used and the result is verified.\n"
                   "  -i reads an 8-bit gray RAW image; detected lines are drawn but not verified.\n", argv[0]);
            return 0;
        }
    }
    if (W < 16 || H < 16 || W > 16384 || H > 16384 || maxLines < 1 || maxLines > 1000000 || threshold < 1 || iterations < 0 ||
        cannyLow < 0 || cannyHigh < cannyLow || cannyHigh > 32767) {
        fprintf(stderr, "Invalid option: need 16 <= -w/-h <= 16384, 1 <= -m <= 1000000, -t >= 1, -n >= 0 and 0 <= -cl <= -ch <= 32767\n");
        return EXIT_FAILURE;
    }

    const bool synthetic = imagePath.empty();
    std::vector<uint8_t> gray;
    if (synthetic) {
        makeSyntheticImage(gray, W, H);
    } else {
        gray.resize((size_t)W * H);
        std::ifstream f(imagePath, std::ios::binary);
        if (!f || !f.read(reinterpret_cast<char*>(gray.data()), gray.size())) {
            fprintf(stderr, "Cannot read %zu bytes from %s\n", gray.size(), imagePath.c_str());
            return EXIT_FAILURE;
        }
    }

    hipStream_t stream;
    CHECK_CUDA(hipStreamCreate(&stream));
    uint64_t cannyBytes = 0;
    CHECK_CUDA(rocm_image_canny_workspace_size(W, H, &cannyBytes));
    const int accHeight = rocm_image_hough_accumulator_height(W, H);
    const int capacity = accHeight * 180;
    uint8_t *d_gray, *d_edges;
    void* d_cannyBuf;
    RocmHoughPeak* d_lines;
    int* d_lineCount;
    CHECK_CUDA(hipMalloc(&d_gray, gray.size()));
    CHECK_CUDA(hipMalloc(&d_edges, gray.size()));
    CHECK_CUDA(hipMalloc(&d_cannyBuf, cannyBytes));
    CHECK_CUDA(hipMalloc(&d_lines, (size_t)capacity * sizeof(RocmHoughPeak)));
    CHECK_CUDA(hipMalloc(&d_lineCount, sizeof(int)));
    CHECK_CUDA(hipMemcpyAsync(d_gray, gray.data(), gray.size(), hipMemcpyHostToDevice, stream));

    auto canny = [&]() {
        CHECK_CUDA(rocm_image_canny_local(d_gray, gray.size(), W, W, H, 1,
            cannyLow, cannyHigh, d_edges, gray.size(), W, d_cannyBuf, cannyBytes, stream));
    };
    auto hough = [&]() {
        CHECK_CUDA(rocm_image_hough_peaks(d_edges, W, H, threshold,
            d_lines, capacity, d_lineCount, stream));
    };

    canny();
    hough();
    int candidateCount = 0;
    CHECK_CUDA(hipMemcpyAsync(&candidateCount, d_lineCount, sizeof(int), hipMemcpyDeviceToHost, stream));
    CHECK_CUDA(hipStreamSynchronize(stream));
    if (candidateCount < 0 || candidateCount > capacity) {
        fprintf(stderr, "Hough candidate count out of range\n");
        return EXIT_FAILURE;
    }
    std::vector<RocmHoughPeak> raw(candidateCount);
    if (candidateCount) CHECK_CUDA(hipMemcpyAsync(raw.data(), d_lines,
        raw.size() * sizeof(RocmHoughPeak), hipMemcpyDeviceToHost, stream));
    CHECK_CUDA(hipStreamSynchronize(stream));
    std::sort(raw.begin(), raw.end(), [](const RocmHoughPeak& a, const RocmHoughPeak& b) {
        if (a.votes != b.votes) return a.votes > b.votes;
        if (a.theta_degrees != b.theta_degrees) return a.theta_degrees < b.theta_degrees;
        return a.rho_index < b.rho_index;
    });
    const int found = std::min(candidateCount, maxLines);
    std::vector<Line> lines(found);
    for (int i = 0; i < found; ++i)
        lines[i] = {double(raw[i].rho_index - (accHeight >> 1)), double(raw[i].theta_degrees)};
    std::sort(lines.begin(), lines.end(), [](const Line& a, const Line& b) {
        return a.theta != b.theta ? a.theta < b.theta : a.rho < b.rho;
    });
    // Project diagnostic: keep every GPU peak inspectable even when the
    // original sample suppresses stdout for more than forty lines.
    {
        std::ofstream csv("hough_lines.csv",std::ios::binary);
        csv << "rho,theta\n";
        for (const Line& l:lines) csv << int(l.rho) << ',' << int(l.theta) << '\n';
        if (!csv) { std::fprintf(stderr,"Cannot write hough_lines.csv\n"); return EXIT_FAILURE; }
    }

    printf("%s image %dx%d, Canny %d/%d, Hough threshold %d\n", synthetic ? "Synthetic" : imagePath.c_str(), W, H, cannyLow,
           cannyHigh, threshold);
    printf("Detected %d line(s)%s\n", found, found == maxLines ? "  (hit the -m limit: raise it or the threshold)" : "");
    if (found <= 40)
        for (const Line& l : lines) printf("  theta %6.1f deg   rho %8.1f px\n", l.theta, l.rho);

    bool ok = true;
    if (synthetic) {
        // Each true line is a 3-pixel-wide band, so Canny outlines both sides and two detections per line are expected.
        printf("Check against the five true lines (tolerance 3 px, 1 degree):\n");
        for (const Line& t : kTruth) {
            int n = 0;
            for (const Line& l : lines)
                if (std::fabs(l.rho - t.rho) <= 3.0 && std::fabs(l.theta - t.theta) <= 1.0) ++n;
            printf("  true theta %5.1f rho %6.1f : %d detection(s)%s\n", t.theta, t.rho, n,
                   n ? "" : "   <-- MISSED");
            if (n == 0) ok = false;
        }
        int extra = 0;
        for (const Line& l : lines) {
            bool matched = false;
            for (const Line& t : kTruth)
                if (std::fabs(l.rho - t.rho) <= 3.0 && std::fabs(l.theta - t.theta) <= 1.0) matched = true;
            if (!matched) ++extra;
        }
        printf("Detections not matching any true line: %d\n", extra);
        printf("All five lines found: [%s]\n", ok ? "PASS" : "FAIL");
    }

    // Output: input image in gray with the detected lines in red.
    {
        std::vector<uint8_t> rgb((size_t)W * H * 3);
        for (size_t i = 0; i < gray.size(); ++i) rgb[3 * i] = rgb[3 * i + 1] = rgb[3 * i + 2] = gray[i];
        for (const Line& l : lines) drawLine(rgb, W, H, l);
        std::ofstream ppm("hough_result.ppm", std::ios::binary);
        ppm << "P6\n" << W << " " << H << "\n255\n";
        ppm.write(reinterpret_cast<const char*>(rgb.data()), rgb.size());
    }

    // Time the two stages separately. -n 0 skips the timing.
    if (iterations == 0) {
        printf("Timing skipped (-n 0)\n");
    } else {
        hipEvent_t e0, e1, e2;
        CHECK_CUDA(hipEventCreate(&e0));
        CHECK_CUDA(hipEventCreate(&e1));
        CHECK_CUDA(hipEventCreate(&e2));
        CHECK_CUDA(hipEventRecord(e0, stream));
        for (int i = 0; i < iterations; ++i) canny();
        CHECK_CUDA(hipEventRecord(e1, stream));
        for (int i = 0; i < iterations; ++i) hough();
        CHECK_CUDA(hipEventRecord(e2, stream));
        CHECK_CUDA(hipEventSynchronize(e2));
        float msCanny = 0.f, msHough = 0.f;
        CHECK_CUDA(hipEventElapsedTime(&msCanny, e0, e1));
        CHECK_CUDA(hipEventElapsedTime(&msHough, e1, e2));
        printf("GPU time per frame: Canny %.3f ms, Hough %.3f ms (average of %d runs)\n", msCanny / iterations, msHough / iterations,
               iterations);

        hipEventDestroy(e0); hipEventDestroy(e1); hipEventDestroy(e2);
    }
    hipFree(d_gray); hipFree(d_edges); hipFree(d_cannyBuf); hipFree(d_lines); hipFree(d_lineCount);
    hipStreamDestroy(stream);
    return ok ? EXIT_SUCCESS : EXIT_FAILURE;
}
