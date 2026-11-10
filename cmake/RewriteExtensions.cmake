file(READ "${CMAKE_CURRENT_SOURCE_DIR}/../migration/rewrite/extensions.json" _extensions)
string(JSON _extension_count LENGTH "${_extensions}" profiles)
math(EXPR _extension_last "${_extension_count}-1")
file(GLOB_RECURSE _extension_headers CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/backends/*.hpp" "${CMAKE_CURRENT_SOURCE_DIR}/common/rewrite*.hpp")
foreach(_i RANGE ${_extension_last})
 string(JSON _kind GET "${_extensions}" profiles ${_i} kind)
 string(JSON _implementation GET "${_extensions}" profiles ${_i} implementation)
 set(_binary "${CMAKE_CURRENT_BINARY_DIR}/rewrite_ext_${_kind}.bin")
 set(_extra_links "")
 if(_kind STREQUAL "svd")
  set(_extra_links -lhipsolver)
 endif()
 add_custom_command(OUTPUT "${_binary}"
  COMMAND "${MIGRATION_HIPCC}" "--rocm-path=${_overlay}" "--hip-path=${_overlay}"
   "--rocm-device-lib-path=${ROCM_CORE_ROOT}/lib/llvm/amdgcn/bitcode" "--offload-arch=${MIGRATION_AMD_ARCH}"
   -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ -x hip "${CMAKE_CURRENT_SOURCE_DIR}/../${_implementation}" -o "${_binary}"
   "-I${CMAKE_CURRENT_SOURCE_DIR}/common" "-I${CMAKE_CURRENT_SOURCE_DIR}/backends/image" "-I${CMAKE_CURRENT_SOURCE_DIR}/backends/solver"
   "-I${CMAKE_CURRENT_SOURCE_DIR}/backends/sparse" "-I${CMAKE_CURRENT_SOURCE_DIR}/backends/codec"
   "-I${ROCM_CORE_ROOT}/include" "-I${ROCM_MATH_INCLUDE}" "-L/opt/rocm/core-10.1/lib"
   "-L${ROCM_LIBRARIES_ROOT}/lib" "-L${ROCM_CORE_ROOT}/lib" "-Wl,-rpath,${ROCM_LIBRARIES_ROOT}/lib"
   "-Wl,-rpath,${ROCM_CORE_ROOT}/lib" -lhipblas -lamdhip64 ${_extra_links}
  DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/../${_implementation}" ${_extension_headers} VERBATIM)
 add_custom_target(rewrite_ext_${_kind} DEPENDS "${_binary}")
endforeach()
