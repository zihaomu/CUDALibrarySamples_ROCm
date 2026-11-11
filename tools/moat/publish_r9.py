#!/usr/bin/env python3
"""Update the catalog from the ten already sealed R9 qualifications."""
import json
from experiment import ROOT,write,digest
from audit import check
from selected_proofs import inspect
from qualify_r9 import helpers,crc_benchmark,load

def profile_identity(q,profile):
 kind='matrix-helper/'+profile['language']+'/'+profile['kind'] if profile else 'crc32-benchmark'
 implementation=profile['implementation'] if profile else 'rocm/ported/nvCOMP/benchmarks/benchmark_crc32.cpp'
 if q.get('kind')!=kind or q.get('implementation')!=implementation or q.get('implementation_sha256')!=digest(ROOT/implementation):raise ValueError('qualification source-language/profile identity')

def validate_qualification(q,sample,profile,review):
 directory=ROOT/q['evidence'];seal=json.loads((directory/'sealed.json').read_text())['files']
 mandatory={'qualification.json','manifest.json','source.json','validation.json'}
 if not mandatory<=set(seal) or check(directory):raise ValueError('unsealed composite qualification')
 profile_identity(q,profile)
 m=json.loads((directory/'manifest.json').read_text());sealed=json.loads((directory/'qualification.json').read_text())
 if any(q.get(k)!=v for k,v in sealed.items()) or m['backend']!='composite-qualification' or m['sample_id']!=sample['id'] or m['experiment_id']!=q['qualification_id'] or m['experiment_outcome']!='PASSED' or q['status']!='PASSED':raise ValueError('composite qualification identity')
 expected=profile['cases'] if profile else [c['case'] for c in json.loads((ROOT/'migration/rewrite/crc-benchmark-cases.json').read_text())]
 if q['case_ids']!=expected or q['case_count']!=len(expected) or len(expected)!=5 or not q['evidence_references'] or q['source_commit']!=review['source_commit']:raise ValueError('incomplete or unreviewed qualification contract')
 checks,refs,sources,build=helpers(profile,review) if profile else crc_benchmark(review)
 if not checks or not all(c['passed'] for c in checks) or q['checks']!=checks or set(q['evidence_references'])!=refs or q['dependencies']!=build['dependencies']:raise ValueError('qualification differs from recomputed complete proof')
 proposal=dict(sample,implementation=q['implementation'],selected_validation=q)
 inspected=inspect(proposal)
 if inspected['status']!='PASSED':raise ValueError('qualification publication/current closure '+str(inspected['errors']))

def main():
 groups=[json.loads((ROOT/'migration/reports'/name).read_text()) for name in ['rewrite-R9-helper-qualification.json','rewrite-R9-crc-benchmark-qualification.json']]
 if any(g['status']!='PASSED' for g in groups):raise ValueError('unqualified R9 group')
 rows=[r for g in groups for r in g['qualifications']];spec=json.loads((ROOT/'migration/rewrite/helpers-benchmark.json').read_text());expected={p['sample_id'] for p in spec['helpers']}|{'nvCOMP/benchmarks::benchmark_crc32.cpp'}
 if len(rows)!=10 or {r['sample_id'] for r in rows}!=expected:raise ValueError('R9 ten-entry denominator')
 catalog=json.loads((ROOT/'migration/samples.yaml').read_text());samples={s['id']:s for s in catalog['samples']}
 profiles={p['sample_id']:p for p in spec['helpers']}
 # Qualification and referenced seals must already have an immutable Git
 # publication. Validate every row before preparing any catalog mutation.
 for q in rows:
  profile=profiles.get(q['sample_id']);review=load('rewrite-R9-'+('helper' if profile else 'crc-benchmark')+'-review.json')
  validate_qualification(q,samples[q['sample_id']],profile,review)
 for q in rows:
  directory=ROOT/q['evidence'];sealed=json.loads((directory/'qualification.json').read_text())
  if check(directory) or any(q.get(k)!=v for k,v in sealed.items()) or not q['checks'] or not all(c['passed'] for c in q['checks']) or digest(ROOT/q['implementation'])!=q['implementation_sha256'] or any(digest(ROOT/n)!=h for n,h in q['dependencies'].items()):raise ValueError('invalid selected qualification '+q['sample_id'])
  s=samples[q['sample_id']];profile=profiles.get(q['sample_id']);helper=profile is not None;fortran=helper and profile['language']!='cpp';required=['rewrite/'+c for c in q['case_ids']]+['rewrite/negative-and-runtime','rewrite/sealed-build-and-native-identities','rewrite/independent-source-review']
  s.update(status='PASSED',level='L4',reason_code='VALIDATED_MOAT_REWRITE',required_cases=required,passed_cases=required,selected_validation=q,equivalence='PROJECT_DESCRIPTOR_ABI_WITH_HIP_STORAGE' if helper else 'PROJECT_HIP_CRC_WITH_ORIGINAL_BENCHMARK_HARNESS',actual_library='ProjectMatrixHelpers + HIP (host descriptors; real device storage/pointer tables)' if helper else 'HIP + hipRAND + project segmented IEEE CRC32/GPU GF2 search',backend_library='project host descriptor C ABI / real HIP buffers' if helper else 'project HIP segmented CRC/GF2 backend',reason=('9入口中的一个：真实C++/标准Fortran调用项目描述符C ABI，HIP分配/指针表与完整数据读回；5场景AMD/独立CPU/原生cuDSS API对照、生命周期/别名/故障和独立复审通过。仅描述符管理，不是GPU稀疏求解算法。' if helper else '保留原始CRC32 benchmark的CLI、默认storage、完整CSV网格及真实GPU配置搜索/最终重算；默认16GiB原规模、4个小场景、独立zlib、真实nvCOMP对照、故障/CLI/64位长度/trace/replay及独立复审通过。默认RNG序列不跨库逐位比较；性能与完整32GiB complete扫描未验收。'),cuda_comparison='PASSED',cuda_comparison_mode='NATIVE_CUDSS_API_COUNTERPART' if fortran else 'NATIVE_CUDSS_ORIGINAL_PLUS_API_COUNTERPART' if helper else 'NATIVE_NVCOMP_ORIGINAL_HARNESS',cuda_comparison_reason=('原始CUDA Fortran工具链仍BLOCKED；同输入native cuDSS C++ API对照通过，AMD侧实际执行标准Fortran。' if fortran else '原始CUDA C++程序及同输入native cuDSS API对照通过。' if helper else '四个冻结小输入同字节三方；默认各自实际RNG输入在各GPU运行后独立CPU校验。'),retry_condition='扩展API/精度/布局/设备或性能声明时重新冻结合同并完成实际GPU与独立参考验收。',next_step='本批登记范围已通过；其它cuDSS属性/前端与nvCOMP NVBENCH框架保持单列。',benchmark='NOT_QUALIFIED',active_batch='R9',reproduce=('python3 tools/moat/build_helpers.py\npython3 tools/moat/run_helpers.py' if helper else 'python3 tools/moat/build_crc_benchmark.py\npython3 tools/moat/run_crc_benchmark.py'))
  if not fortran:s['cuda_baseline']='PASSED'
  if fortran:s['cuda_baseline']='BLOCKED';s['cuda_baseline_reason']='5090主机无nvfortran/gfortran/flang原语言工具链；兼容native C++ cuDSS API对照不替代原Fortran编译器。'
  for ref in ['migration/reports/rewrite-R9.md',q['evidence'],*q['evidence_references']]:
   if ref not in s['evidence']:s['evidence'].append(ref)
  if not any(a.get('qualification_id')==q['qualification_id'] for a in s['attempts']):s['attempts'].append(q)
 write(ROOT/'migration/samples.yaml',catalog)
 libs=json.loads((ROOT/'migration/libraries.json').read_text());libs['libraries']=[r for r in libs['libraries'] if r['id']!='ProjectMatrixHelpers'];build=json.loads((ROOT/'migration/reports/rewrite-R9-helper-build.json').read_text());libs['libraries'].append(dict(id='ProjectMatrixHelpers',version='R9',status='QUALIFIED_SCOPED',qualified_samples=sorted(q['sample_id'] for q in rows if q['kind'].startswith('matrix-helper/')),source_dependencies=build['dependencies'],shared_library_sha256=build['shared_library_sha256'],observation_scope='Host-only narrow descriptor ABI, caller-owned host shape arrays and real HIP GPU storage/pointer tables. No numerical GPU sparse-solver or native cuDSS binary ABI claim.'))
 write(ROOT/'migration/libraries.json',libs);print('Published ten scoped R9 qualifications')
if __name__=='__main__':main()
