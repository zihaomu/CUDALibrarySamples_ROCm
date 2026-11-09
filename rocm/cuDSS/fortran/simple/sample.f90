! SPDX-License-Identifier: Apache-2.0
! Standard Fortran replacement of the original cuDSS simple binding/device syntax.
program sparse_cholesky_rocm
 use iso_c_binding
 use ieee_arithmetic
 implicit none
 interface
  function rocm_sparse_chol(n,nnz,rows,cols,vals,base,b,x) bind(c) result(rc)
   import
   integer(c_int),value :: n,nnz,base
   integer(c_int) :: rows(*),cols(*)
   real(c_double) :: vals(*),b(*),x(*)
   integer(c_int) :: rc
  end function
 end interface
 integer(c_int) :: rows(6)=[1,3,5,7,8,9],cols(8)=[1,3,2,3,3,5,4,5],rc
 real(c_double) :: vals(8)=[4d0,1d0,3d0,2d0,5d0,1d0,1d0,2d0]
 real(c_double) :: b(5)=[7d0,12d0,25d0,4d0,13d0],x(5),ax(5)
 integer :: i,j,q
 rc=rocm_sparse_chol(5_c_int,8_c_int,rows,cols,vals,1_c_int,b,x)
 if(rc/=0) stop 1
 if(any(.not.ieee_is_finite(x)))stop 2
 if(maxval(abs(x-[1d0,2d0,3d0,4d0,5d0]))>2d-15)stop 3
 print *, '{"case":"original-one-based-spd-fortran-solution","passed":true}'
 ax=0d0
 do i=1,5
  do q=rows(i),rows(i+1)-1
   j=cols(q);ax(i)=ax(i)+vals(q)*x(j)
   if(i/=j) ax(j)=ax(j)+vals(q)*x(i)
  end do
 end do
 if(maxval(abs(ax-b))>1d-11)stop 4
 print *, '{"case":"original-one-based-spd-fortran-residual","passed":true}'
end program
