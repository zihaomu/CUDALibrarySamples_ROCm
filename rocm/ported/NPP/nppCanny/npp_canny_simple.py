# SPDX-FileCopyrightText: Copyright (c) 2021 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""Original three-output workflow backed by project HIP classical C3 Canny."""
import json,os,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'python'))
import cv2,numpy as np,torch
from image.canny_color import NPPCanny

def main():
 path=sys.argv[1] if len(sys.argv)>1 else 'image.jpg';image=cv2.imread(path)
 if image is None:raise FileNotFoundError('Could not read '+path)
 if not torch.cuda.is_available():raise RuntimeError('No HIP device')
 print('Image:',image.shape,'GPU:',torch.cuda.get_device_name(0),'Backend: Project HIP classical C3 Canny')
 detector=NPPCanny();detector.detect(image);torch.cuda.synchronize();timings=[]
 for _ in range(10):
  start=time.perf_counter();edges=detector.detect(image);timings.append((time.perf_counter()-start)*1000)
 gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY);start=time.perf_counter()
 for _ in range(10):gray_edges=cv2.Canny(gray,50,100,L2gradient=True)
 gray_ms=(time.perf_counter()-start)*1000/10;b,g,r=cv2.split(image);start=time.perf_counter()
 for _ in range(10):merged=cv2.bitwise_or(cv2.Canny(r,50,100,L2gradient=True),cv2.bitwise_or(cv2.Canny(g,50,100,L2gradient=True),cv2.Canny(b,50,100,L2gradient=True)))
 color_ms=(time.perf_counter()-start)*1000/10;hip_ms=float(np.mean(timings));counts=[int(np.count_nonzero(a)) for a in [edges,gray_edges,merged]]
 print('HIP 3-Channel:',hip_ms,'ms',counts[0],'edges');print('OpenCV Grayscale:',gray_ms,'ms',counts[1],'edges');print('OpenCV 3-Channel:',color_ms,'ms',counts[2],'edges')
 print('Gray/HIP elapsed ratio:',gray_ms/hip_ms,'3-channel/HIP elapsed ratio:',color_ms/hip_ms)
 print('Extra edges vs Gray (%):',100.*(counts[0]-counts[1])/counts[1] if counts[1] else 'undefined (no gray edges)')
 for name,array in zip(['edges_npp.png','edges_opencv_gray.png','edges_opencv_3ch.png'],[edges,gray_edges,merged]):
  if not cv2.imwrite(name,array):raise RuntimeError('Image output failed: '+name)
 if root:=os.environ.get('MIGRATION_IMAGE_AUDIT_DIR'):
  d=Path(root);d.mkdir(parents=True,exist_ok=True);image.tofile(d/'input.bin');edges.tofile(d/'mask.bin');(d/'workflow.json').write_text(json.dumps(dict(width=image.shape[1],height=image.shape[0],warmup=1,iterations=10,gray_iterations=10,color_iterations=10,timings_ms=timings,gray_ms=gray_ms,color_ms=color_ms,backend='Project HIP classical C3 Canny'))+'\n')
 return 0
if __name__=='__main__':raise SystemExit(main())
