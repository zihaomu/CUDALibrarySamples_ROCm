#!/usr/bin/env python3
"""Bind watershed proofs to their frozen contract, actual vendor, layout and build."""
import hashlib,json,shlex,tarfile
from experiment import ROOT,digest
from image_encoder_math_binding import sealed
from image_watershed_v2_reference import bound
CONTRACT=ROOT/'migration/rewrite/image-watershed-completion-contract.json'
SPEC=ROOT/'migration/rewrite/image-watershed-completion-spec-v1.json'
FOLDER=ROOT/'migration/fixtures/image-watershed-completion'
NATIVE=ROOT/'rocm/probes/image/watershed_completion_native.cpp'
BUILD=ROOT/'migration/reports/image-watershed-v2-build.json'

def need(condition,message):
    if not condition:raise ValueError(message)

def contract():
    row=json.loads(CONTRACT.read_text());proof=sealed(row,'contract.json');spec=json.loads(SPEC.read_text())
    need({k:v for k,v in row.items() if k!='evidence'}==spec,'frozen specification identity')
    need(row['status']=='FROZEN' and row['algorithm_id']=='strict-descent-directed-terminal-reachability-v1','contract status/algorithm')
    need(len(row['inputs'])==60 and len({i['id'] for i in row['inputs']})==60,'complete unique input inventory')
    expected=''.join(f'{i["id"]} {i["width"]} {i["height"]}\n' for i in row['inputs'])
    need((FOLDER/'cases.txt').read_text()==expected,'frozen input list identity')
    for item in row['inputs']:
        path=ROOT/item['path'];need(path.stat().st_size==item['bytes']==item['width']*item['height'] and digest(path)==item['sha256'],'frozen raw input '+item['id'])
    return row

def build(row=None):
    row=json.loads(BUILD.read_text()) if row is None else row;proof=sealed(row,'build.json')
    need(row['status']=='BUILT' and row['return_code']==0,'successful AMD build required')
    need(set(row['dependencies'])=={'rocm/common/image/watershed_v2.hpp','rocm/probes/image/watershed_v2_probe.cpp'},'compiled dependency inventory')
    for name,sha in row['dependencies'].items():need(digest(ROOT/name)==sha,'current compiled dependency '+name)
    binary=ROOT/row['binary']['path'];need(digest(binary)==row['binary']['sha256'],'current AMD executable SHA')
    commands=json.loads((proof/'commands.json').read_text());need(len(commands)==1 and commands[0]['return_code']==0,'AMD build command identity')
    argv=commands[0]['argv'];need('--offload-arch=gfx1201' in argv and str(ROOT/'rocm/probes/image/watershed_v2_probe.cpp') in argv and argv[-2:]==['-o',str(binary)],'actual AMD compiler target/source/output')
    return row

def runtime(row,key,backend):
    need(row.get('key')==key,'run key/layout/vendor mismatch')
    need(row.get('status')=='EXECUTED' and row.get('return_code')==0,'successful run required')
    need(row.get('contract_sha256')==digest(CONTRACT),'run contract digest mismatch')
    proof=sealed(row);manifest=json.loads((proof/'manifest.json').read_text());source=json.loads((proof/'source.json').read_text())
    need(manifest['backend']==backend and manifest['experiment_outcome']=='EXECUTED','actual recorded backend/outcome')
    need(source['dependencies'].get(str(CONTRACT.relative_to(ROOT)))==digest(CONTRACT),'run source contract binding')
    need(source['dependencies'].get(str((FOLDER/'cases.txt').relative_to(ROOT)))==digest(FOLDER/'cases.txt'),'run input-list binding')
    p=json.loads(CONTRACT.read_text())
    for item in p['inputs']:need(source['dependencies'].get(item['path'])==item['sha256'],'run input snapshot '+item['id'])
    need(row['output_dir']==manifest['raw_artifact_dir']+'/outputs','run output directory identity')
    commands=json.loads((proof/'commands.json').read_text());need(commands and all(c['return_code']==0 for c in commands),'all actual commands succeeded')
    return proof,source,commands

def amd(row,mode,b):
    proof,source,commands=runtime(row,'AMD-'+mode,'rocm');binary=ROOT/b['binary']['path']
    need(row['build_evidence']==b['evidence'] and row['binary_sha256']==b['binary']['sha256'],'AMD run build/binary mismatch')
    need(source['dependencies'].get(str(BUILD.relative_to(ROOT)))==digest(BUILD),'AMD source build receipt binding')
    for name,sha in b['dependencies'].items():need(source['dependencies'].get(name)==sha,'AMD run compiled source binding '+name)
    need(source['dependencies'].get(b['binary']['path'])==b['binary']['sha256'],'AMD captured executable binding')
    need(len(commands)==1,'one exact AMD corpus command')
    command=commands[0];need(command['phase']=='frozen-AMD-corpus' and command['argv']==[str(binary),str(FOLDER),str(ROOT/row['output_dir']),mode],'actual AMD executable/input/layout command')
    observed=json.loads((proof/'backend.observed.json').read_text());need(observed['rocm_release']=='10.1.0' and observed['packages']['rocm-sdk-core']=='10.1.0','actual ROCm 10.1 environment')
    need(len(observed['devices'])==1 and observed['devices'][0]['physical_id']==1 and observed['devices'][0]['pci_bdf']=='0000:23:00.0','actual allowed AMD physical device')
    log=(proof/command['stdout']).read_text();need('arch=gfx1201 PCI=0000:23:00.0' in log,'actual AMD probe device')
    lines=[s for s in log.splitlines() if s.startswith('RESULT ')];p=json.loads(CONTRACT.read_text())
    expected=[f'RESULT {i["id"]} pixels={i["bytes"]} products={5 if mode=="no-labels" else 7} padding=1 mode={mode}' for i in p['inputs']]
    need(lines==expected,'actual AMD layout/padding/input receipt')
    return bound(row)

def native(row,vendor):
    need(row.get('vendor')==vendor,'native vendor mismatch')
    proof,source,commands=runtime(row,'native-'+vendor,'cuda');remote=row['remote'];selected=[c for c in commands if c['phase']=='frozen-native-corpus'];need(len(selected)==1,'one actual native command');command=selected[0]
    need(command['argv'][:2]==['ssh','nvidia-5090x2'] and shlex.split(command['argv'][-1])==['env','CUDA_VISIBLE_DEVICES=1',remote+'/probe',remote+'/inputs',remote+'/outputs'],'actual native host/device/input command')
    compile_command=next(c for c in commands if c['phase']=='build');argv=shlex.split(compile_command['argv'][-1]);need(('-DIMAGE_NPP_PLUS' in argv)==(vendor=='NPPPlus'),'actual native SDK compile selection')
    need(argv[0]=='/usr/local/cuda-13.4/bin/nvcc' and '-arch=sm_120' in argv and remote+'/probe.cpp' in argv and argv[argv.index('-o')+1]==remote+'/probe','actual native compiler/source/output')
    need(source['dependencies'].get(str(NATIVE.relative_to(ROOT)))==digest(NATIVE),'actual native probe source binding')
    log=(proof/command['stdout']).read_text();version='12.4.0' if vendor=='NPPPlus' else '13.2.0';need('PCI 0000:E1:00.0 NPP '+version in log,'actual NVIDIA GPU and SDK version')
    identity=next(c for c in commands if c['phase']=='binary-and-loaded-library-identity');text=(proof/identity['stdout']).read_text();libraries=json.loads(text[text.index('{'):]);need(remote+'/probe' in libraries,'actual native binary identity')
    needle='libnpp_plus_if.so' if vendor=='NPPPlus' else 'libnppif.so';need(any(needle in n for n in libraries),'actual loaded native image library')
    need(all(len(v['sha256'])==64 and v['bytes']>0 for v in libraries.values()),'actual loaded native object digests')
    raw=ROOT/json.loads((proof/'manifest.json').read_text())['raw_artifact_dir'];p=json.loads(CONTRACT.read_text())
    with tarfile.open(raw/'inputs.tar') as tar:
        need(hashlib.sha256(tar.extractfile('probe.cpp').read()).hexdigest()==digest(NATIVE),'uploaded actual native source')
        need(tar.extractfile('inputs/cases.txt').read()==(FOLDER/'cases.txt').read_bytes(),'uploaded actual input list')
        for item in p['inputs']:need(hashlib.sha256(tar.extractfile('inputs/'+item['id']+'.raw').read()).hexdigest()==item['sha256'],'uploaded native input '+item['id'])
    return bound(row)
