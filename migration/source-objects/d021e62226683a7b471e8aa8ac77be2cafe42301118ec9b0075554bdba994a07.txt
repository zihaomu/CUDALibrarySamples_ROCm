"""Independent CPU codec decoding of every raw GPU block and full byte-exact outputs."""
import ctypes,hashlib,json,pathlib
from catalog import ROOT
from validate_blas import np,observed
from batches9_11_spec import kind
lz4=ctypes.CDLL(str(ROOT/'build/cpu-codecs/lib/liblz4.so'));snappy=ctypes.CDLL(str(ROOT/'build/cpu-codecs/lib/libsnappy.so'));lz4.LZ4_decompress_safe.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int];snappy.snappy_uncompress.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.POINTER(ctypes.c_size_t)]
def decode(data,n,sn):
 out=ctypes.create_string_buffer(max(1,n));size=ctypes.c_size_t(n);got=snappy.snappy_uncompress(data,len(data),out,ctypes.byref(size)) if sn else lz4.LZ4_decompress_safe(data,out,len(data),n)
 if (got!=0 or size.value!=n) if sn else got!=n:raise ValueError('CPU codec rejected raw stream')
 return out.raw[:n]
table=[]
for i in range(256):
 c=i
 for _ in range(8):c=(c>>1)^(0x82f63b78 if c&1 else 0)
 table.append(c)
def crc(data):
 c=0xffffffff
 for b in data:c=table[(c^b)&255]^(c>>8)
 return c^0xffffffff

def validate(source,case,d,backend='rocm'):
 o=observed(d/'run.log');sn=bool(o['input_snappy'][0]);lengths=o['input_lengths'].astype(int).tolist();checks=[];hashes={};bad=case in ['corrupt-stream','truncated-stream']
 def gate(name,yes,**detail):checks.append(dict(check=name,passed=bool(yes),**detail))
 def load(name):return (d/(name+'.bin')).read_bytes()
 gate('declared-codec',sn==('snappy' in source));gate('chunk-count',len(lengths)==o['input_chunks'][0]);gate('chunk-bounds',all(0<=n<=65536 for n in lengths));nonempty=[i for i,n in enumerate(lengths) if n]
 gate('original-million-bytes',case!='original' or sum(lengths)==1000000);gate('boundary-lengths',case!='boundary-lengths' or lengths==[0,1,15,16,255,256,65535,65536]);gate('real-cross-library-read',o['used_cross_codec'][0]==(case=='cross-library-interop'));gate('repeat-count',o['repeat_count'][0]==(3 if case=='repeat' else 1))
 if case=='cross-library-interop':
  producer=next(r for r in json.loads((ROOT/'migration/reports/b9-cross-interop-inputs.json').read_text()) if r['source']==source and r['producer_backend']!=backend)
  for i in nonempty:
   stream=load('cross_input_stream_'+str(i));expected=producer['streams']['gpu_compressed_'+str(i)+'.bin'];gate('opposite-vendor-captured-stream-'+str(i),hashlib.sha256(stream).hexdigest()==expected['sha256'] and len(stream)==expected['bytes'] and stream==load('decode_stream_'+str(i)))
 for i,n in enumerate(lengths):
  raw=load('input_'+str(i));hashes['input_'+str(i)]=hashlib.sha256(raw).hexdigest();gate('input-length-'+str(i),len(raw)==n)
  gpu=load('gpu_compressed_'+str(i)) if n or not bad else None
  if gpu is not None:gate('GPU-to-independent-CPU-'+str(i),decode(gpu,n,sn)==raw)
  gate('CPU-stream-valid-'+str(i),decode(load('cpu_compressed_'+str(i)),n,sn)==raw)
  if n:gate('CPU-stage-output-'+str(i),load('cpu_decoded_'+str(i))==raw)
  if not bad:gate('GPU-output-full-bytes-'+str(i),load('gpu_decoded_'+str(i))==raw)
 if bad:gate('bounded-invalid-stream-rejection',np.all(o['preflight_status']!=0) and o['bad_stream_rejected'][0]==1)
 else:gate('vendor-status-and-actual-sizes',len(o['native_status'])==len(nonempty) and np.all(o['native_status']==0) and o['actual_lengths'].astype(int).tolist()==[lengths[i] for i in nonempty] and np.all(o['preflight_status']==0))
 if 'high_level_quickstart' in source:
  if bad:gate('manager-checksum-corruption-rejected',o['manager_checksum_rejected'][0]==1)
  else:
   count=int(o['manager_roundtrips'][0]);gate('manager-original-flow',count==(34 if case=='original' else 2));cache={}
   for i in range(count):
    raw=load('manager_input_'+str(i));result=load('manager_output_'+str(i));key=hashlib.sha256(raw).hexdigest();checksum=cache.setdefault(key,crc(raw)) if key not in cache else cache[key];gate('manager-roundtrip-'+str(i),raw==result and o['manager_size_'+str(i)][0]==len(raw) and o['manager_status_'+str(i)][0]==0);gate('real-manager-API-path-'+str(i),o['manager_api_path_'+str(i)][0]==(0 if i<2 else 2 if 14<=i<24 else 1));gate('GPU-CRC32C-'+str(i),o['manager_input_crc_'+str(i)][0]==checksum and o['manager_output_crc_'+str(i)][0]==checksum)
   if case=='original':
    gate('real-same-manager-reconfigure',load('manager_reused_output')==load('manager_input_4')[:int(o['manager_reused_size'][0])]);gate('raw100-real-batch',o['raw_batch_buffers'][0]==100 and np.all(o['raw100_status']==0) and np.all(o['raw100_actual']==65536))
    for i in range(100):raw=load('raw100_input_'+str(i));gate('raw100-full-bytes-'+str(i),load('raw100_output_'+str(i))==raw and decode(load('raw100_compressed_'+str(i)),65536,False)==raw)
 return dict(status='PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED',checks=checks,input_sha256=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest(),output_values={},oracle='Independent liblz4/Google Snappy C API decoder, full byte identity, per-chunk native status/length, manager/factory/raw100 and independent CRC32C')
