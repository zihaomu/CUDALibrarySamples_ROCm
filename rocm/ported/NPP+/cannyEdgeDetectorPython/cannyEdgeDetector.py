# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# Derived from the unchanged original NPP+ example. Pixel computation uses HIP.
import argparse,json,os,sys
from pathlib import Path
import cv2,numpy as np,pandas as pd,torch,torchvision
from tabulate import tabulate
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'rocm/python'))
from image.canny import CannyEdgeDetector

INPUT_IMAGE='Teapot.jpg';OUTPUT_DIR='Teapot_resolutions';WARMUP_ITERATIONS=5;MEASURE_ITERATIONS=1000
THRESH_WEAK=72;THRESH_STRONG=256
RESOLUTIONS=[(320,180,'320x180'),(640,360,'640x360'),(800,600,'800x600'),(1280,720,'1280x720'),(1920,1080,'1920x1080'),(2560,1440,'2560x1440'),(3840,2160,'3840x2160'),(5120,2880,'5120x2880')]

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--input',default=INPUT_IMAGE);parser.add_argument('--output',default=OUTPUT_DIR);args=parser.parse_args()
 image=cv2.imread(args.input)
 if image is None:raise FileNotFoundError('Image not found: '+args.input)
 if not torch.cuda.is_available() or torch.version.hip is None:raise RuntimeError('ROCm Torch device required')
 output=Path(args.output);output.mkdir(parents=True,exist_ok=True)
 audit=Path(os.environ['MIGRATION_IMAGE_AUDIT_DIR']) if os.environ.get('MIGRATION_IMAGE_AUDIT_DIR') else None
 if audit:audit.mkdir(parents=True,exist_ok=True)
 detector=CannyEdgeDetector();results=[];observations=[]
 print('Input image size:',image.shape);print('Backend: project HIP local Canny');print('Running benchmark...',MEASURE_ITERATIONS,'iterations')
 for width,height,label in RESOLUTIONS:
  print('Processing',label,flush=True)
  resized=cv2.resize(image,(width,height));img_tensor=torch.from_numpy(resized).cuda().permute(2,0,1)
  # Keep the source example's BGR ordering passed into RGB-to-gray weights.
  img_tensor=torchvision.transforms.functional.rgb_to_grayscale(img_tensor).squeeze(0)
  for _ in range(WARMUP_ITERATIONS):detector(img_tensor,THRESH_WEAK,THRESH_STRONG)
  if audit:img_tensor.cpu().numpy().tofile(audit/(label+'-input.bin'))
  timings=[]
  for _ in range(MEASURE_ITERATIONS):
   start=torch.cuda.Event(enable_timing=True);end=torch.cuda.Event(enable_timing=True)
   start.record();detector(img_tensor,THRESH_WEAK,THRESH_STRONG);end.record();torch.cuda.synchronize();timings.append(float(start.elapsed_time(end)))
  pixels=detector(img_tensor,THRESH_WEAK,THRESH_STRONG).cpu().numpy()
  if not cv2.imwrite(str(output/('out_npp_'+label+'.png')),pixels):raise RuntimeError('PNG output failed')
  results.append({'Resolution':label,'Megapixels':width*height/1_000_000,'HIP Time (ms)':float(np.mean(timings)),'Backend':'Project HIP local Canny'})
  observations.append(dict(case='original-'+label,width=width,height=height,warmup=WARMUP_ITERATIONS,iterations=MEASURE_ITERATIONS,timings_ms=timings,nonzero=int(np.count_nonzero(pixels))))
  if audit:pixels.tofile(audit/(label+'-mask.bin'));(audit/'benchmark.json').write_text(json.dumps(dict(resolutions=observations,library=str(detector.library_path)),indent=2)+'\n')
 frame=pd.DataFrame(results);frame.to_csv(output/'performance_results.csv',index=False);print(tabulate(frame,headers='keys',tablefmt='pretty',floatfmt='.3f'));return 0
if __name__=='__main__':raise SystemExit(main())
