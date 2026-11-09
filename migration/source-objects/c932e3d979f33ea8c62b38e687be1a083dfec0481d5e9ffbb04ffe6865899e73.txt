// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <cstdlib>
#include <fstream>
#include <stdexcept>
#include <string>
namespace migration_binary {inline void emit(const char* name,const void* data,size_t bytes){const char* dir=std::getenv("MIGRATION_OUTPUT_DIR");if(!dir)throw std::runtime_error("MIGRATION_OUTPUT_DIR required");std::ofstream f(std::string(dir)+"/"+name,std::ios::binary);f.write(static_cast<const char*>(data),bytes);if(!f)throw std::runtime_error("binary observation failed");}}
