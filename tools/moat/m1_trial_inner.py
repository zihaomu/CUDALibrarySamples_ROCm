import argparse,os,subprocess
from pathlib import Path
from snapshot import capture
from experiment import ROOT,write
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();write(a.output,capture())
r=subprocess.run([str(ROOT/'build/rocm/cuBLAS_Level-3_gemm')],env=dict(os.environ,MIGRATION_FIXTURE=str(ROOT/'tests/fixtures/m1-input.f64')));raise SystemExit(r.returncode)
