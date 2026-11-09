#!/usr/bin/env python3
"""Append implementation checkpoints to the user-requested design log."""
import argparse,datetime,pathlib
DOC=pathlib.Path(__file__).resolve().parents[3]/'doc/cuda_samples_on_rocm_design.md'
def checkpoint(step,result,next_step,status='已完成'):
 if not DOC.exists():return print(step,result,flush=True)
 s=DOC.read_text();line=f'| {step} | {status} | {result.replace(chr(10)," ").replace("|","/")} | {next_step.replace(chr(10)," ").replace("|","/")} |\n'
 marker='\n## 12.'
 pos=s.index(marker);s=s[:pos].rstrip()+'\n'+line+s[pos:];DOC.write_text(s)
 print(step,flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('step');p.add_argument('result');p.add_argument('next_step');p.add_argument('--status',default='已完成');a=p.parse_args();checkpoint(a.step,a.result,a.next_step,a.status)
