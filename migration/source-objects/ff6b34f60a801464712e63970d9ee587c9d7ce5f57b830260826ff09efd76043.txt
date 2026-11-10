#include <cstdlib>
#include <fstream>
#include <string>
#include <vector>
template<class T> void native_emit(const char*name,const std::vector<T>&v,size_t count=0){const char*p=std::getenv("NATIVE_CAPTURE_OUTPUT");if(!p)return;if(!count)count=v.size();std::ofstream f(std::string(p)+"/"+name+".bin",std::ios::binary);f.write(reinterpret_cast<const char*>(v.data()),sizeof(T)*count);}
