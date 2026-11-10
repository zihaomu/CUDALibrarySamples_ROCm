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
  integer(c_int) function set_values(h,nnz,values) bind(C,name='rw_sparse_set_values')
   import
   type(c_ptr),value :: h
   integer(c_int),value :: nnz
   real(c_double),intent(in) :: values(*)
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
  integer :: unit,s,j,status,count,i,k,col
  integer(c_int) :: n,nnz,nrhs,ldb,ldx,base,mtype,reorder,info,rc
  integer(c_int) :: saved_descriptor(8)
  integer(c_size_t) :: bytes
  integer(c_int),allocatable :: r(:),c(:),rp(:),cp(:),saved_r(:),saved_c(:)
  real(c_double),allocatable :: v(:),b(:),x(:),bcopy(:)
  real(c_double),allocatable :: uniform_v(:,:),uniform_b(:,:),uniform_x(:,:),residuals(:),y(:)
  real(c_double) :: af,denominator
  type(c_ptr),allocatable :: handles(:)
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
  allocate(handles(count))
  do s=1,count
   read(unit,*,iostat=status) n,nnz,nrhs,ldb,ldx,base,mtype,reorder
   if(status/=0.or.n<1.or.n>64.or.nnz<n.or.nnz>n*n.or.nrhs<1.or.nrhs>32) error stop 'shape'
   if(ldb<n.or.ldb>n+64.or.ldx<n.or.ldx>n+64) error stop 'leading dimension'
   if(profile=='uniform_batch') then
    if(s==1) then
     saved_descriptor=[n,nnz,nrhs,ldb,ldx,base,mtype,reorder]
    else
     if(any(saved_descriptor/=[n,nnz,nrhs,ldb,ldx,base,mtype,reorder])) error stop 'uniform descriptor'
    endif
   endif
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
     allocate(uniform_v(nnz,count),uniform_b(ldb*nrhs,count),uniform_x(ldx*nrhs,count))
    else
     if(size(r)/=size(saved_r).or.size(c)/=size(saved_c)) error stop 'uniform shape'
     if(any(r/=saved_r).or.any(c/=saved_c)) error stop 'uniform pattern'
    endif
   endif
   bcopy=b
   rc=create(n,nnz,r,c,v,base,mtype,reorder,h);call check(rc)
   handles(s)=h
   rc=analyze(h,rp,cp,bytes);call check(rc)
   if(bytes/=int(n,c_size_t)*c_sizeof(rp(1))) error stop 'query byte count'
   if(any(rp<base).or.any(rp>=n+base).or.any(cp<base).or.any(cp>=n+base)) error stop 'permutation range'
   rc=solve(h,nrhs,b,ldb,x,ldx,info);call check(rc)
   if(any(b/=bcopy)) error stop 'RHS was mutated'
   if(any(.not.ieee_is_finite(x))) error stop 'nonfinite solution'
   if(profile=='residual'.and.info==0) then
    allocate(residuals(nrhs+1),y(n));af=sqrt(sum(v*v))
    do j=1,nrhs
     y=0
     do i=1,n
      do k=r(i)-base+1,r(i+1)-base
       col=c(k)-base+1
       y(i)=y(i)+v(k)*x((j-1)*ldx+col)
      enddo
     enddo
     y=y-b((j-1)*ldb+1:(j-1)*ldb+n)
     denominator=af*sqrt(sum(x((j-1)*ldx+1:(j-1)*ldx+n)**2)) &
        +sqrt(sum(b((j-1)*ldb+1:(j-1)*ldb+n)**2))
     if(denominator>0) then
      residuals(j)=sqrt(sum(y*y))/denominator
     else
      residuals(j)=sqrt(sum(y*y))
     endif
    enddo
    residuals(nrhs+1)=maxval(residuals(1:nrhs))
    path=trim(output)//'/'//trim(label)//'_fortran_residual.bin'
    open(newunit=j,file=trim(path),access='stream',form='unformatted',status='replace');write(j) residuals;close(j)
    if(any(.not.ieee_is_finite(residuals)).or.residuals(nrhs+1)>1.0e-12_c_double) error stop 2
    deallocate(residuals,y)
   endif
   rc=export(h,trim(label)//c_null_char);call check(rc)
   path=trim(output)//'/'//trim(label)//'_fortran_X.bin'
   open(newunit=j,file=trim(path),access='stream',form='unformatted',status='replace');write(j) x;close(j)
   path=trim(output)//'/'//trim(label)//'_fortran_permutation.bin'
   open(newunit=j,file=trim(path),access='stream',form='unformatted',status='replace');write(j) rp,cp;close(j)
   path=trim(output)//'/'//trim(label)//'_fortran_query_bytes.bin'
   open(newunit=j,file=trim(path),access='stream',form='unformatted',status='replace');write(j) bytes;close(j)
   if(profile=='uniform_batch') then
    uniform_v(:,s)=v;uniform_b(:,s)=b;uniform_x(:,s)=x
   else
    rc=destroy(h);call check(rc)
   endif
   if(info/=0) then
    print *, 'numerical info propagated to Fortran:',info
    error stop 2
   endif
   deallocate(r,c,v,b,x,bcopy,rp,cp)
  enddo
  close(unit)
  if(profile=='uniform_batch') then
   ! Original UBATCH_INDEX=1 selects the second retained factor; the output
   ! matrix pointer stays at slot zero. No analysis or other factor is rebuilt.
   allocate(x(ldx*nrhs));x=uniform_x(:,1)
   rc=set_values(handles(2),nnz,uniform_v(:,2));call check(rc)
   rc=solve(handles(2),nrhs,uniform_b(:,2),ldb,x,ldx,info);call check(rc)
   if(info/=0) error stop 2
   rc=export(handles(2),'selected'//c_null_char);call check(rc)
   uniform_x(:,1)=x
   path=trim(output)//'/selected_fortran_X.bin'
   open(newunit=j,file=trim(path),access='stream',form='unformatted',status='replace');write(j) x;close(j)
   path=trim(output)//'/uniform_final_X.bin'
   open(newunit=j,file=trim(path),access='stream',form='unformatted',status='replace');write(j) uniform_x;close(j)
   path=trim(output)//'/selection.bin'
   open(newunit=j,file=trim(path),access='stream',form='unformatted',status='replace')
   write(j) 1_c_int,0_c_int,2_c_int
   close(j)
   rc=export(handles(1),'retained_b0'//c_null_char);call check(rc)
   rc=export(handles(2),'retained_b1'//c_null_char);call check(rc)
   do s=1,count
    rc=destroy(handles(s));call check(rc)
   enddo
   deallocate(x,uniform_v,uniform_b,uniform_x)
  endif
  print *, 'PASSED standard Fortran + HIP: ',profile
 end subroutine
end module
