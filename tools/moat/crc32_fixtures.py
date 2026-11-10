#!/usr/bin/env python3
"""Freeze file/chunk CRC32 contracts; the polynomial is IEEE, not Castagnoli."""
import random
from experiment import ROOT,write,digest
cases={'original':[b'123456789'],'changed-values':[random.Random(1234).randbytes(10001)],'chunk-boundary':[bytes((i*13)%256 for i in range(n)) for n in [65535,65536,65537]],'multi-file':[b'123456789',bytes(2048),bytes(range(256))*1000,b''],'empty-with-data':[b'',b'123456789'],'repeat':[b'123456789'],'empty-only':[b'']}
for case,files in cases.items():
 path=ROOT/'tests/fixtures/rewrite-extensions/crc32'/case;path.mkdir(parents=True,exist_ok=True)
 for i,data in enumerate(files):(path/f'file{i}.raw').write_bytes(data)
 write(path/'manifest.json',dict(kind='crc32',case=case,expected_run_outcome='ZERO_CHUNKS_REJECTED' if not any(files) else 'SUCCESS',polynomial='IEEE reflected 0xedb88320; init/xorout 0xffffffff',chunk_bytes=65536,warmup=2,total_iterations=5,argv=['-f']+[f'file{i}.raw' for i in range(len(files))],generator_sha256=digest(__file__),files={p.name:dict(sha256=digest(p),bytes=p.stat().st_size) for p in path.glob('*.raw')}))
 print(case,[len(x) for x in files])
