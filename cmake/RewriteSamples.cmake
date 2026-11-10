# The locked profile selects the target architecture; kernels keep portable code.
file(READ "${CMAKE_CURRENT_SOURCE_DIR}/../migration/rewrite/first-eight.json" _rewrite_spec)
string(JSON _rewrite_count LENGTH "${_rewrite_spec}" profiles)
math(EXPR _rewrite_last "${_rewrite_count}-1")
file(GLOB_RECURSE _rewrite_headers CONFIGURE_DEPENDS
 "${CMAKE_CURRENT_SOURCE_DIR}/common/rewrite*.hpp"
 "${CMAKE_CURRENT_SOURCE_DIR}/backends/*.hpp"
 "${CMAKE_CURRENT_SOURCE_DIR}/device/*.hpp")
foreach(_i RANGE ${_rewrite_last})
 string(JSON _kind GET "${_rewrite_spec}" profiles ${_i} kind)
 string(JSON _source GET "${_rewrite_spec}" profiles ${_i} source)
 set(_binary "${CMAKE_CURRENT_BINARY_DIR}/rewrite_${_kind}.bin")
 add_custom_command(OUTPUT "${_binary}"
  COMMAND "${MIGRATION_HIPCC}" "--rocm-path=${_overlay}" "--hip-path=${_overlay}"
   "--rocm-device-lib-path=${ROCM_CORE_ROOT}/lib/llvm/amdgcn/bitcode"
   "--offload-arch=${MIGRATION_AMD_ARCH}" -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ -x hip
   "${CMAKE_CURRENT_SOURCE_DIR}/ported/${_source}" -o "${_binary}"
   "-I${CMAKE_CURRENT_SOURCE_DIR}/common" "-I${CMAKE_CURRENT_SOURCE_DIR}/backends/blas"
   "-I${CMAKE_CURRENT_SOURCE_DIR}/device/solver" "-I${ROCM_CORE_ROOT}/include" "-I${ROCM_MATH_INCLUDE}"
   "-L/opt/rocm/core-10.1/lib" "-L${ROCM_LIBRARIES_ROOT}/lib" "-L${ROCM_CORE_ROOT}/lib"
   "-Wl,-rpath,${ROCM_LIBRARIES_ROOT}/lib" "-Wl,-rpath,${ROCM_CORE_ROOT}/lib"
   -lhipblas -lamdhip64
  DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/ported/${_source}" ${_rewrite_headers}
  VERBATIM)
 add_custom_target(rewrite_${_kind} DEPENDS "${_binary}")
endforeach()
