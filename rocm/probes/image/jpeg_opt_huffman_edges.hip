// SPDX-License-Identifier: Apache-2.0
#include "jpeg_optimal_huffman.hpp"
#include <iostream>

static int validate(const std::array<unsigned,256>& frequencies) {
    JHUFF_TBL table{};
    image_jpeg_opt::make_table(&table, frequencies.data());
    auto codes = make_codes(&table);
    int active = 0, longest = 0;
    for (int symbol = 0; symbol < 256; ++symbol) {
        if (!frequencies[symbol]) {
            if (codes[symbol].length) throw std::runtime_error("unused symbol received code");
            continue;
        }
        const auto code = codes[symbol];
        if (code.length < 1 || code.length > 16 ||
            code.bits == ((1U << code.length) - 1))
            throw std::runtime_error("invalid JPEG canonical code");
        longest = std::max(longest, int(code.length));
        ++active;
        for (int other = 0; other < symbol; ++other) {
            if (!frequencies[other]) continue;
            auto prior = codes[other];
            if ((code.length <= prior.length &&
                 code.bits == (prior.bits >> (prior.length - code.length))) ||
                (prior.length <= code.length &&
                 prior.bits == (code.bits >> (code.length - prior.length))))
                throw std::runtime_error("JPEG Huffman prefix collision");
        }
    }
    int inventory = 0;
    for (int depth = 1; depth <= 16; ++depth) inventory += table.bits[depth];
    if (inventory != active) throw std::runtime_error("DHT symbol inventory mismatch");
    return longest;
}

int main() {
    try {
        std::array<unsigned,256> counts{};
        counts[0] = 1;
        int singleton = validate(counts);
        counts.fill(1);
        int uniform = validate(counts);
        counts.fill(0);
        for (int i = 0; i < 25; ++i) counts[i] = 1U << i;
        int long_tail = validate(counts);
        counts.fill(0);
        for (int i = 0; i < 120; ++i) counts[(i * 67) % 256] = 1U + ((i * 23) % 37);
        int sparse = validate(counts);
        counts.fill(0); counts[0] = 0xffffffffU; counts[1] = 1;
        int skewed = validate(counts);
        std::cout << "{\"singleton\":" << singleton
                  << ",\"uniform256\":" << uniform
                  << ",\"power2-25\":" << long_tail
                  << ",\"sparse120\":" << sparse
                  << ",\"max-skew\":" << skewed << "}" << std::endl;
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "RESULT status=FAIL reason=" << error.what() << std::endl;
        return 1;
    }
}
