// SPDX-License-Identifier: BSD-2-Clause
// Isolated JPEG2000 MQ arithmetic decoder. State transitions use mq_states.hpp
// (numeric table from OpenJPEG v2.5.4, BSD-2-Clause, see OPENJPEG-LICENSE).
#pragma once
#include "mq_states.hpp"

namespace image_j2k_mq {

__device__ inline void bytein(const unsigned char *input, int bytes, int &position,
                              uint32_t &c, uint32_t &ct) {
    const uint32_t current = position < bytes ? input[position] : 0xffU;
    const uint32_t next = position + 1 < bytes ? input[position + 1] : 0xffU;
    if (current == 0xffU) {
        if (next > 0x8fU) {
            c += 0xff00U;
            ct = 8;
        } else {
            ++position;
            c += next << 9;
            ct = 7;
        }
    } else {
        ++position;
        c += next << 8;
        ct = 8;
    }
}

__device__ inline void renorm(const unsigned char *input, int bytes, int &position,
                              uint32_t &a, uint32_t &c, uint32_t &ct) {
    do {
        if (ct == 0) bytein(input, bytes, position, c, ct);
        a <<= 1;
        c <<= 1;
        --ct;
    } while (a < 0x8000U);
}

__device__ inline int decode(const unsigned char *input, int bytes,
                             const unsigned char *contexts, int count,
                             unsigned char *output) {
    if (bytes < 2 || count < 1 || count > 65536) return 1;
    uint8_t context_state[19] = {0};
    context_state[0] = 8;
    context_state[17] = 6;
    context_state[18] = 92;
    int position = 0;
    uint32_t c = static_cast<uint32_t>(input[0]) << 16;
    uint32_t ct = 0;
    bytein(input, bytes, position, c, ct);
    c <<= 7;
    ct -= 7;
    uint32_t a = 0x8000U;
    for (int i = 0; i < count; ++i) {
        const unsigned context = contexts[i];
        if (context >= 19) return 2;
        const State state = states[context_state[context]];
        a -= state.qeval;
        unsigned symbol;
        if ((c >> 16) < state.qeval) {
            if (a < state.qeval) {
                a = state.qeval;
                symbol = state.mps;
                context_state[context] = static_cast<uint8_t>(state.nmps);
            } else {
                a = state.qeval;
                symbol = 1U - state.mps;
                context_state[context] = static_cast<uint8_t>(state.nlps);
            }
            renorm(input, bytes, position, a, c, ct);
        } else {
            c -= state.qeval << 16;
            if ((a & 0x8000U) == 0) {
                if (a < state.qeval) {
                    symbol = 1U - state.mps;
                    context_state[context] = static_cast<uint8_t>(state.nlps);
                } else {
                    symbol = state.mps;
                    context_state[context] = static_cast<uint8_t>(state.nmps);
                }
                renorm(input, bytes, position, a, c, ct);
            } else {
                symbol = state.mps;
            }
        }
        output[i] = static_cast<unsigned char>(symbol);
    }
    return 0;
}

__global__ void decode_one(const unsigned char *input, int bytes,
                           const unsigned char *contexts, int count,
                           unsigned char *output, int *status) {
    if (blockIdx.x == 0 && threadIdx.x == 0)
        *status = decode(input, bytes, contexts, count, output);
}

} // namespace image_j2k_mq
