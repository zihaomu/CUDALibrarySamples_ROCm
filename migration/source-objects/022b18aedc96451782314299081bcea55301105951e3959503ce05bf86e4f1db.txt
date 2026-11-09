#!/usr/bin/env python3
"""Link each recorded support decision to its implementation and exact logs."""
import collections, hashlib, json, os, pathlib
from catalog import ROOT, CANDIDATES
from run import digest

METHODS={
    'API_PORT':'库 API 迁移',
    'HYBRID_HIP':'生态库 + 项目 HIP 实现',
    'LIBRARY_REWRITE':'改用 AMD 库重写算法流程',
    'API_PORT_WITH_EXECUTION_ADAPTER':'库 API 迁移 + 执行语义适配',
    'UNIMPLEMENTED_BINDING':'语言绑定尚未实现',
}

def logs(root):
    if not root:return []
    p=ROOT/root
    if p.is_file():return [root] if p.suffix=='.log' else []
    return sorted(str(q.relative_to(ROOT)) for q in p.rglob('*.log') if q.is_file())

def records(sample):
    items=[('selected_validation',sample.get('selected_validation',{})),
           ('original_profile_validation',sample.get('original_profile_validation',{}))]
    items += [('attempts/'+str(i),r) for i,r in reversed(list(enumerate(sample['attempts'])))]
    return items

def render_index(cat):
    comparisons={}
    for name in ['m1-comparison.json','additional-comparison.json','blas-three-way.json']:
        for r in json.loads((ROOT/'migration/reports'/name).read_text()):
            comparisons.setdefault(r['id'],[]).append((str(pathlib.PurePosixPath('migration/reports')/name),r))
    rows=[]
    for sample in cat['samples']:
        implementation=sample.get('implementation');sha=digest(ROOT/implementation) if implementation and (ROOT/implementation).is_file() else None
        matches=[(field,r) for field,r in records(sample) if sha and sha in [r.get(k) for k in ['implementation_sha256','ported_sha256','source_sha256','original_port_sha256']]]
        if sample['status']=='PASSED':
            matches=[(f,r) for f,r in matches if r.get('status')=='PASSED']
            if sample['milestone']=='M1':matches=[(f,r) for f,r in matches if r.get('scope','').startswith('M1 extended')]
            if not matches:raise ValueError('No current-source qualification: '+sample['id'])
        field,proof=matches[0] if matches else ('original_port',sample.get('original_port') or sample['attempts'][-1])
        amd=proof.get('rocm_evidence') or proof.get('evidence')
        if not amd:
            amd=next((p for p in reversed(sample['evidence']) if (ROOT/p).is_dir() and 'cuda' not in p),None)
        cuda=proof.get('cuda_evidence');cuda_basis='当前验收记录' if cuda else None
        reports=[]
        if proof.get('cpu_report'):reports.append(proof['cpu_report'])
        for path,r in comparisons.get(sample['id'],[]):
            reports.append(path)
            if not cuda:cuda=r.get('cuda_evidence');cuda_basis='专项对照记录'
        if not cuda:
            cuda=(sample.get('original_cuda') or {}).get('evidence');cuda_basis='原始 CUDA 尝试'
        if not cuda:
            cuda=next((p for p in reversed(sample['evidence']) if (ROOT/p).is_dir() and 'cuda' in p),None)
            cuda_basis='历史 CUDA 尝试' if cuda else '未归档 CUDA 日志，见详情中的前置条件'
        reports += [p for p in sample['evidence'] if p.endswith('.json') and (ROOT/p).is_file()]
        reports=list(dict.fromkeys(reports))
        rows.append({
            'id':sample['id'],'family':sample['family'],'source':sample['source'],
            'status':sample['status'],'level':sample['level'],
            'actual_library':sample.get('actual_library'),'backend_library':sample.get('backend_library'),
            'implementation_method':sample.get('equivalence'),
            'implementation':implementation,'implementation_sha256':sha,
            'passed_cases':sample['passed_cases'],'required_cases':sample['required_cases'],
            'scope_and_reason':sample['reason'],'retry_condition':sample['retry_condition'],
            'detail':'migration/sample-reports/'+sample['source']+'.md',
            'record_field':field,'amd_evidence':amd,'amd_logs':logs(amd),
            'cuda_comparison':sample['cuda_comparison'],'cuda_evidence':cuda,
            'cuda_evidence_basis':cuda_basis,'cuda_logs':logs(cuda),
            'validation_reports':reports,'all_evidence':sample['evidence'],
        })
    return {'scope':'All 639 entrypoints, including failures. PASSED is limited to registered cases. Logs point to current-source qualification where available, otherwise the recorded attempt; compilation/import logs are not GPU correctness proof.',
            'counts':dict(collections.Counter(r['status'] for r in rows)),
            'implementation_methods':METHODS,'samples':rows}

def write_index(cat):
    report=render_index(cat);base=ROOT/'migration/reports'
    (base/'support-log-index.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    link_parent=base
    def link(label,target,parent=None):
        return '['+str(label).replace('|','/')+']('+os.path.relpath(ROOT/target,parent or link_parent).replace(' ','%20')+')'
    def safe(value):return str(value or '—').replace('|','/').replace('\n',' ')
    def log_cell(r,backend):
        evidence=r[backend+'_evidence'];files=r[backend+'_logs']
        if not files:return '未归档该类日志；'+link('详情/阻塞原因',r['detail'])
        parts=[]
        for p in files:
            root=ROOT/evidence
            label=os.path.relpath(ROOT/p,root) if root.is_dir() else pathlib.Path(p).name
            parts.append(link(label,p))
        return '<br>'.join(parts)
    text='# 样例支持方式与详细日志总表\n\n'
    text+='覆盖 **'+str(len(report['samples']))+' 个样例入口**：'+'、'.join(str(report['counts'].get(k,0))+' '+k for k in ['PASSED','PARTIAL','FAILED','UNSUPPORTED','BLOCKED'])+'。全部 '+str(len(CANDIDATES))+' 个模块逐项列出实现方式、范围/原因、AMD 日志、CUDA 日志与验收报告。数据直接来自 '+link('逐例清单','migration/samples.yaml')+'，'+link('JSON 索引','migration/reports/support-log-index.json')+' 另含全部历史证据路径、源码 SHA256、已通过/必需用例及恢复条件。\n\n'
    text+='**查阅方式：** 先看状态和“支持范围/失败原因”，再看实际库与实现源码。AMD 栏优先链接与当前源码 hash 匹配的选定验收日志；未通过项链接实际尝试。`build.log` 是编译/链接记录，`run.log` 是程序输出，`<case>/run.log` 是对应输入的输出。命令与环境位于同目录的 `commands.json` 和 `*.environment.json`，从“证据目录”进入。缺少运行日志时会明确标注，不将编译/import 成功视作 GPU 通过。\n\n'
    text+='CUDA 栏注明“当前验收记录”“专项对照记录”或“原始/历史尝试”；只有该行 `CUDA comparison = PASSED` 才表示已完成登记范围的对照。CPU 验收报告保存误差、阈值、残差等结构化检查，不要求每个样例另有一个 CPU 文本 log。所有历史失败与重试记录保留在“详情”。大二进制输出按 hash/生成方法保存，未全部提交 Git。\n\n'
    text+='实现方式是逐例登记值：库 API 迁移、生态库 + 项目 HIP、算法流程重写、执行语义适配或未实现语言绑定；**实际库名称和逐例范围决定具体支持边界**。例如 cuDSS 的 CPU 符号分析 + GPU CSRRF、rotmg 的项目 HIP 修正，不因同样标为 PASSED 而隐去区别。\n\n'
    text+='模块导航：'+' · '.join('['+f+'](#module-'+str(i)+')' for i,f in enumerate(CANDIDATES))+'\n\n'
    order={'PASSED':0,'PARTIAL':1,'FAILED':2,'UNSUPPORTED':3,'BLOCKED':4}
    for i,family in enumerate(CANDIDATES):
        group=sorted((r for r in report['samples'] if r['family']==family),key=lambda r:(order.get(r['status'],5),r['source']))
        text+='<a id="module-'+str(i)+'"></a>\n\n## '+family+'\n\n'
        page=base/'support-log-index'/(family.replace('/','__')+'.md');page.parent.mkdir(exist_ok=True)
        text+='| 样例 / 详情 | 状态 / 用例 | 实际库与实现方式 | 详细日志与范围 |\n| --- | --- | --- | --- |\n'
        link_parent=page.parent
        module_text='# '+family+'：支持方式与详细日志\n\n'+link('返回总表','migration/reports/support-log-index.md')+'；完整记录包括当前范围/失败原因、AMD/CUDA 日志和 CPU 验收报告。编译/import 成功不代表 GPU 数值通过；CUDA 栏标明日志属于哪次记录。\n\n'
        module_text+='| 样例 / 详情 | 状态 / 用例 | 实际库、方式与源码 | 支持范围 / 失败原因 | AMD 详细 log | CPU 验收 / CUDA log |\n| --- | --- | --- | --- | --- | --- |\n'
        for r in group:
            method=METHODS.get(r['implementation_method'],r['implementation_method'])
            actual=(r['actual_library'] or '尚无已验证使用库')+(' / '+r['backend_library'] if r['actual_library'] and r['backend_library'] else '')
            implementation=link('源码' if r['status']=='PASSED' else '实现/草稿',r['implementation']) if r['implementation'] and (ROOT/r['implementation']).exists() else '无实现源码'
            amd=log_cell(r,'amd')+'<br>'+link('证据目录',r['amd_evidence']) if r['amd_evidence'] and (ROOT/r['amd_evidence']).exists() else log_cell(r,'amd')
            cpu='<br>'.join(link(pathlib.Path(p).name,p) for p in r['validation_reports']) or link('验收/缺项记录',r['detail'])
            cuda='CUDA comparison = '+r['cuda_comparison']+'；'+r['cuda_evidence_basis']+'<br>'+log_cell(r,'cuda')
            label=str(pathlib.PurePosixPath(r['source']).relative_to(family));anchor='sample-'+hashlib.sha256(r['id'].encode()).hexdigest()[:12]
            text+='| '+link(label,r['detail'],base)+' | '+r['status']+' / '+str(len(r['passed_cases']))+'/'+str(len(r['required_cases']))+' | '+safe(actual)+'；'+safe(method)+' | '+link('日志、范围、源码',str(page.relative_to(ROOT)),base)[:-1]+'#'+anchor+') |\n'
            module_text+='| <a id="'+anchor+'"></a>'+link(label,r['detail'])+' | '+r['status']+' / '+r['level']+'<br>'+str(len(r['passed_cases']))+'/'+str(len(r['required_cases']))+' | '+safe(actual)+'<br>'+safe(method)+'；'+implementation+' | '+safe(r['scope_and_reason'])+' | '+amd+' | '+cpu+'<br>'+cuda+' |\n'
        page.write_text(module_text)
        link_parent=base
        text+='\n'
    text+='重新生成：`python3 tools/migration/render.py`（同时更新总表和 JSON）。只生成文档，不重新执行 GPU 实验或更改验收结论。\n'
    (base/'support-log-index.md').write_text(text)
    return report

if __name__=='__main__':
    result=write_index(json.loads((ROOT/'migration/samples.yaml').read_text()))
    print('Indexed',len(result['samples']),'samples;',sum(len(r['amd_logs'])+len(r['cuda_logs']) for r in result['samples']),'direct log links')
