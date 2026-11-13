#!/usr/bin/env python3
"""Independent strict baseline JPEG entropy parser for encoder qualification.

CPU reference only. Supports the encoder contract's single interleaved scan,
three components, 8-bit baseline, 444/420, and no restart intervals.
"""
import math

def zigzag():
    result=[]
    for diagonal in range(15):
        pairs=[(y,diagonal-y) for y in range(8) if 0<=diagonal-y<8]
        if diagonal%2==0:pairs.reverse()
        result.extend(y*8+x for y,x in pairs)
    return result

class Bits:
    def __init__(self,data):self.data=data;self.position=0
    def take(self,n):
        if self.position+n>8*len(self.data):raise ValueError('truncated entropy')
        value=0
        for _ in range(n):
            value=(value<<1)|((self.data[self.position//8]>>(7-self.position%8))&1);self.position+=1
        return value
    def symbol(self,table):
        code=0
        for length in range(1,17):
            code=(code<<1)|self.take(1)
            if (length,code) in table:return table[length,code]
        raise ValueError('invalid Huffman code')
    def signed(self,n):
        value=self.take(n)
        return value if n==0 or value>=1<<(n-1) else value-(1<<n)+1

def decode(data):
    if data[:2]!=b'\xff\xd8':raise ValueError('missing SOI')
    cursor=2;quant={};tables={};frame=None;scan=None;order=zigzag()
    while cursor<len(data):
        if data[cursor]!=255 or cursor+1>=len(data):raise ValueError('invalid marker')
        marker=data[cursor+1];cursor+=2
        if marker in [0,1,0xd8,0xd9] or 0xd0<=marker<=0xd7:raise ValueError('unexpected header marker')
        if cursor+2>len(data):raise ValueError('truncated marker length')
        length=int.from_bytes(data[cursor:cursor+2],'big')
        if length<2 or cursor+length>len(data):raise ValueError('truncated marker segment')
        payload=data[cursor+2:cursor+length];cursor+=length
        if marker==0xdb:
            at=0
            while at<len(payload):
                selector=payload[at];at+=1
                if selector>>4 or selector in quant or at+64>len(payload):raise ValueError('invalid/duplicate baseline DQT')
                values=[0]*64
                for index in range(64):values[order[index]]=payload[at+index]
                if min(values)<1:raise ValueError('zero quantizer')
                quant[selector]=values;at+=64
        elif marker==0xc4:
            at=0
            while at<len(payload):
                if at+17>len(payload):raise ValueError('truncated Huffman header')
                selector=payload[at];counts=payload[at+1:at+17];at+=17
                if selector>>4>1 or selector&15>3 or selector in tables or not sum(counts) or at+sum(counts)>len(payload):raise ValueError('invalid/duplicate Huffman table')
                table={};code=0
                for length,count in enumerate(counts,1):
                    for _ in range(count):
                        if code>=(1<<length)-1:raise ValueError('oversubscribed/all-ones Huffman code')
                        table[length,code]=payload[at];at+=1;code+=1
                    code<<=1
                tables[selector]=table
        elif marker==0xc0:
            if frame is not None or len(payload)!=15 or payload[0]!=8 or payload[5]!=3:raise ValueError('baseline three-component SOF required')
            height=int.from_bytes(payload[1:3],'big');width=int.from_bytes(payload[3:5],'big')
            components=[dict(id=payload[i],horizontal=payload[i+1]>>4,vertical=payload[i+1]&15,quant=payload[i+2]) for i in [6,9,12]]
            if not width or not height or len({c['id'] for c in components})!=3:raise ValueError('invalid frame dimensions/component IDs')
            sampling=components[0]['horizontal']
            if sampling not in [1,2] or components[0]['vertical']!=sampling or any(c['horizontal']!=1 or c['vertical']!=1 for c in components[1:]):raise ValueError('outside 444/420 output contract')
            frame=dict(width=width,height=height,components=components,sampling=sampling)
        elif marker==0xda:
            if frame is None or len(payload)!=10 or payload[0]!=3 or payload[-3:]!=bytes([0,63,0]):raise ValueError('single baseline interleaved scan required')
            scan=[dict(id=payload[i],dc=payload[i+1]>>4,ac=16+(payload[i+1]&15)) for i in [1,3,5]]
            if [c['id'] for c in scan]!=[c['id'] for c in frame['components']]:raise ValueError('scan component order')
            break
        elif not (0xe0<=marker<=0xef or marker==0xfe):raise ValueError('unexpected coding process/marker')
    if scan is None:raise ValueError('missing scan')
    entropy=bytearray();ended=False
    while cursor<len(data):
        value=data[cursor];cursor+=1
        if value==255:
            if cursor>=len(data):raise ValueError('truncated entropy marker')
            following=data[cursor];cursor+=1
            if following==0:entropy.append(255)
            elif following==0xd9:
                if cursor!=len(data):raise ValueError('trailing bytes after EOI')
                ended=True;break
            else:raise ValueError('unexpected entropy marker/restart')
        else:entropy.append(value)
    if not ended:raise ValueError('missing EOI')
    bits=Bits(entropy);s=frame['sampling'];mx=math.ceil(frame['width']/(8*s));my=math.ceil(frame['height']/(8*s));last=[0,0,0];blocks=[]
    for c in frame['components']:
        if c['quant'] not in quant:raise ValueError('undefined DQT')
    for y in range(my):
        for x in range(mx):
            for channel,(component,selector) in enumerate(zip(frame['components'],scan)):
                if selector['dc'] not in tables or selector['ac'] not in tables:raise ValueError('undefined DHT')
                for dy in range(component['vertical']):
                    for dx in range(component['horizontal']):
                        coefficient=[0]*64;n=bits.symbol(tables[selector['dc']])
                        if n>11:raise ValueError('baseline DC category')
                        last[channel]+=bits.signed(n);coefficient[0]=last[channel];k=1
                        while k<64:
                            symbol=bits.symbol(tables[selector['ac']]);run= symbol>>4;n=symbol&15
                            if n==0:
                                if run==0:break
                                if run!=15:raise ValueError('invalid AC run')
                                k+=16
                                if k>64:raise ValueError('AC zero run overflow')
                            else:
                                k+=run
                                if n>10 or k>=64:raise ValueError('AC category/run overflow')
                                coefficient[order[k]]=bits.signed(n);k+=1
                        blocks.append(dict(channel=channel,x=x*component['horizontal']+dx,y=y*component['vertical']+dy,coefficients=coefficient))
    remaining=8*len(entropy)-bits.position
    if remaining>=8 or bits.take(remaining)!=(1<<remaining)-1:raise ValueError('extra entropy or invalid final pad bits')
    return dict(**frame,quant=quant,blocks=blocks,entropy_bytes=len(entropy),pad_bits=remaining)
