// SPDX-License-Identifier: Apache-2.0
// Probe the real parser boundary. Rejection is not evidence of a JPEG2000/TIFF port.
#include <rocjpeg/rocjpeg.h>
#include <fstream>
#include <iterator>
#include <iostream>
#include <vector>
int main(int argc,char**argv){if(argc!=2)return 2;std::ifstream f(argv[1],std::ios::binary);std::vector<unsigned char>bytes((std::istreambuf_iterator<char>(f)),{});if(bytes.empty())return 2;RocJpegStreamHandle stream=nullptr;auto create=rocJpegStreamCreate(&stream);if(create!=ROCJPEG_STATUS_SUCCESS)return 3;auto parse=rocJpegStreamParse(bytes.data(),bytes.size(),stream);auto destroy=rocJpegStreamDestroy(stream);std::cout<<"{\"bytes\":"<<bytes.size()<<",\"parse_status\":"<<int(parse)<<",\"destroy_status\":"<<int(destroy)<<"}\n";return parse!=ROCJPEG_STATUS_SUCCESS&&destroy==ROCJPEG_STATUS_SUCCESS?0:1;}
