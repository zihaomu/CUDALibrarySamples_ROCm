# SPDX-License-Identifier: Apache-2.0
"""Three-channel Canny with an explicit classical connected-hysteresis profile."""
import ctypes,operator,os
from pathlib import Path
import torch
ROOT=Path(__file__).resolve().parents[3]

class NPPCanny:
    def __init__(self,library=None):
        if torch.version.hip is None:raise RuntimeError('ROCm Torch is required')
        self.library_path=Path(library or os.environ.get('MIGRATION_IMAGE_COLOR_LIBRARY',ROOT/'build/image/libimage_canny_color.so')).resolve();self.library=ctypes.CDLL(str(self.library_path))
        self.library.rocm_image_canny_color_abi_version.restype=ctypes.c_uint32
        if self.library.rocm_image_canny_color_abi_version()!=1:raise RuntimeError('Unsupported color Canny ABI version')
        self.size=self.library.rocm_image_canny_color_workspace_size;self.size.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.POINTER(ctypes.c_uint64)];self.size.restype=ctypes.c_int
        self.call=self.library.rocm_image_canny_color;self.call.argtypes=[ctypes.c_void_p,ctypes.c_uint64,ctypes.c_uint64,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_void_p,ctypes.c_uint64,ctypes.c_uint64,ctypes.c_void_p,ctypes.c_uint64,ctypes.c_void_p];self.call.restype=ctypes.c_int

    def tensor(self,image,low=50,high=100):
        if not isinstance(image,torch.Tensor) or image.ndim!=3 or image.shape[2]!=3:raise ValueError('Expected a HWC three-channel Torch image')
        h,w,_=image.shape;lo,hi=operator.index(low),operator.index(high)
        if not(0<w<=32768 and 0<h<=32768 and 0<=lo<=hi<=32767):raise ValueError('Invalid dimensions or thresholds')
        image=image.to(torch.uint8)
        if not image.is_cuda:image=image.cuda()
        with torch.cuda.device(image.device):
            stream=torch.cuda.current_stream(image.device);image=image.contiguous();out=torch.empty((h,w),dtype=torch.uint8,device=image.device);size=ctypes.c_uint64();rc=self.size(w,h,ctypes.byref(size))
            if rc:raise RuntimeError('Color Canny workspace query: '+str(rc))
            workspace=torch.empty(size.value,dtype=torch.uint8,device=image.device)
            rc=self.call(image.data_ptr(),image.numel(),image.stride(0),w,h,lo,hi,out.data_ptr(),out.numel(),out.stride(0),workspace.data_ptr(),workspace.numel(),stream.cuda_stream)
            if rc:raise RuntimeError('HIP color Canny: '+str(rc))
            image.record_stream(stream);workspace.record_stream(stream);out.record_stream(stream);return out

    def detect(self,image,low=50,high=100):
        return self.tensor(torch.from_numpy(image),low,high).cpu().numpy()
