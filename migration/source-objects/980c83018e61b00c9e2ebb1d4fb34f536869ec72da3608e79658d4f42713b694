// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <stdint.h>
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif
/* Narrow sample ABI: FP64, INT32 indices/shape arrays, column-major. Metadata
 * lives on the host; all value/index buffers and batch pointer tables are GPU
 * allocations owned by the caller. Format bits follow the original samples. */
typedef struct mh_query {
 int64_t sizes[5]; /* batch, first nrows, first ncols, original nnz, ld */
 void *pointers[8]; /* row, column, values, nrows[], ncols[], nnz[], ld[], rowEnd */
 int32_t codes[8]; /* format,index,offset,value,mtype,mview,base,layout */
} mh_query;
int mh_alloc(void **p,size_t bytes);
int mh_upload(void *p,const void *host,size_t bytes);
int mh_download(void *host,const void *p,size_t bytes);
int mh_free(void *p);
int mh_context_create(int batched,void **context);
int mh_context_destroy(void *context);
int mh_create(int format,int batch,int32_t *nr,int32_t *nc,int32_t *nnz,int32_t *ld,
              void *rows,void *columns,void *values,int base,void **handle);
int mh_get(void *handle,mh_query *out,int mask); /* 1 sizes,2 pointers,4 codes */
int mh_set_values(void *handle,void *values);
int mh_set_csr(void *handle,void *rows,void *columns,void *values);
int mh_destroy(void *handle);
int mh_snapshot(const char *name,const mh_query *q,void *rows,void *columns,void *values,
                int32_t *nr,int32_t *nc,int32_t *nnz,int32_t *ld);
int mh_save(const char *name,const void *data,size_t bytes);
size_t mh_query_bytes(void);
#ifdef __cplusplus
}
#endif
