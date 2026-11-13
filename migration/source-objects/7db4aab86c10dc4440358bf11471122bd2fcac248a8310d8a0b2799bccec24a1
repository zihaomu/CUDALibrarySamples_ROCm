#!/usr/bin/env python3
"""Full contingency and deterministic one-to-one marker compatibility diagnostics."""
import numpy as np
from image_watershed_semantics_reference import canonical

def adjacency(project,native):
    h,w=project.shape;rows={}
    for name,dy,dx in [('horizontal',0,1),('vertical',1,0),('diagonal-down-right',1,1),('diagonal-down-left',1,-1)]:
        y0,y1=max(0,-dy),min(h,h-dy);x0,x1=max(0,-dx),min(w,w-dx)
        dst=np.s_[y0:y1,x0:x1];src=np.s_[y0+dy:y1+dy,x0+dx:x1+dx]
        p=project[dst]!=project[src];n=native[dst]!=native[src]
        rows[name]=dict(edges=p.size,agree=int(np.sum(p==n)),project_splits_native_edge=int(np.sum(p&~n)),project_merges_native_edge=int(np.sum(~p&n)))
    count=sum(r['edges'] for r in rows.values());same=sum(r['agree'] for r in rows.values())
    return dict(directions=rows,all_edges=count,agreement=None if not count else same/count)

def compare(project,native,folder,case):
    p=canonical(project).ravel();n=canonical(native).ravel();pn=int(p.max())+1;nn=int(n.max())+1
    pairs,counts=np.unique(np.stack([p,n],axis=1),axis=0,return_counts=True);pa=np.bincount(p,minlength=pn);na=np.bincount(n,minlength=nn)
    folder.mkdir(parents=True,exist_ok=True);table=folder/(case+'.contingency.csv')
    np.savetxt(table,np.column_stack([pairs,counts]),fmt='%d',delimiter=',',header='project_region,native_region,intersection_pixels',comments='')
    # This is a declared greedy diagnostic, not an optimal-assignment claim.
    order=np.lexsort((pairs[:,1],pairs[:,0],-counts));pm=np.full(pn,-1,np.int64);nm=np.full(nn,-1,np.int64);pi=np.zeros(pn);ni=np.zeros(nn);matches=[]
    for k in order:
        a,b=map(int,pairs[k]);intersection=int(counts[k])
        if pm[a]>=0 or nm[b]>=0:continue
        pm[a]=b;nm[b]=a;iou=intersection/(int(pa[a])+int(na[b])-intersection);pi[a]=iou;ni[b]=iou;matches.append((a,b,intersection,int(pa[a]),int(na[b]),iou))
    for a in np.flatnonzero(pm<0):matches.append((int(a),-1,0,int(pa[a]),0,0.0))
    for b in np.flatnonzero(nm<0):matches.append((-1,int(b),0,0,int(na[b]),0.0))
    matching=folder/(case+'.one-to-one.csv')
    with matching.open('w') as f:
        f.write('project_region,native_region,intersection_pixels,project_area,native_area,IoU\n')
        for row in matches:f.write(','.join(str(v) for v in row)+'\n')
    def summary(values,areas):
        small=areas<=64
        return dict(macro_IoU=float(values.mean()),area_weighted_IoU=float(np.sum(values*areas)/areas.sum()),small_regions_1_to_64_pixels=int(small.sum()),small_region_macro_IoU=float(values[small].mean()) if small.any() else None,zero_IoU_regions=int(np.sum(values==0)),minimum_IoU=float(values.min()))
    return dict(classification='DIAGNOSTIC_ONLY_ALGORITHM_VARIANT',project_regions=pn,native_regions=nn,
      exact_partition=bool(np.array_equal(p,n)),project_regions_spanning_multiple_native=int(np.sum(np.bincount(pairs[:,0],minlength=pn)>1)),native_regions_spanning_multiple_project=int(np.sum(np.bincount(pairs[:,1],minlength=nn)>1)),
      matching_rule='Greedy descending intersection pixel count; ties by canonical project then native first-pixel ID. Each region matched at most once; unmatched IoU=0. Not optimal matching.',matched_pairs=int(np.sum(pm>=0)),unmatched_project=int(np.sum(pm<0)),unmatched_native=int(np.sum(nm<0)),project_IoU=summary(pi,pa),native_IoU=summary(ni,na),
      adjacency=adjacency(project,native),contingency_csv=table.name,one_to_one_csv=matching.name)
