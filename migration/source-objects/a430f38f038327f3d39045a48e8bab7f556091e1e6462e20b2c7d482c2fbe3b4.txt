#!/usr/bin/env python3
"""Independent array mathematics for the declared color and DCT contract."""
from decimal import Decimal,localcontext
import numpy as np

def color(rgb,channel,sampling):
    scale=sampling if channel else 1;h,w=rgb.shape[:2]
    a=np.pad(rgb.astype(np.int64),((0,(-h)%scale),(0,(-w)%scale),(0,0)),mode='edge')
    sums=a.reshape((h+scale-1)//scale,scale,(w+scale-1)//scale,scale,3).sum((1,3))
    weights=np.array([[299000,587000,114000],[-168736,-331264,500000],[500000,-418688,-81312]][channel])
    denominator=1000000*scale*scale;n=(sums*weights).sum(-1)+(128*denominator if channel else 0)
    q,r=np.divmod(n,denominator)
    return np.clip(q+((r*2>denominator)|((r*2==denominator)&(q%2!=0))),0,255).astype(np.uint8)

def blocks(plane):
    h,w=plane.shape;a=np.pad(plane,((0,(-h)%8),(0,(-w)%8)),mode='edge').astype(np.float64)-128
    return a.reshape((h+7)//8,8,(w+7)//8,8).transpose(0,2,1,3)

def transform(block_array):
    x=np.arange(8);u=x[:,None];basis=np.cos((2*x+1)*u*np.pi/16)
    basis[0]*=np.sqrt(.5)
    result=(basis@block_array@basis.T)*.25
    result[...,0,0]=block_array.sum(axis=(-2,-1))/8
    return result

def coefficient_checks(plane,coefficients,quant,budget):
    block_array=blocks(plane);coefficients=np.asarray(coefficients,dtype=np.int64).reshape(block_array.shape)
    quant=np.asarray(quant,dtype=np.int64).reshape(8,8)
    if np.any(quant<1) or np.any(quant>255):raise ValueError('baseline DQT range')
    exact=transform(block_array);error=np.abs(coefficients*quant-exact);allowance=quant*.5+budget
    total=block_array.sum(axis=(-2,-1)).astype(np.int64);q=int(quant[0,0])
    dc=np.sign(total)*((np.abs(total)+4*q)//(8*q))
    margin=error-allowance
    return dict(passed=bool(np.all(margin<=0) and np.array_equal(coefficients[...,0,0],dc)),
        coefficients=int(coefficients.size),DC_exact=bool(np.array_equal(coefficients[...,0,0],dc)),
        worst_excess=float(margin.max()),max_unquantized_residual=float(error.max()),
        failing_frequencies=int(np.count_nonzero(margin>0)),
        first_failures=[dict(block_y=int(y),block_x=int(x),v=int(v),u=int(u),actual=int(coefficients[y,x,v,u]),DCT=float(exact[y,x,v,u]),quant=int(quant[v,u]),excess=float(margin[y,x,v,u])) for y,x,v,u in np.argwhere(margin>0)[:20]])

def precision_check():
    # Decimal oracle has independently evaluated cosine and normalization; no
    # NumPy coefficient table, production source, or GPU output is reused.
    with localcontext() as context:
        context.prec=80
        pi=Decimal('3.14159265358979323846264338327950288419716939937510582097494459230781640628620899')
        def cos(angle):
            angle=angle%(2*pi)
            if angle>pi:angle-=2*pi
            term=result=Decimal(1);n=0
            while abs(term)>Decimal('1e-75'):
                n+=1;term*=-angle*angle/Decimal((2*n-1)*(2*n));result+=term
            return result
        basis=[[cos(Decimal((2*x+1)*u)*pi/16)*(Decimal('.5').sqrt() if u==0 else 1)/2 for x in range(8)] for u in range(8)]
        y,x=np.indices((8,8));rng=np.random.default_rng(66391)
        samples=[np.full((8,8),n) for n in [-128,-1,0,1,127]]
        samples += [np.where((x+y)%2,127,-128),np.where(x<4,127,-128),rng.integers(-128,128,(8,8)),np.eye(8,dtype=int)*255-128]
        differences=[]
        for sample in samples:
            actual=transform(sample.astype(np.float64))
            reference=np.array([[float(sum(Decimal(int(sample[y,x]))*basis[v][y]*basis[u][x] for y in range(8) for x in range(8))) for u in range(8)] for v in range(8)])
            differences.append(float(np.abs(reference-actual).max()))
    return dict(blocks=len(samples),frequencies=len(samples)*64,decimal_precision=80,max_abs=max(differences),passed=max(differences)<=1e-9)
