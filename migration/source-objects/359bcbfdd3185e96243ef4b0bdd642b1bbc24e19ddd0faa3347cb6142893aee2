# Both builders record immutable compiler commands, source closure and binaries.
# The six nvfortran-origin helpers use the standard Fortran ISO_C_BINDING port.
add_custom_target(rewrite_matrix_helpers
 COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/../tools/moat/build_helpers.py"
 WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/.."
 COMMENT "Build nine C++/Fortran matrix helper entrypoints and shared HIP storage ABI"
 VERBATIM)
add_custom_target(rewrite_crc32_benchmark
 COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/../tools/moat/build_crc_benchmark.py"
 WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/.."
 COMMENT "Build original CRC32 benchmark harness with project HIP CRC search backend"
 VERBATIM)
