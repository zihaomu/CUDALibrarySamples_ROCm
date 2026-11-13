#!/usr/bin/env python3
"""Derive adaptive GPU stage counts from an independently encoded JPEG."""
import json
from experiment import ROOT

SELECTION=ROOT/'migration/rewrite/image-prefix-dispatch-selection.json'

def algorithm_count(path,optimized):
    data=path.read_bytes()
    if data[:2]!=b'\xff\xd8' or data[-2:]!=b'\xff\xd9':raise ValueError('incomplete reference JPEG')
    pos=2;shape=None;entropy=None
    while pos+4<=len(data):
        if data[pos]!=255:raise ValueError('invalid JPEG reference marker')
        marker=data[pos+1];length=int.from_bytes(data[pos+2:pos+4],'big')
        if length<2 or pos+2+length>len(data):raise ValueError('truncated JPEG reference marker')
        payload=data[pos+4:pos+2+length]
        if marker==0xc0:
            if len(payload)!=15 or payload[0]!=8 or payload[5]!=3 or payload[7] not in (0x11,0x22) or payload[10]!=0x11 or payload[13]!=0x11:raise ValueError('unexpected baseline reference layout')
            shape=(int.from_bytes(payload[3:5],'big'),int.from_bytes(payload[1:3],'big'),payload[7]&15)
        pos+=2+length
        if marker==0xda:entropy=data[pos:-2];break
    if shape is None or entropy is None:raise ValueError('baseline SOF/SOS missing')
    raw_bytes=0;i=0
    while i<len(entropy):
        if entropy[i]==255:
            if i+1>=len(entropy) or entropy[i+1]!=0:raise ValueError('non-stuffed marker in reference entropy')
            i+=1
        raw_bytes+=1;i+=1
    width,height,sampling=shape
    blocks=((width+8*sampling-1)//(8*sampling))*((height+8*sampling-1)//(8*sampling))*(6 if sampling==2 else 3)
    thresholds=json.loads(SELECTION.read_text())['thresholds']
    bit_kernels=1 if blocks<=thresholds['bits'] else 3
    stuff_kernels=1 if raw_bytes<=thresholds['stuff'] else 3
    return 10+int(optimized)+bit_kernels+stuff_kernels
