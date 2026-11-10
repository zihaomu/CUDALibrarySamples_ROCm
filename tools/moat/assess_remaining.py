#!/usr/bin/env python3
"""Publish per-entry research dispositions; never issue sample qualifications."""
import collections,json,re
from experiment import ROOT,digest,write

REPORT=ROOT/'migration/reports'
def route(s):
    f,p=s['family'],s['source'];low=p.lower()
    # Each recommendation is coupled below to this entry's original source hash,
    # API tokens, missing cases and actual failed attempt, rather than declaring
    # that a related ecosystem library implements the whole vendor contract.
    if s['status']=='PARTIAL':
        if 'Xgeev' in p:return ('GPU_EIGENSOLVER_REQUIRED','rocSOLVER/custom HIP Hessenberg + QR eigenvectors','Current Xgeev numerical work falls back to CPU OpenBLAS; residual BLAS/copy kernels are not the eigen-decomposition.','Trace actual GPU Hessenberg/QR/eigenvector stages and check complex pairs, residual and normalization against LAPACK/native CUDA.','XL')
        if 'simple_reordering_phase' in p:return ('VENDOR_POLICY_IDENTITY','Shared HIP sparse C ABI + optional METIS policy adapter','Full GPU factor/solve restored; project minimum-degree permutation differs from the exact METIS permutation asserted by original C++ entry.','Use pinned METIS options/version and test exact original permutation plus factor/solve; no hardcoded permutation.','M')
        if any(x in low for x in ['jpeg','canny','flood']):return ('PIXEL_OR_CODEC_CONTRACT','rocJPEG / RPP / project HIP with per-pixel reference',s['reason'],'Replay original image files, ROI/borders/stride/colorspace and native pixel outputs; isolate codec metadata and GPU pixel work.','L')
        if any(x in low for x in ['rand','normal','lognormal']):return ('RNG_SEQUENCE_CONTRACT','rocRAND device API or explicitly implemented CUDA sequence','A matching distribution does not establish the original generator state/offset/bit sequence.','Freeze native sequences and state progression; verify exact integers plus normal/lognormal transform and skip-ahead edge cases.','L')
        if any(x in low for x in ['get_set','bench','query']):return ('QUERY_OR_HARNESS_CONTRACT','Existing project HIP core + original API/harness adapter',s['reason'],'Exercise original CLI/query attributes/repeated execution; assert returned metadata affects actual computation.','M')
        return ('DESCRIPTOR_OR_EXECUTION_CONTRACT','Existing HIP core + MPI/RCCL descriptor adapter',s['reason'],'Freeze exact original offsets, process grid, dtype, seed and data; test gather/scatter, distinct physical GPUs and untouched padding.','L')
    if f.startswith('MathDx/'):
        kind=f.split('/')[-1]
        if kind=='libmathdx':return ('JIT_SOURCE_REGENERATION','HIPRTC + HIP module API + project device libraries','Vendor generator headers/ABI and NVIDIA cubin/PTX cannot be loaded as AMD HSACO; actual HIPRTC compile/load/launch pilot passes.','Regenerate AMD source for this original generator/options; compare generated GPU result and execute error/recompile paths.','XL')
        lib={'cuBLASDx':'HIP cooperative device GEMM / rocWMMA after arch probe','cuFFTDx':'HIP device FFT (radix/butterfly) with original fusion','cuSolverDx':'Project HIP device factor/solve / BLAS','cuRANDDx':'rocRAND device API + sequence adapter','nvCOMPDx':'Project device codec or a verified hipCOMP device API'}[kind]
        gate={'cuBLASDx':'device-callable precision/layout, block cooperation, pipeline and fused epilogue','cuFFTDx':'device-callable FFT length/type, shared memory, fusion and synchronization','cuSolverDx':'device-callable pivots, info, dtype, batch and synchronization','cuRANDDx':'generator state, sequence/offset, exact integer or original distribution contract','nvCOMPDx':'device-callable encode/decode, chunk format, bound and cross-vendor bitstream'}[kind]
        return ('DEVICE_ALGORITHM_REWRITE',lib,'Original vendor-only header is absent from locked AMD SDK; a host library call does not meet '+gate+'.','Implement '+gate+' for the original entry; independent CPU/native oracle plus real enclosing HIP kernel trace.','XL' if kind in ['cuFFTDx','nvCOMPDx'] else 'L')
    if f=='cuEST':return ('QUANTUM_CHEMISTRY_COMPONENT_REWRITE','LibintX (integrals), GauXC (XC), QUICK (selected HF/DFT); all candidates','cuEST object/plan ABI is absent; candidate HIP components do not cover the complete ECP/PCM/VV10/range-separated/gradient surface.','Build pinned candidate dependencies in the locked profile; implement only this entry’s operator/basis/gradient and compare native cuEST plus independent molecular reference.','XL')
    if f=='cuPQC':return ('CRYPTOGRAPHIC_ALGORITHM_REWRITE','Project HIP Keccak/NTT/field arithmetic + independent standards reference','CUDA cuPQC/cuhash ABI is absent. Self round-trip or random output is insufficient evidence for ML-KEM/ML-DSA/Poseidon2/Merkle.','Freeze source algorithm parameters; official KAT and malformed-input rejection, exact wire encoding/NTT/field arithmetic, then GPU traces.','XL')
    if f in ['cuBLASMp','cuSOLVERMp','cuFFTMp','cuTENSORMp','cuTENSORMg'] or '/Mg' in p:
        lib='MPI + RCCL + '+('hipFFT/rocFFT' if 'FFT' in f else 'hipSOLVER/rocSOLVER' if 'SOLVER' in f else 'hipBLAS/hipTensor')+' + HIP redistribution'
        return ('DISTRIBUTED_DESCRIPTOR_REWRITE',lib,'Vendor distributed headers/descriptors are absent. Two-device GEMM+AllGather pilot proves only local communication, not this entry’s global algorithm.','Rebuild the original process grid/submatrix/decomposition; two physical GPU and MPI-rank tests, CPU global oracle, and separate multi-node validation if required.','XL')
    if f in ['nvJPEG2000','nvTIFF','nvJPEG']:
        if f=='nvJPEG2000':return ('GPU_JPEG2000_CODEC_REWRITE','Project HIP DWT + tier-1/2 arithmetic codec (research)','rocJPEG actual parser rejects JP2; it is a JPEG codec. No JP2 GPU codec was qualified in the locked SDK.','Implement original lossless/lossy, bit depth, ROI/tile and encode/decode direction; CPU OpenJPEG/native comparison and cross-decode bitstreams.','XL')
        if f=='nvTIFF':return ('TIFF_CONTAINER_AND_GPU_CODEC','hipCIM JPEG-tile reader candidate + project metadata/encoder','hipCIM documents JPEG TIFF tile GPU decode; other compression may run on CPU. This is not a full nvTIFF GPU encode/decode/GeoTIFF replacement; not installed here.','Build compatible pinned hipCIM without replacing ROCm lock; test this entry’s compression/tiles/metadata/direction, verify GPU codec trace and independent TIFF decode.','XL')
        return ('JPEG_FRAMEWORK_REWRITE','rocJPEG + explicit host metadata/filesystem adapter','Vendor CUDA JPEG framework/API remains unmigrated; supported pixel or format subsets do not qualify its full original harness.','Run original files and CLI, all pixel formats/strides/batching plus malformed streams, reference pixels and actual GPU decode trace.','L')
    if f in ['cuBLAS','cuBLASLt']:
        if 'GreenContext' in p:return ('HARDWARE_RESOURCE_POLICY','HIP stream/queue adaptation (numeric subset only)','CUDA green-context SM partition/resource identity has no demonstrated equivalent in this locked AMD profile.','Specify measurable AMD queue/resource isolation semantics; original mathematical GEMM alone cannot qualify the resource-policy sample.','XL')
        if '/Emulation/' in p or 'Emulated' in p:return ('EMULATION_ALGORITHM_CONTRACT','Project HIP mantissa splitting + hipBLAS/GEMM accumulation','Vendor emulation controls and BF16x9/fixed/dynamic Ozaki-style policies are not equivalent to one normal GEMM.','Port original selection/scaling/split and accumulator rules; grade difficult dynamic-range inputs and original policy queries against native.','L')
        return ('LOW_PRECISION_LAYOUT_OR_SEARCH','hipBLASLt after exact dtype/scale probe + HIP pack/dequantize fallback','Original low-precision block/MX/NV scale layout or preset/custom-search ABI has no qualified adapter; FP32 GEMM alone loses the contract.','Read original scale encoding/grouping/rounding/search; exact pack/dequantize edge tests, CPU and native CUDA output plus actual chosen GPU kernels.','L')
    if f in ['cuDSS','cuSOLVERSp2cuDSS']:
        return ('SPARSE_PHASE_AND_BINDING','Shared HIP sparse C ABI + symbolic analysis / optional external sparse library','Only audited small-matrix subsets are qualified. This entry’s sparse matrix type, phase, configuration, batching or distributed/frontend contract is unimplemented.','Bind original language only after its GPU core works; replay original CSR/type/phase/refactor/error behavior and scalable sparse storage, residual oracle and factor/solve trace.','L')
    if f=='cuSOLVER':return ('SOLVER_ALGORITHM_OR_PRECISION','hipSOLVER/rocSOLVER where available + explicit HIP algorithm','Exact original QR/IRS/randomized SVD/generic eigensolver expert API is missing or not yet migrated; numeric substitutes need algorithm/precision qualification.','Probe this entry’s actual API, workspace, rank/convergence/info and precision; preserve original dimensions and independently validate residual/orthogonality/refinement.','L')
    if f=='nvCOMP':return ('CODEC_BITSTREAM_OR_FRAMEWORK','hipCOMP for verified codec APIs + project GPU codec/harness','Codec availability does not establish this sample’s direction, native bitstream, host/device invocation, options or benchmark framework.','Probe exact source codec/options; test encode/decode separately, cross-vendor streams, chunk bounds, malformed input and original CLI/GPU work.','L')
    if f=='nvMatmulHeuristics':return ('HEURISTIC_MODEL_AND_FRONTEND','hipBLASLt measured algorithm enumeration + project result schema','NVIDIA model scores/algorithm IDs are vendor-specific; no AMD cost model or original-language adapter has been qualified.','Implement AMD-specific measured recommendations for original shapes; run chosen algorithm, validate output and report model/ranking scope without claiming identical NVIDIA IDs.','L')
    if f in ['NPP','NPP+']:return ('IMAGE_KERNEL_OR_FRONTEND','RPP where exact API matches; project HIP + CPU file/metadata adapter','This original image algorithm or Python frontend is still unmigrated; available image primitives do not establish its pixel/border/ROI contract.','Implement exact source operation, dtype/channel/ROI/border/stride and original image CLI; independent native pixels plus GPU trace and invalid input.','L')
    if f=='cuTENSOR':return ('TENSOR_DESCRIPTOR_OR_BINDING','hipTensor / hipBLAS + HIP layout and original-language adapter','Generic tensor operation availability does not cover this entry’s descriptor, contraction options, plan or binding.','Probe original dtype/modes/strides/plan; independent CPU contraction, native CUDA and real entry ownership/error checks.','L')
    if f=='cuSPARSE':return ('SPARSE_API_ADAPTER','hipSPARSE/rocSPARSE + HIP format conversion','The source sparse API or its exact descriptor/algorithm contract has not been implemented.','Probe original index widths/base/layout and operation; independent CSR/dense oracle, native CUDA plus error/empty/batch checks.','M')
    raise ValueError('Unclassified entry: '+p)

def main():
    cat=json.loads((ROOT/'migration/samples.yaml').read_text());tasks=json.loads((ROOT/'migration/moat/tasks.json').read_text());by={t['sample_id']:t for t in tasks['tasks']}
    report=[]
    for s in cat['samples']:
        t=by[s['id']]
        if s['status']=='PASSED':continue
        code,library,why,probe,cost=route(s)
        if s['source']=='cuDSS/simple_reordering_phase/simple_reordering_phase.cpp':
            t['previous_primary_phase']=t['primary_phase'];t['primary_phase']='R5';t['scope_addendum']='Legacy C++ false-pass repair; additional to original 73 frontend entries'
            if t.get('selected_validation',{}):t['historical_selected_validation']=t.pop('selected_validation')
        retry=probe+' Complete frozen original contract, independent review and immutable qualification before changing support status.'
        row=dict(sample_id=s['id'],source=s['source'],source_sha256=digest(ROOT/s['source']),phase=t['primary_phase'],current_status=s['status'],
            disposition=code,candidate_route=library,blocking_reason=why,first_observed_failure=s['reason'],
            original_api_tokens=s.get('original_semantics',{}).get('api_tokens',[]),required_cases=s['required_cases'],missing_cases=sorted(set(s['required_cases'])-set(s['passed_cases'])),
            original_contract=s.get('original_semantics'),cost_class=cost,minimum_next_experiment=probe,retry_condition=retry,
            evidence=s['evidence'],qualification='NOT_QUALIFIED',assessment_scope='Source and recorded failure review; no new GPU sample execution or qualification')
        report.append(row)
        t.update(state='ASSESSED_GAP_REMAINS',assessment='migration/reports/rewrite-remaining-assessment.json',disposition=code,candidate_route=library,
                 current_reason=s['reason'],retry_condition=retry,prerequisites=[probe],cost_class=cost,source_sha256=row['source_sha256'])
    assert len(report)==len(cat['samples'])-sum(s['status']=='PASSED' for s in cat['samples'])
    tasks['phase_counts']=dict(collections.Counter(t['primary_phase'] for t in tasks['tasks']));write(ROOT/'migration/moat/tasks.json',tasks)
    summary=dict(schema_version=1,status='ASSESSMENT_COMPLETE_PORTS_PENDING',samples=len(report),by_phase=dict(collections.Counter(r['phase'] for r in report)),by_disposition=dict(collections.Counter(r['disposition'] for r in report)),
                 cost_legend={'M':'Estimated several focused days','L':'Estimated one to several weeks','XL':'Research project / multiple weeks or longer; not a delivery commitment'},rows=report)
    write(REPORT/'rewrite-remaining-assessment.json',summary)
    lines=['# 未通过入口：逐项路线与恢复条件','',f'当前 {len(report)} 个入口尚未整例通过。此表记录源码/历史失败评估；候选库和基础探针不计入支持数。','',
           'M/L/XL 是粗略工程量级（数日／一至数周／专题研究），不承诺日期。原始合同及逐例失败保留在详情页与 JSON。','',
           '| 阶段 | 未通过入口 |','| --- | ---: |']+[f'| {k} | {v} |' for k,v in sorted(summary['by_phase'].items())]
    lines+=['','| 原始入口 / 当前状态 | 路线与未支持原因 | 最小后续实验 / 成本 |','| --- | --- | --- |']
    for r in report:
        page='../sample-reports/'+r['source']+'.md'
        escape=lambda x:str(x).replace('|',' / ').replace('\n',' ')
        lines.append(f'| [{r["source"]}]({page})<br>{r["current_status"]} / {r["phase"]} | {escape(r["candidate_route"])}<br>{escape(r["blocking_reason"])} | {escape(r["minimum_next_experiment"])}<br>{r["cost_class"]} |')
    (REPORT/'rewrite-remaining-assessment.md').write_text('\n'.join(lines)+'\n')
    routes=json.loads((ROOT/'migration/backend-routes.json').read_text());pending={r['sample_id']:r for r in report}
    for r in routes['routes']:
        if r['sample_id'] in pending:
            a=pending[r['sample_id']];r.update(candidate_rewrite=a['candidate_route'],retry_condition=a['retry_condition'],cost_class=a['cost_class'],assessment=a['disposition'])
    write(ROOT/'migration/backend-routes.json',routes)
    libraries=json.loads((ROOT/'migration/libraries.json').read_text());pins=json.loads((REPORT/'rewrite-R6-candidate-sources.json').read_text())
    for p in pins['candidates']:
        name=p['name'];existing=next((r for r in libraries['libraries'] if r['id']==name),None)
        row=dict(id=name,version=p.get('commit'),status='SOURCE_REVIEWED_NOT_GPU_QUALIFIED',qualified_samples=[],upstream=p['repository'],license=p['license_spdx'],
                 source_pin=p['commit'],source_evidence=p['evidence'],observation_scope=p['scope'],runtime_path=None)
        if existing:existing.update(row)
        else:libraries['libraries'].append(row)
    write(ROOT/'migration/libraries.json',libraries)
    print(json.dumps({k:v for k,v in summary.items() if k!='rows'}))
if __name__=='__main__':main()
