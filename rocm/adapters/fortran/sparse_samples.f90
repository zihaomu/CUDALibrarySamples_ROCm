! SPDX-License-Identifier: Apache-2.0
! Original sample contracts, standard Fortran arrays and a narrow C ABI.
module rewrite_sparse_samples
 use iso_c_binding
 use, intrinsic :: ieee_arithmetic
 implicit none
 interface
  integer(c_int) function create(n,nnz,r,c,v,base,mtype,reorder,h) bind(C,name='rw_sparse_create')
   import
   integer(c_int),value :: n,nnz,base,mtype,reorder
   integer(c_int),intent(in) :: r(*),c(*)
   real(c_double),intent(in) :: v(*)
   type(c_ptr),intent(out) :: h
  end function
  integer(c_int) function analyze(h,rp,cp,bytes) bind(C,name='rw_sparse_analyze')
   import
   type(c_ptr),value :: h
   integer(c_int),intent(out) :: rp(*),cp(*)
   integer(c_size_t),intent(out) :: bytes
  end function
  integer(c_int) function solve(h,nrhs,b,ldb,x,ldx,info) bind(C,name='rw_sparse_solve')
   import
   type(c_ptr),value :: h
   integer(c_int),value :: nrhs,ldb,ldx
   real(c_double),intent(in) :: b(*)
   real(c_double),intent(inout) :: x(*)
   integer(c_int),intent(out) :: info
  end function
  integer(c_int) function export(h,label) bind(C,name='rw_sparse_export')
   import
   type(c_ptr),value :: h
   character(c_char),intent(in) :: label(*)
  end function
  integer(c_int) function destroy(h) bind(C,name='rw_sparse_destroy')
   import
   type(c_ptr),value :: h
  end function
 end interface
contains
 subroutine check(status)
  integer(c_int),intent(in) :: status
  if(status/=0) then
   print *, 'C ABI error propagated to Fortran:',status
   error stop 1
  endif
 end subroutine
 subroutine run_sparse_sample(profile)
  character(*),intent(in) :: profile
  character(4096) :: input,output,path
  character(32) :: kind,label
  integer :: unit,s,j,status,count
  integer(c_int) :: n,nnz,nrhs,ldb,ldx,base,mtype,reorder,info,rc
  integer(c_size_t) :: bytes
  integer(c_int),allocatable :: r(:),c(:),rp(:),cp(:),saved_r(:),saved_c(:)
  real(c_double),allocatable :: v(:),b(:),x(:),bcopy(:)
  type(c_ptr) :: h
  call get_environment_variable('REWRITE_INPUT',input,status=status)
  if(status/=0.or.len_trim(input)==0) error stop 'REWRITE_INPUT required'
  call get_environment_variable('REWRITE_OUTPUT',output,status=status)
  if(status/=0.or.len_trim(output)==0) error stop 'REWRITE_OUTPUT required'
  open(newunit=unit,file=trim(input)//'/config.txt',status='old',action='read',iostat=status)
  if(status/=0) error stop 'missing config'
  read(unit,*,iostat=status) kind,count
  if(status/=0.or.trim(kind)/=profile.or.count<1.or.count>16) error stop 'profile/batch descriptor'
  if((profile=='batch'.or.profile=='uniform_batch').and.count/=2) error stop 'batch count'
  if((profile=='reordering_phase'.or.profile=='residual').and.count/=1) error stop 'single count'
  do s=1,count
   read(unit,*,iostat=status) n,nnz,nrhs,ldb,ldx,base,mtype,reorder
   if(status/=0.or.n<1.or.n>64.or.nnz<n.or.nnz>n*n.or.nrhs<1.or.nrhs>32) error stop 'shape'
   if(ldb<n.or.ldb>n+64.or.ldx<n.or.ldx>n+64) error stop 'leading dimension'
   write(label,'("b",i0)') s-1
   allocate(r(n+1),c(nnz),v(nnz),b(ldb*nrhs),x(ldx*nrhs),bcopy(ldb*nrhs),rp(n),cp(n))
   path=trim(input)//'/'//trim(label)//'_rows.bin'
   open(newunit=j,file=trim(path),access='stream',form='unformatted',status='old');read(j) r;close(j)
   path=trim(input)//'/'//trim(label)//'_columns.bin'
   open(newunit=j,file=trim(path),access='stream',form='unformatted',status='old');read(j) c;close(j)
   path=trim(input)//'/'//trim(label)//'_values.bin'
   open(newunit=j,file=trim(path),access='stream',form='unformatted',status='old');read(j) v;close(j)
   path=trim(input)//'/'//trim(label)//'_B.bin'
   open(newunit=j,file=trim(path),access='stream',form='unformatted',status='old');read(j) b;close(j)
   path=trim(input)//'/'//trim(label)//'_X.bin'
   open(newunit=j,file=trim(path),access='stream',form='unformatted',status='old');read(j) x;close(j)
   if(profile=='uniform_batch') then
    if(s==1) then
     saved_r=r;saved_c=c
    else
     if(size(r)/=size(saved_r).or.size(c)/=size(saved_c)) error stop 'uniform shape'
     if(any(r/=saved_r).or.any(c/=saved_c)) error stop 'uniform pattern'
    endif
   endif
   bcopy=b
   rc=create(n,nnz,r,c,v,base,mtype,reorder,h);call check(rc)
   rc=analyze(h,rp,cp,bytes);call check(rc)
   if(bytes/=int(n,c_size_t)*c_sizeof(rp(1))) error stop 'query byte count'
   if(any(rp<base).or.any(rp>=n+base).or.any(cp<base).or.any(cp>=n+base)) error stop 'permutation range'
   rc=solve(h,nrhs,b,ldb,x,ldx,info);call check(rc)
   if(any(b/=bcopy)) error stop 'RHS was mutated'
   if(any(.not.ieee_is_finite(x))) error stop 'nonfinite solution'
   rc=export(h,trim(label)//c_null_char);call check(rc)
   path=trim(output)//'/'//trim(label)//'_fortran_X.bin'
   open(newunit=j,file=trim(path),access='stream',form='unformatted',status='replace');write(j) x;close(j)
   path=trim(output)//'/'//trim(label)//'_fortran_permutation.bin'
   open(newunit=j,file=trim(path),access='stream',form='unformatted',status='replace');write(j) rp,cp;close(j)
   path=trim(output)//'/'//trim(label)//'_fortran_query_bytes.bin'
   open(newunit=j,file=trim(path),access='stream',form='unformatted',status='replace');write(j) bytes;close(j)
   rc=destroy(h);call check(rc)
   if(info/=0) then
    print *, 'numerical info propagated to Fortran:',info
    error stop 2
   endif
   deallocate(r,c,v,b,x,bcopy,rp,cp)
  enddo
  close(unit)
  print *, 'PASSED standard Fortran + HIP: ',profile
 end subroutine
end module
