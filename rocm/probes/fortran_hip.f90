! SPDX-License-Identifier: Apache-2.0
program hip_iso_c_binding_roundtrip
  use iso_c_binding
  implicit none
  interface
    function hipMalloc(p,n) bind(c,name='hipMalloc') result(rc)
      import
      type(c_ptr) :: p
      integer(c_size_t),value :: n
      integer(c_int) :: rc
    end function
    function hipMemcpy(dst,src,n,kind) bind(c,name='hipMemcpy') result(rc)
      import
      type(c_ptr),value :: dst,src
      integer(c_size_t),value :: n
      integer(c_int),value :: kind
      integer(c_int) :: rc
    end function
    function hipFree(p) bind(c,name='hipFree') result(rc)
      import
      type(c_ptr),value :: p
      integer(c_int) :: rc
    end function
  end interface
  integer(c_int),target :: input(4)=[1,3,7,13],output(4)=0
  type(c_ptr) :: device
  integer(c_int) :: rc
  rc=hipMalloc(device,16_c_size_t)
  if(rc/=0)stop 1
  rc=hipMemcpy(device,c_loc(input),16_c_size_t,1_c_int)
  if(rc/=0)stop 2
  rc=hipMemcpy(c_loc(output),device,16_c_size_t,2_c_int)
  if(rc/=0)stop 3
  if(any(input/=output))stop 4
  rc=hipFree(device)
  if(rc/=0)stop 5
  print *, '{"case":"fortran-iso-c-hip-roundtrip","passed":true}'
end program
