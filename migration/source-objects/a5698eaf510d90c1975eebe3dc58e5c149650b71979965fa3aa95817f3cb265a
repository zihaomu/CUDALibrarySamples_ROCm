// SPDX-License-Identifier: Apache-2.0
// Frequency-adaptive baseline JPEG Huffman tables from actual GPU MCU symbols.
#pragma once
#include "jpeg_full_gpu.hpp"
#include <algorithm>
#include <array>
#include <queue>

namespace image_jpeg_opt {

__global__ static void histogram(const short *coefficients, const int *previous,
                                 const unsigned char *component, unsigned *counts,
                                 unsigned *invalid, int blocks) {
    int id = blockIdx.x * blockDim.x + threadIdx.x;
    if (id >= blocks) return;
    const short *c = coefficients + size_t(id) * 64;
    const int group = component[id] == 0 ? 0 : 1;
    const int prev = previous[id];
    int value = int(c[0]) - (prev < 0 ? 0 : int(coefficients[size_t(prev) * 64]));
    int size = category(value);
    if (size > 11) { atomicExch(invalid, 1U); return; }
    atomicAdd(counts + group * 256 + size, 1U);
    const int zigzag[64] = {0,1,8,16,9,2,3,10,17,24,32,25,18,11,4,5,12,19,26,33,40,48,41,34,27,20,13,6,7,14,21,28,35,42,49,56,57,50,43,36,29,22,15,23,30,37,44,51,58,59,52,45,38,31,39,46,53,60,61,54,47,55,62,63};
    int zeros = 0;
    for (int k = 1; k < 64; ++k) {
        value = c[zigzag[k]];
        if (!value) { ++zeros; continue; }
        while (zeros >= 16) {
            atomicAdd(counts + (group + 2) * 256 + 0xf0, 1U);
            zeros -= 16;
        }
        size = category(value);
        if (size > 10) { atomicExch(invalid, 1U); return; }
        atomicAdd(counts + (group + 2) * 256 + (zeros << 4) + size, 1U);
        zeros = 0;
    }
    if (zeros) atomicAdd(counts + (group + 2) * 256, 1U);
}

inline void make_table(JHUFF_TBL *table, const unsigned *counts) {
    struct Node { uint64_t frequency; int left, right, symbol; };
    std::vector<Node> nodes;
    using Item = std::pair<uint64_t, int>;
    std::priority_queue<Item, std::vector<Item>, std::greater<Item>> queue;
    std::array<int, 257> depths{};
    for (int symbol = 0; symbol <= 256; ++symbol) {
        uint64_t frequency = symbol == 256 ? 1 : counts[symbol];
        if (!frequency) continue;
        int index = static_cast<int>(nodes.size());
        nodes.push_back({frequency, -1, -1, symbol});
        queue.push({frequency, index});
    }
    while (queue.size() > 1) {
        auto left = queue.top(); queue.pop();
        auto right = queue.top(); queue.pop();
        int index = static_cast<int>(nodes.size());
        nodes.push_back({left.first + right.first, left.second, right.second, -1});
        queue.push({nodes.back().frequency, index});
    }
    auto visit = [&](auto &&self, int index, int depth) -> void {
        const auto &node = nodes[index];
        if (node.symbol >= 0) { depths[node.symbol] = depth; return; }
        self(self, node.left, depth + 1);
        self(self, node.right, depth + 1);
    };
    visit(visit, queue.top().second, 0);
    std::array<int, 257> lengths{};
    for (int depth : depths) if (depth) {
        if (depth > 256) throw std::runtime_error("Huffman tree depth exceeds bound");
        ++lengths[depth];
    }
    for (int depth = 256; depth > 16; --depth) {
        while (lengths[depth] > 0) {
            if (lengths[depth] < 2) throw std::runtime_error("invalid JPEG Huffman depth count");
            int shorter = depth - 2;
            while (shorter > 0 && lengths[shorter] == 0) --shorter;
            if (shorter == 0) throw std::runtime_error("cannot limit JPEG Huffman depths");
            lengths[depth] -= 2;
            ++lengths[depth - 1];
            lengths[shorter]--;
            lengths[shorter + 1] += 2;
        }
    }
    int longest = 16;
    while (longest > 0 && lengths[longest] == 0) --longest;
    if (!longest) throw std::runtime_error("empty optimized JPEG Huffman table");
    --lengths[longest]; // Remove pseudo-symbol 256 to avoid an all-ones data code.
    std::vector<std::pair<int, int>> symbols;
    for (int symbol = 0; symbol < 256; ++symbol)
        if (counts[symbol]) symbols.push_back({depths[symbol], symbol});
    std::sort(symbols.begin(), symbols.end());
    int total = 0;
    for (int depth = 1; depth <= 16; ++depth) {
        if (lengths[depth] > 255) throw std::runtime_error("JPEG DHT count overflow");
        table->bits[depth] = static_cast<UINT8>(lengths[depth]);
        total += lengths[depth];
    }
    if (total != static_cast<int>(symbols.size()) || total > 256)
        throw std::runtime_error("optimized JPEG symbol inventory mismatch");
    std::fill(std::begin(table->huffval), std::end(table->huffval), 0);
    for (int i = 0; i < total; ++i)
        table->huffval[i] = static_cast<UINT8>(symbols[i].second);
    table->sent_table = FALSE;
}

} // namespace image_jpeg_opt
