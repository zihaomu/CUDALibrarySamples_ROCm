#!/usr/bin/env python3
"""Compare independent scalar-stage Canny models with native observations."""
import itertools,json
import cv2,numpy as np
from experiment import ROOT,Experiment,write,digest
from image_progress import record

def gradients(input,config):
 w,h,c,pitch=config['width'],config['height'],config['channels'],config['pitch'];a=np.fromfile(input,dtype=np.uint8).reshape(h,pitch)[:,:w*c].reshape(h,w,c).astype(np.int32);p=np.pad(a,((1,1),(1,1),(0,0)),mode='edge');gx=-p[:-2,:-2]-2*p[1:-1,:-2]-p[2:,:-2]+p[:-2,2:]+2*p[1:-1,2:]+p[2:,2:];gy=-p[:-2,:-2]-2*p[:-2,1:-1]-p[:-2,2:]+p[2:,:-2]+2*p[2:,1:-1]+p[2:,2:];sq=gx*gx+gy*gy;arg=np.argmax(sq,axis=2);dx=np.take_along_axis(gx,arg[:,:,None],2)[:,:,0];dy=np.take_along_axis(gy,arg[:,:,None],2)[:,:,0];mag=np.sqrt(np.take_along_axis(sq,arg[:,:,None],2)[:,:,0].astype(np.float64));return dx,dy,mag

def classify(dx,dy,mag,config,quant,tie,direction,border,strict):
 if quant=='floor':m=np.floor(mag)
 elif quant=='round':m=np.floor(mag+.5)
 elif quant=='squared':m=mag**2
 else:m=mag
 h,w=m.shape;ax=np.abs(dx);ay=np.abs(dy)
 if direction=='opencv':horizontal=ay*32768<ax*13573;vertical=ay*32768>ax*(13573+65536)
 elif direction=='old':angle=(np.arctan2(dy,dx)*180/np.pi)%180;horizontal=(angle<22.5)|(angle>=157.5);vertical=(angle>=67.5)&(angle<112.5)
 else:horizontal=ay<ax*.4142135623730951;vertical=ay>ax*2.414213562373095
 # Compare against the dominant-gradient axis and the appropriate diagonal.
 p=np.pad(m,1,mode='edge' if border=='replicate' else 'constant');left=p[1:-1,:-2];right=p[1:-1,2:];up=p[:-2,1:-1];down=p[2:,1:-1];diag=(dx*dy>=0)
 a=np.where(horizontal,left,np.where(vertical,up,np.where(diag,p[:-2,:-2],p[:-2,2:])));b=np.where(horizontal,right,np.where(vertical,down,np.where(diag,p[2:,2:],p[2:,:-2])))
 if tie=='ge-gt':maximum=(m>=a)&(m>b)
 elif tie=='gt-ge':maximum=(m>a)&(m>=b)
 elif tie=='ge-ge':maximum=(m>=a)&(m>=b)
 elif tie=='opencv':maximum=np.where(horizontal|vertical,(m>a)&(m>=b),(m>a)&(m>b))
 else:maximum=(m>a)&(m>b)
 low=config['low'];high=config['high'];weak=maximum&(mag>low if strict else mag>=low);strong=weak&(mag>high if strict else mag>=high)
 _,labels=cv2.connectedComponents(weak.astype(np.uint8),connectivity=8);good=np.zeros(labels.max()+1,dtype=bool);good[labels[strong]]=True;good[0]=False;return good[labels].astype(np.uint8)*255

def main():
 rows=json.loads((ROOT/'migration/reports/image-I0-Canny-native-probes.json').read_text());e=Experiment('I0','Canny-independent-model-research','CPU-research',sources=[__file__]);prepared=[]
 for r in rows:
  if r['return_code']:continue
  src=ROOT/r['input_snapshot'];config=json.loads((src/'config.json').read_text());gold=np.fromfile(ROOT/r['output']/'output.bin',np.uint8).reshape(config['height'],config['output_pitch'])[:,:config['width']];dx,dy,mag=gradients(src/'input.bin',config);prepared.append((r['case'],config,gold,dx,dy,mag))
 results=[]
 for quant,tie,direction,border,strict in itertools.product(['exact','floor','round'],['ge-gt','gt-ge','ge-ge','gt-gt','opencv'],['opencv','old'],['replicate','zero'],[True,False]):
  mismatches={}
  for name,config,gold,dx,dy,mag in prepared:
   if name.startswith('teapot'):continue
   actual=classify(dx,dy,mag,config,quant,tie,direction,border,strict);mismatches[name]=int(np.count_nonzero(actual!=gold))
  results.append(dict(quantization=quant,tie=tie,direction=direction,border=border,strict=strict,mismatches=mismatches,total=sum(mismatches.values())))
 best=sorted(results,key=lambda r:r['total'])[:12]
 for model in best:
  for name,config,gold,dx,dy,mag in prepared:
   if not name.startswith('teapot'):continue
   actual=classify(dx,dy,mag,config,model['quantization'],model['tie'],model['direction'],model['border'],model['strict']);model['mismatches'][name]=int(np.count_nonzero(actual!=gold))
  model['all_total']=sum(model['mismatches'].values())
 result=dict(status='OBSERVED',scope='Contract research only; model selection must be frozen and checked on independent holdouts before qualification',best=best,all_small_models=results);write(e.path/'models.json',result);ref=e.finish('OBSERVED');result['evidence']=ref;write(ROOT/'migration/reports/image-I0-Canny-models.json',result);record('I0','独立CPU Canny阶段模型与真实NPP像素作研究对照；包含整数梯度、L2量化、NMS方向/tie与边界候选，不以拟合一张图作为资格。',[ref]);print(json.dumps(best[:5]))
if __name__=='__main__':main()
