# SPDX-License-Identifier: Apache-2.0
"""Torch caller for the project HIP local Canny profile."""
import ctypes,operator,os
from pathlib import Path
import torch

ROOT=Path(__file__).resolve().parents[3]
class CannyEdgeDetector:
    def __init__(self,library=None):
        if torch.version.hip is None:raise RuntimeError('ROCm Torch is required')
        self.library_path=Path(library or os.environ.get('MIGRATION_IMAGE_LIBRARY',ROOT/'build/image/libimage_canny.so')).resolve()
        self.library=ctypes.CDLL(str(self.library_path))
        self.library.rocm_image_canny_abi_version.restype=ctypes.c_uint32
        if self.library.rocm_image_canny_abi_version()!=1:raise RuntimeError('Unsupported image C ABI version')
        self.size=self.library.rocm_image_canny_workspace_size
        self.size.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.POINTER(ctypes.c_uint64)];self.size.restype=ctypes.c_int
        self.call=self.library.rocm_image_canny_local
        self.call.argtypes=[ctypes.c_void_p,ctypes.c_uint64,ctypes.c_uint64,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_void_p,ctypes.c_uint64,ctypes.c_uint64,ctypes.c_void_p,ctypes.c_uint64,ctypes.c_void_p]
        self.call.restype=ctypes.c_int

    def __call__(self,img_tensor,low_thresh,high_thresh):
        if not isinstance(img_tensor,torch.Tensor) or img_tensor.ndim!=2:raise ValueError('Expected a two-dimensional Torch image')
        low=operator.index(low_thresh);high=operator.index(high_thresh)
        h,w=img_tensor.shape
        if not(0<w<=32768 and 0<h<=32768 and 0<=low<=high<=32767):raise ValueError('Invalid dimensions or thresholds')
        # Preserve the source helper's public conversion and CPU-input behavior.
        if img_tensor.dtype!=torch.uint8:img_tensor=(img_tensor*255).byte()
        if not img_tensor.is_cuda:img_tensor=img_tensor.cuda()
        with torch.cuda.device(img_tensor.device):
            stream=torch.cuda.current_stream(img_tensor.device)
            image=img_tensor.contiguous();output=torch.empty_like(image);size=ctypes.c_uint64()
            rc=self.size(w,h,ctypes.byref(size))
            if rc:raise RuntimeError('Canny workspace query failed: '+str(rc))
            workspace=torch.empty(size.value,dtype=torch.uint8,device=image.device)
            rc=self.call(image.data_ptr(),image.numel(),image.stride(0),w,h,1,low,high,output.data_ptr(),output.numel(),output.stride(0),workspace.data_ptr(),workspace.numel(),stream.cuda_stream)
            if rc:raise RuntimeError('HIP Canny failed: '+str(rc))
            image.record_stream(stream);workspace.record_stream(stream);output.record_stream(stream)
            return output
