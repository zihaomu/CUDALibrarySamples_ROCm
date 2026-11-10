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

// Template matching with normalized cross-correlation (NCC) in NPP.
//
// A template is cut out of a circuit-board image and deliberately degraded (gain, offset and noise), then located
// again in the full image:
//
//     nppiCrossCorrValid_NormLevel_8u32f_C1R_Ctx   NCC score for every template position
//     nppiMaxIndx_32f_C1R_Ctx                      position of the best score, found on the GPU
//
// The "NormLevel" score is the zero-mean normalized correlation coefficient (Pearson), in [-1, 1].  Because the mean and
// the energy of both patches are removed, the score does not change if the template has a different brightness (offset)
// or contrast (gain) than the image, which makes it robust to illumination changes in inspection setups.
//
// The sample checks the GPU scores against a CPU computation, reports how clearly the best match stands out from the
// next best one, writes an annotated copy of the image, and times the GPU search.

#include "batch15_image.hpp"
int main(){return migration_image::main15("ncc");}
