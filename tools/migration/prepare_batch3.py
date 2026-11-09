#!/usr/bin/env python3
"""Instrument the eight profiles without modifying immutable upstream sources."""
import json, pathlib, re, shutil
from catalog import ROOT
from batch3_spec import ALL, SPARSE, SOLVER

def emit(name, ptr, n):
    return f'migration_observer::emit("{name}",{ptr},{n});\n'

for source in ALL:
    for backend in ['rocm', 'cuda']:
        p = ROOT / ('rocm/ported' if backend == 'rocm' else 'build/cuda-observed') / source
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / source, p)
        text = p.read_text()
        if 'MIGRATION_BATCH3' in text:
            continue
        runtime = 'hip' if backend == 'rocm' else 'cuda'
        kind = pathlib.PurePosixPath(source).parent.name
        text = '#include "observe.hpp"\n#include "binary_observe.hpp"\n#include <string>\n#include <vector>\n#include <cstdlib>\n' + text
        start = text.index('{', text.index('int main')) + 1
        text = text[:start] + '\n// MIGRATION_BATCH3: preserve original GPU mathematical calls.\nconst std::string migration_case=std::getenv("MIGRATION_CASE")?std::getenv("MIGRATION_CASE"):"original";\n' + text[start:]
        if kind in ['cg', 'bicgstab']:
            text = text.replace('int grid = 700;', 'const char* mc=std::getenv("MIGRATION_CASE");\n    int grid = mc && std::string(mc)=="small-varied"?23:mc && std::string(mc)=="nonzero-initial"?31:700;')
            text = text.replace('h_X[i] = 1.0;', 'h_X[i] = migration_case=="original"?1.0:1.0+double(i%17-8)/16.0;')
            marker = '    // ### Device memory management ###'
            code = '''migration_binary::emit("input_rows.bin",h_A_rows,(m+1)*sizeof(int));
migration_binary::emit("input_columns.bin",h_A_columns,nnz*sizeof(int));
migration_binary::emit("input_values.bin",h_A_values,nnz*sizeof(double));
migration_binary::emit("input_manufactured.bin",h_X,m*sizeof(double));
'''
            code += emit('input_tolerance', '&tolerance', '1') + emit('input_max_iterations', '&maxIterations', '1')
            text = text.replace(marker, code + marker, 1)
            marker = f'    CHECK_CUDA( {runtime}Memset(d_X.ptr, 0x0, m * sizeof(double)) )'
            code = f'''std::vector<double> migration_rhs(m),migration_initial(m,0.0);
CHECK_CUDA({runtime}Memcpy(migration_rhs.data(),d_B.ptr,m*sizeof(double),{runtime}MemcpyDeviceToHost))
migration_binary::emit("generated_rhs.bin",migration_rhs.data(),m*sizeof(double));
if(const char* fixture=std::getenv("MIGRATION_INPUT_FIXTURE_DIR")){{
 std::ifstream f(std::string(fixture)+"/input_rhs.bin",std::ios::binary);
 f.read(reinterpret_cast<char*>(migration_rhs.data()),m*sizeof(double));
 if(!f || f.peek()!=std::ifstream::traits_type::eof())return EXIT_FAILURE;
 CHECK_CUDA({runtime}Memcpy(d_B.ptr,migration_rhs.data(),m*sizeof(double),{runtime}MemcpyHostToDevice))
}}
if(migration_case=="nonzero-initial")for(int i=0;i<m;++i)migration_initial[i]=0.125+double(i%7)/64.;
CHECK_CUDA({runtime}Memcpy(d_X.ptr,migration_initial.data(),m*sizeof(double),{runtime}MemcpyHostToDevice))
migration_binary::emit("input_rhs.bin",migration_rhs.data(),m*sizeof(double));
migration_binary::emit("input_initial.bin",migration_initial.data(),m*sizeof(double));
'''
            assert marker in text, source
            text = text.replace(marker, code, 1)
            text = text.replace('    double threshold = tolerance * nrm_R;', '    double threshold = tolerance * nrm_R;\n' + emit('initial_residual', '&nrm_R', '1') + emit('threshold', '&threshold', '1') + 'int migration_iterations=0;')
            text = text.replace('        printf("  Iteration = %d; Error Norm = %e\\n", i, nrm_R);', '        ++migration_iterations;\n        printf("  Iteration = %d; Error Norm = %e\\n", i, nrm_R);')
            marker = '    printf("Final error norm = %e\\n", nrm_R);'
            assert marker in text
            text = text.replace(marker, marker + '\n' + emit('final_residual', '&nrm_R', '1') + emit('iterations', '&migration_iterations', '1'))
            # Propagate nested routine failures instead of discarding return codes.
            func = 'gpu_CG' if kind == 'cg' else 'gpu_BiCGStab'
            text = text.replace('    ' + func + '(cublasHandle,', '    if(' + func + '(cublasHandle,', 1)
            text = text.replace('d_tmp, d_bufferMV, maxIterations, tolerance);', 'd_tmp, d_bufferMV, maxIterations, tolerance)!=EXIT_SUCCESS)return EXIT_FAILURE;', 1)
            marker = '    // ### Free resources ###'
            code = f'''std::vector<double> migration_solution(m);
CHECK_CUDA({runtime}Memcpy(migration_solution.data(),d_X.ptr,m*sizeof(double),{runtime}MemcpyDeviceToHost))
migration_binary::emit("solution.bin",migration_solution.data(),m*sizeof(double));
'''
            text = text.replace(marker, code + marker, 1)
        elif kind == 'gpsvInterleavedBatch':
            marker = '    // step 1: allocate device memory'
            code = '''if(migration_case=="changed-rhs")for(int i=0;i<full_size;++i)h_B[i]=(i%2?-1.f:1.f)*(i+0.5f);
if(migration_case=="diagonal-dominant")for(int i=0;i<full_size;++i){h_M[i]=100.f+i;h_B[i]=float(i-3);}
'''
            for name in ['S','L','M','U','W','B']:
                code += emit('input_' + name, 'h_' + name, 'full_size')
            text = text.replace(marker, code + marker, 1)
            marker = '    // step 6: solve Aj*xj = bj'
            code = 'std::vector<float> migration_interleaved(full_size);\n'
            for name in ['S','L','M','U','W','X']:
                code += f'CHECK_CUDA({runtime}Memcpy(migration_interleaved.data(),d_{name},full_size*sizeof(float),{runtime}MemcpyDeviceToHost))\n'
                code += emit('interleaved_' + name, 'migration_interleaved.data()', 'full_size')
            text = text.replace(marker, code + marker, 1)
            marker = '    // step 7: convert h_X back to aggregate format'
            code = f'CHECK_CUDA({runtime}Memcpy(migration_interleaved.data(),d_X,full_size*sizeof(float),{runtime}MemcpyDeviceToHost))\n' + emit('solution_interleaved', 'migration_interleaved.data()', 'full_size')
            text = text.replace(marker, code + marker, 1)
            text = text.replace('    // step 9: Check results', emit('solution', 'h_X', 'full_size') + '    // step 9: Check results', 1)
        elif source in SOLVER:
            # CUDA copies from the initial inventory may lack observers.
            if 'MIGRATION_OBSERVE_ORIGINAL' not in text:
                names = {'gesvdjBatched':['A','U','V','S','info'], 'syevjBatched':['A','V','W','info'], 'syevdx':['A','V','W'], 'sygvdx':['A','B','V','W']}[kind]
                code = '// MIGRATION_OBSERVE_ORIGINAL\n' + ''.join(emit(n, n+'.data()', n+'.size()') for n in names)
                marker = '/* free resources */'
                assert marker in text, source
                text = text.replace(marker, code + marker, 1)
            if kind in ['gesvdjBatched','syevjBatched']:
                marker = '    /* step 1: create cusolver/cublas handle, bind a stream */'
                # Insert immediately before copying the fully constructed input.
                marker = '    CUDA_CHECK(' + runtime + 'Malloc(reinterpret_cast<void **>(&d_A)'
                pos = text.index(marker)
                if kind == 'gesvdjBatched':
                    code = '''if(migration_case=="perturbed")for(size_t i=0;i<A.size();++i)A[i]+=double(int(i%5)-2)/8.;
if(migration_case=="rank-deficient")for(int b=0;b<batchSize;++b)for(int i=0;i<m;++i)A[b*lda*n+lda+i]=2*A[b*lda*n+i];
'''
                else:
                    text = text.replace('const int sort_eig = 0;', 'const int sort_eig = migration_case=="sorted"?1:0;')
                    pos = text.index(marker)
                    code = '''if(migration_case=="perturbed")for(int b=0;b<batchSize;++b){for(int i=0;i<m;++i)A[b*m*m+i*m+i]+=0.125*(b+i+1);A[b*m*m+2]=A[b*m*m+6]=0.375;}
'''
                text = text[:pos] + code + emit('input_A', 'A.data()', 'A.size()') + text[pos:]
            else:
                pref = 'HIPSOLVER' if backend == 'rocm' else 'CUSOLVER'
                marker = '    /* step 2: query working space'
                # The range has to be configured before both workspace query and solve.
                match = re.search(r'    (?:hipsolver|cusolver)EigRange_t range = .*?;', text)
                assert match, source
                code = f'''\nif(migration_case=="value-range"){{range={pref}_EIG_RANGE_V;vl={2.5 if kind=='syevdx' else 0.2};vu={4.5 if kind=='syevdx' else 0.7};}}
if(migration_case=="all-range")range={pref}_EIG_RANGE_ALL;
if(migration_case=="empty-range"){{range={pref}_EIG_RANGE_V;vl=10.;vu=11.;}}
'''
                # Actual enum spelling is RANGE_ALL in hipSOLVER and CUDA.
                text = text[:match.end()] + code + text[match.end():]
                # Do not inspect unreturned eigenvalues/columns; range references live in CPU oracle.
                begin = text.index('    std::printf("eigenvalue =')
                end = text.index('// MIGRATION_OBSERVE_ORIGINAL', begin)
                text = text[:begin] + '''    std::printf("Eigenvalues found = %d\\n",h_meig);
    for(int i=0;i<h_meig;++i)std::printf("W[%d] = %.17g\\n",i,W[i]);
    print_matrix(m,h_meig,V.data(),lda);
''' + text[end:]
                text = re.sub(r'emit\("W",W.data\(\),W.size\(\)\)', 'emit("W",W.data(),h_meig)', text)
                text = re.sub(r'emit\("V",V.data\(\),V.size\(\)\)', 'emit("V",V.data(),m*h_meig)', text)
                marker = '/* free resources */'
                code = ''.join(emit(n, '&'+v, '1') for n,v in [('info','info'),('meig','h_meig'),('input_il','il'),('input_iu','iu'),('input_vl','vl'),('input_vu','vu')])
                code += emit('input_A', 'A.data()', 'A.size()')
                if kind == 'sygvdx': code += emit('input_B','B.data()','B.size()')
                text = text.replace(marker, code + marker, 1)
        else:
            # Graph adaptation is installed separately from the preserved upstream prefix.
            continue
        p.write_text(text)

shutil.copytree(ROOT/'cuSOLVER/utils', ROOT/'build/cuda-observed/cuSOLVER/utils', dirs_exist_ok=True)
(ROOT/'migration/batch3.json').write_text(json.dumps({'samples':[{'source':s,'required_cases':c,'initial_status':'PARTIAL'} for s,c in ALL.items()], 'scope':'Sparse 3, solver 4, genuine SpVV capture/replay 1; 26 predeclared input cases'},indent=2)+'\n')
print('Prepared batch 3 sparse and solver observation copies')
