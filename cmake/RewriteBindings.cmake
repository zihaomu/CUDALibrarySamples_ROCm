# Fortran is a real entrypoint, linked through ISO_C_BINDING to the shared HIP core.
# The recorder preserves compiler commands, hashes, failures and all eight binaries.
find_package(Python3 COMPONENTS Interpreter REQUIRED)
add_custom_target(rewrite_sparse_bindings
 COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/../tools/moat/build_sparse_bindings.py"
 WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/.."
 COMMENT "Build eight standard Fortran sparse samples and the shared HIP C ABI"
 VERBATIM)
