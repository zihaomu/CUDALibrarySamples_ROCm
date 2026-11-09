// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <cmath>
#include <iomanip>
#include <iostream>
#include <type_traits>
#include <utility>
namespace migration_observer {
template<class T,class=void>struct has_xy:std::false_type{};
template<class T>struct has_xy<T,std::void_t<decltype(std::declval<T>().x),decltype(std::declval<T>().y)>>:std::true_type{};
template<class T>void value(T v){
 if constexpr(std::is_arithmetic_v<T>){double d=double(v);if(std::isfinite(d))std::cout<<d;else std::cout<<"null";}
 else if constexpr(has_xy<T>::value){std::cout<<'[';value(v.x);std::cout<<',';value(v.y);std::cout<<']';}
 else {value(float(v));}
}
template<class T>void emit(const char* name,const T* data,size_t count){
 std::cout<<std::setprecision(17)<<"{\"observe\":\""<<name<<"\",\"values\":[";
 for(size_t i=0;i<count;i++){if(i)std::cout<<',';value(data[i]);}std::cout<<"]}"<<std::endl;
}
}
