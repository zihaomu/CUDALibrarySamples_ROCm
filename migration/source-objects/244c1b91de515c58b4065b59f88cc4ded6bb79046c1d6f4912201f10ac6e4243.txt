// SPDX-License-Identifier: Apache-2.0
// Independent test-vector producer linked against pinned OpenJPEG v2.5.4.
// OpenJPEG itself remains in the private build directory (BSD-2-Clause).
#include "opj_includes.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void save(const char *directory, const char *name, const unsigned char *data,
                 size_t count) {
    char path[1024];
    if (snprintf(path, sizeof(path), "%s/%s", directory, name) >= (int)sizeof(path))
        exit(4);
    FILE *file = fopen(path, "wb");
    if (!file || fwrite(data, 1, count, file) != count || fclose(file)) exit(5);
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    for (unsigned case_id = 0; case_id < 4; ++case_id) {
        const unsigned lengths[4] = {97, 256, 511, 1023};
        const unsigned length = lengths[case_id];
        unsigned char encoded[4096] = {0};
        unsigned char bits[1023], contexts[1023], observed[1023];
        uint32_t rng = 0x91ab3511U + 31U * case_id;
        for (unsigned i = 0; i < length; ++i) {
            rng ^= rng << 13; rng ^= rng >> 17; rng ^= rng << 5;
            contexts[i] = (unsigned char)((i * 7U + case_id * 3U) % 19U);
            bits[i] = (unsigned char)(case_id == 0 ? 0U :
                case_id == 1 ? (i & 1U) :
                case_id == 2 ? (i % 17U == 0U) : (rng & 1U));
        }
        opj_mqc_t coder;
        opj_mqc_t *mqc = &coder;
        opj_mqc_resetstates(mqc);
        opj_mqc_setstate(mqc, 0, 0, 4);
        opj_mqc_setstate(mqc, 17, 0, 3);
        opj_mqc_setstate(mqc, 18, 0, 46);
        opj_mqc_init_enc(mqc, encoded + 1);
        for (unsigned i = 0; i < length; ++i) {
            opj_mqc_setcurctx(mqc, contexts[i]);
            opj_mqc_encode_macro(mqc, mqc->curctx, mqc->a, mqc->c, mqc->ct, bits[i]);
        }
        opj_mqc_flush(mqc);
        unsigned encoded_length = opj_mqc_numbytes(mqc);
        if (encoded_length == 0 || encoded_length > 4090) return 6;

        opj_mqc_t decoder;
        mqc = &decoder;
        opj_mqc_resetstates(mqc);
        opj_mqc_setstate(mqc, 0, 0, 4);
        opj_mqc_setstate(mqc, 17, 0, 3);
        opj_mqc_setstate(mqc, 18, 0, 46);
        opj_mqc_init_dec(mqc, encoded + 1, encoded_length, 2);
        for (unsigned i = 0; i < length; ++i) {
            unsigned value;
            opj_mqc_setcurctx(mqc, contexts[i]);
            opj_mqc_decode(value, mqc);
            observed[i] = (unsigned char)value;
        }
        opq_mqc_finish_dec(mqc);
        if (memcmp(bits, observed, length)) return 7;
        char name[64];
        snprintf(name, sizeof(name), "case%u.mq", case_id);
        save(argv[1], name, encoded + 1, encoded_length);
        snprintf(name, sizeof(name), "case%u.bits", case_id);
        save(argv[1], name, bits, length);
        snprintf(name, sizeof(name), "case%u.ctx", case_id);
        save(argv[1], name, contexts, length);
        printf("case=%u symbols=%u bytes=%u\n", case_id, length, encoded_length);
    }
    return 0;
}
