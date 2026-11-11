!mod$ v1 sum:e04052032b347bb5
!need$ d373ac43db7bb26e i iso_c_binding
!need$ d676699be0556005 i __fortran_builtins
module rewrite_helper_samples
use,intrinsic::iso_c_binding,only:c_associated
use,intrinsic::iso_c_binding,only:c_funloc
use,intrinsic::iso_c_binding,only:c_funptr
use,intrinsic::iso_c_binding,only:c_f_pointer
use,intrinsic::iso_c_binding,only:c_f_strpointer
use,intrinsic::iso_c_binding,only:c_loc
use,intrinsic::iso_c_binding,only:c_null_funptr
use,intrinsic::iso_c_binding,only:c_null_ptr
use,intrinsic::iso_c_binding,only:c_ptr
use,intrinsic::iso_c_binding,only:c_sizeof
use,intrinsic::iso_c_binding,only:f_c_string
use,intrinsic::iso_c_binding,only:operator(==)
use,intrinsic::iso_c_binding,only:operator(/=)
use,intrinsic::iso_c_binding,only:c_int8_t
use,intrinsic::iso_c_binding,only:c_int16_t
use,intrinsic::iso_c_binding,only:c_int32_t
use,intrinsic::iso_c_binding,only:c_int64_t
use,intrinsic::iso_c_binding,only:c_int128_t
use,intrinsic::iso_c_binding,only:c_int
use,intrinsic::iso_c_binding,only:c_short
use,intrinsic::iso_c_binding,only:c_long
use,intrinsic::iso_c_binding,only:c_long_long
use,intrinsic::iso_c_binding,only:c_signed_char
use,intrinsic::iso_c_binding,only:c_size_t
use,intrinsic::iso_c_binding,only:c_intmax_t
use,intrinsic::iso_c_binding,only:c_intptr_t
use,intrinsic::iso_c_binding,only:c_ptrdiff_t
use,intrinsic::iso_c_binding,only:c_int_least8_t
use,intrinsic::iso_c_binding,only:c_int_fast8_t
use,intrinsic::iso_c_binding,only:c_int_least16_t
use,intrinsic::iso_c_binding,only:c_int_fast16_t
use,intrinsic::iso_c_binding,only:c_int_least32_t
use,intrinsic::iso_c_binding,only:c_int_fast32_t
use,intrinsic::iso_c_binding,only:c_int_least64_t
use,intrinsic::iso_c_binding,only:c_int_fast64_t
use,intrinsic::iso_c_binding,only:c_int_least128_t
use,intrinsic::iso_c_binding,only:c_int_fast128_t
use,intrinsic::iso_c_binding,only:c_float
use,intrinsic::iso_c_binding,only:c_double
use,intrinsic::iso_c_binding,only:c_long_double
use,intrinsic::iso_c_binding,only:c_float_complex
use,intrinsic::iso_c_binding,only:c_double_complex
use,intrinsic::iso_c_binding,only:c_long_double_complex
use,intrinsic::iso_c_binding,only:c_bool
use,intrinsic::iso_c_binding,only:c_char
use,intrinsic::iso_c_binding,only:c_null_char
use,intrinsic::iso_c_binding,only:c_alert
use,intrinsic::iso_c_binding,only:c_backspace
use,intrinsic::iso_c_binding,only:c_form_feed
use,intrinsic::iso_c_binding,only:c_new_line
use,intrinsic::iso_c_binding,only:c_carriage_return
use,intrinsic::iso_c_binding,only:c_horizontal_tab
use,intrinsic::iso_c_binding,only:c_vertical_tab
use,intrinsic::iso_c_binding,only:c_float16
use,intrinsic::iso_c_binding,only:c_float16_complex
use,intrinsic::iso_c_binding,only:c_float128
use,intrinsic::iso_c_binding,only:c_float128_complex
use,intrinsic::iso_c_binding,only:c_uint8_t
use,intrinsic::iso_c_binding,only:c_uint16_t
use,intrinsic::iso_c_binding,only:c_uint32_t
use,intrinsic::iso_c_binding,only:c_uint64_t
use,intrinsic::iso_c_binding,only:c_uint128_t
use,intrinsic::iso_c_binding,only:c_unsigned_char
use,intrinsic::iso_c_binding,only:c_unsigned_short
use,intrinsic::iso_c_binding,only:c_unsigned
use,intrinsic::iso_c_binding,only:c_unsigned_long
use,intrinsic::iso_c_binding,only:c_unsigned_long_long
use,intrinsic::iso_c_binding,only:c_uintmax_t
use,intrinsic::iso_c_binding,only:c_uint_fast8_t
use,intrinsic::iso_c_binding,only:c_uint_fast16_t
use,intrinsic::iso_c_binding,only:c_uint_fast32_t
use,intrinsic::iso_c_binding,only:c_uint_fast64_t
use,intrinsic::iso_c_binding,only:c_uint_fast128_t
use,intrinsic::iso_c_binding,only:c_uint_least8_t
use,intrinsic::iso_c_binding,only:c_uint_least16_t
use,intrinsic::iso_c_binding,only:c_uint_least32_t
use,intrinsic::iso_c_binding,only:c_uint_least64_t
use,intrinsic::iso_c_binding,only:c_uint_least128_t
use,intrinsic::iso_c_binding,only:c_f_procpointer
use,intrinsic::__fortran_builtins,only:iso_c_binding$__fortran_builtins$c_associated_c_ptr=>c_associated_c_ptr
private::iso_c_binding$__fortran_builtins$c_associated_c_ptr
type,bind(c)::query_t
integer(8)::sizes(1_8:5_8)
type(c_ptr)::pointers(1_8:8_8)
integer(4)::codes(1_8:8_8)
end type
interface
function malloc_gpu(p,n) bind(c,name="mh_alloc")
import::c_ptr
type(c_ptr),intent(out)::p
integer(8),value::n
integer(4)::malloc_gpu
end
end interface
interface
function upload(p,h,n) bind(c,name="mh_upload")
import::c_ptr
type(c_ptr),value::p
type(c_ptr),value::h
integer(8),value::n
integer(4)::upload
end
end interface
interface
function free_gpu(p) bind(c,name="mh_free")
import::c_ptr
type(c_ptr),value::p
integer(4)::free_gpu
end
end interface
interface
function create(f,b,nr,nc,nz,ld,r,c,v,base,h) bind(c,name="mh_create")
import::c_ptr
integer(4),value::f
integer(4),value::b
type(c_ptr),value::nr
type(c_ptr),value::nc
type(c_ptr),value::nz
type(c_ptr),value::ld
type(c_ptr),value::r
type(c_ptr),value::c
type(c_ptr),value::v
integer(4),value::base
type(c_ptr),intent(out)::h
integer(4)::create
end
end interface
interface
function get(h,q,mask) bind(c,name="mh_get")
import::c_ptr
import::query_t
type(c_ptr),value::h
type(query_t),intent(inout)::q
integer(4),value::mask
integer(4)::get
end
end interface
interface
function set_values(h,v) bind(c,name="mh_set_values")
import::c_ptr
type(c_ptr),value::h
type(c_ptr),value::v
integer(4)::set_values
end
end interface
interface
function set_csr(h,r,c,v) bind(c,name="mh_set_csr")
import::c_ptr
type(c_ptr),value::h
type(c_ptr),value::r
type(c_ptr),value::c
type(c_ptr),value::v
integer(4)::set_csr
end
end interface
interface
function destroy(h) bind(c,name="mh_destroy")
import::c_ptr
type(c_ptr),value::h
integer(4)::destroy
end
end interface
interface
function snapshot(name,q,r,c,v,nr,nc,nz,ld) bind(c,name="mh_snapshot")
import::c_ptr
import::query_t
character(1_4,1),intent(in)::name(1_8:*)
type(query_t),intent(in)::q
type(c_ptr),value::r
type(c_ptr),value::c
type(c_ptr),value::v
type(c_ptr),value::nr
type(c_ptr),value::nc
type(c_ptr),value::nz
type(c_ptr),value::ld
integer(4)::snapshot
end
end interface
interface
function save(name,p,n) bind(c,name="mh_save")
import::c_ptr
character(1_4,1),intent(in)::name(1_8:*)
type(c_ptr),value::p
integer(8),value::n
integer(4)::save
end
end interface
interface
function query_bytes() bind(c,name="mh_query_bytes")
integer(8)::query_bytes
end
end interface
contains
subroutine check(rc)
integer(4),intent(in)::rc
end
subroutine run_helper(expected)
integer(4),intent(in)::expected
end
end
