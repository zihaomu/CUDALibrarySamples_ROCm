#!/usr/bin/env python3
"""Reproduce the native rocRAND normal-header compile incompatibility with exact source."""
import datetime,json,pathlib,os,subprocess
from catalog import ROOT
from run import command,digest,evidence_directory
from device_guard import allowed_devices
out=ROOT/'artifacts'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')/'batches12_15-capabilities';out.mkdir(parents=True);devices=allowed_devices();r=next(r for r in json.loads((ROOT/'migration/reports/batches12_15-rocm.json').read_text()) if r['batch']=='b14');cmd=json.loads((evidence_directory(r['evidence'])/'commands.json').read_text())['build'];source=ROOT/'tools/migration/probes/rocrand_normal_header.cu';cmd[cmd.index(str(ROOT/r['implementation']))]=str(source);cmd[cmd.index('-o')+1]=str(out/'normal_header_probe');(out/'commands.json').write_text(json.dumps(cmd,indent=2)+'\n');rc=command(cmd,ROOT,out/'build.log',dict(os.environ),180);code=command([str(out/'normal_header_probe')],ROOT,out/'run.log',dict(os.environ),60) if rc==0 else None
for name in ['b15-rpp-api.log','b12-environment.log','b12-gpu-selection.log','b12-mpi-download.log','b14-mathdx-download.log']:
 p=ROOT/'build'/name
 if p.exists():(out/name).write_bytes(p.read_bytes())
report=dict(native_normal_header_build_return_code=rc,run_return_code=code,status='NATIVE_HEADER_INCOMPATIBILITY_REPRODUCED' if rc else 'NATIVE_HEADER_AVAILABLE',source=str(source.relative_to(ROOT)),source_sha256=digest(source),evidence=str(out.relative_to(ROOT)),environment=dict(devices=devices,image_id=os.environ['DEEPINFER_IMAGE_ID'],rocm_release=os.environ['DEEPINFER_ROCM_RELEASE']));(ROOT/'migration/reports/batches12_15-capabilities.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'])
