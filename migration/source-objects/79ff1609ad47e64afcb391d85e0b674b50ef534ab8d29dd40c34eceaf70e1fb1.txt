"""Keep original CUDA conversion/SpGEMM/symmetric/custom-op APIs and capture GPU outputs."""
import re
from catalog import ROOT
from batches4_8_spec import GROUPS,kind
for source in GROUPS['b8']:
 k=kind(source);raw=(ROOT/source).read_text();lic=raw.split('#include')[0];p=ROOT/'rocm/ported'/source;p.write_text(lic+'// MIGRATION_BATCH8: explicit GPU semantic adapters.\n#include "batch8_sparse.hpp"\nint main(){return migration_batch::sparse8_main("'+k+'");}\n')
 s='#include "batches_runtime.hpp"\nusing migration_batch::emit;using migration_batch::scalar;\n'+raw
 pos=s.index('{',s.index('int main'))+1;s=s[:pos]+'\nconst std::string migration_case=migration_batch::selected_case();\n'+s[pos:]
 names={'spmat_convert':('h_csr_offsets','h_csr_columns','h_csr_values'),'spgemm_mem':('hA_csrOffsets','hA_columns','hA_values'),'spmv_symmetric_csr':('hA_csrOffsets','hA_columns','hA_values'),'spmvop_csr':('hA_offsets','hA_columns','hA_values'),'spmm_csr_op':('hA_csrOffsets','hA_columns','hA_values')};r,c,v=names[k];nnz=7 if k=='spmv_symmetric_csr' else 9
 pos=s.index('    // Device memory management');code=''
 if k in ['spmat_convert','spgemm_mem']:
  code+=f'if(migration_case=="empty-row"){{int rr[]={{0,3,3,7,9}},cc[]={{0,2,3,0,1,2,3,1,3}};float vv[]={{1,2,3,5,4,6,7,8,9}};std::copy(rr,rr+5,{r});std::copy(cc,cc+9,{c});std::copy(vv,vv+9,{v});}}\n'
 if k=='spmv_symmetric_csr':
  code+=f'if(migration_case=="upper"){{int rr[]={{0,2,4,6,7}},cc[]={{0,1,1,2,2,3,3}};std::copy(rr,rr+5,{r});std::copy(cc,cc+7,{c});}}\n'
 code+=f'if(migration_case=="changed-values")for(int i=0;i<{nnz};++i){v}[i]=-.5*{v}[i]+.25;\n'
 if k in ['spmvop_csr','spmm_csr_op']:code+=f'if(migration_case=="cancellation")for(int i=0;i<{nnz};++i){v}[i]=(i%2?-1:1)*(i+1);\n'
 code+=f'int migration_base=migration_case=="base-one"?1:0;if(migration_base){{for(int i=0;i<5;++i)++{r}[i];for(int i=0;i<{nnz};++i)++{c}[i];}}\n'
 code+=f'emit("input_offsets",std::vector<int>({r},{r}+5));emit("input_columns",std::vector<int>({c},{c}+{nnz}));emit("input_values",std::vector<'+('double' if k=='spmvop_csr' else 'float')+f'>({v},{v}+{nnz}));scalar("input_base",migration_base);\n'
 if k in ['spmv_symmetric_csr','spmvop_csr']:
  code+='emit("input_X",std::vector<'+('double' if k=='spmvop_csr' else 'float')+'>(hX,hX+4));emit("input_Y",std::vector<'+('double' if k=='spmvop_csr' else 'float')+'>(hY,hY+4));\n'
 if k=='spmv_symmetric_csr':code+='scalar("input_alpha",alpha);scalar("input_beta",beta);\n'
 if k=='spgemm_mem':code+='emit("input_B_offsets",std::vector<int>(hB_csrOffsets,hB_csrOffsets+5));emit("input_B_columns",std::vector<int>(hB_columns,hB_columns+8));emit("input_B_values",std::vector<float>(hB_values,hB_values+8));\n'
 if k=='spmm_csr_op':code+='if(migration_case=="changed-values")for(float &x:hB)x=x*.5f-2.f;emit("input_B",std::vector<float>(hB,hB+12));emit("input_C",std::vector<float>(hC,hC+12));\n'
 s=s[:pos]+code+s[pos:]
 s=s.replace('CUSPARSE_INDEX_BASE_ZERO','(migration_base?CUSPARSE_INDEX_BASE_ONE:CUSPARSE_INDEX_BASE_ZERO)')
 if k=='spmv_symmetric_csr':s=s.replace('storage  = CUSPARSE_STORE_LOWER','storage  = migration_case=="upper"?CUSPARSE_STORE_UPPER:CUSPARSE_STORE_LOWER')
 if k=='spgemm_mem':s=s.replace('chunk_fraction = 0.2','chunk_fraction = migration_case=="small-budget"?.05f:.2f');s=s.replace('    // ask bufferSize1 bytes','    scalar("input_chunk_fraction",chunk_fraction);\n    // ask bufferSize1 bytes',1)
 if k=='spgemm_mem':
  s=s.replace('int   hC_columns_tmp[C_NUM_NNZ];','std::vector<int> migration_columns(C_nnz1);int* hC_columns_tmp=migration_columns.data();').replace('float hC_values_tmp[C_NUM_NNZ];','std::vector<float> migration_values(C_nnz1);float* hC_values_tmp=migration_values.data();').replace('dC_columns, C_nnz * sizeof(int)','dC_columns, C_nnz1 * sizeof(int)').replace('dC_values, C_nnz * sizeof(float)','dC_values, C_nnz1 * sizeof(float)')
 if k=='spmvop_csr':s=s.replace('epilogue_data.a = 2.0f;','epilogue_data.a = migration_case=="changed-values"?-1.5:2;').replace('epilogue_data.b = 4.0f;','epilogue_data.b = migration_case=="changed-values"?.25:4;');s=s.replace('    // execute SpMV','    scalar("input_even",epilogue_data.a);scalar("input_odd",epilogue_data.b);\n    // execute SpMV',1)
 # Original hardcoded expected arrays apply only to original input. CPU oracle qualifies every case.
 start=s.index('    int correct = 1;');end=s.index('    //--------------------------------------------------------------------------',start) if k!='spmv_symmetric_csr' else s.index('    CHECK_CUSPARSE(cusparseSpMV_destroyDescr',start)
 obs={'spmat_convert':'emit("CSC_offsets",std::vector<int>(h_csc_offsets,h_csc_offsets+5));emit("CSC_rows",std::vector<int>(h_csc_rows,h_csc_rows+csc_nnz));emit("CSC_values",std::vector<float>(h_csc_values,h_csc_values+csc_nnz));', 'spgemm_mem':'emit("C_offsets",std::vector<int>(hC_csrOffsets_tmp,hC_csrOffsets_tmp+5));emit("C_columns",std::vector<int>(hC_columns_tmp,hC_columns_tmp+C_nnz1));emit("C_values",std::vector<float>(hC_values_tmp,hC_values_tmp+C_nnz1));scalar("cuda_chunk_fraction",chunk_fraction);', 'spmv_symmetric_csr':'emit("Z",std::vector<float>(hZ,hZ+4));emit("Y_after",std::vector<float>(hY_after,hY_after+4));','spmvop_csr':'emit("Z",std::vector<double>(hZ_dev_result,hZ_dev_result+4));std::vector<double> migration_y(4);CHECK_CUDA(cudaMemcpy(migration_y.data(),dY,4*sizeof(double),cudaMemcpyDeviceToHost));emit("Y_after",migration_y);','spmm_csr_op':'emit("C",std::vector<float>(hC,hC+12));'}[k]
 s=s[:start]+'    int correct=1; // external independent CPU qualification determines support\n'+obs+'\n'+s[end:]
 s=s.replace('return EXIT_FAILURE;', 'throw std::runtime_error("native CUDA API/RTC failure");')
 if k in ['spmat_convert','spmv_symmetric_csr','spmvop_csr']:
  s=lic+'// CUDA compatibility mathematical baseline: installed SDK lacks original new API; failure preserved.\n#include "batch8_cuda_fallback.hpp"\nint main(){return migration_batch::sparse8_cuda_compatible("'+k+'");}\n'
 else:
  s=s.replace('const std::string migration_case=', 'std::setvbuf(stdout,nullptr,_IONBF,0);const std::string migration_case=')
 p=ROOT/'build/cuda-observed'/source;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
