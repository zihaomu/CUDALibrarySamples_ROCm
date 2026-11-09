// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <iomanip>
#include <iostream>
#include <vector>
namespace rng_observer {
template<class T>void emit(const std::vector<T>& v){long double sum=0,sum2=0,ls=0,ls2=0;bool finite=true,positive=true,integer=true;uint64_t hash=1469598103934665603ull;for(T x:v){long double y=x;finite&=std::isfinite(y);positive&=y>0;integer&=std::floor(y)==y;sum+=y;sum2+=y*y;if(y>0){long double l=std::log(y);ls+=l;ls2+=l*l;}unsigned char raw[sizeof(T)];std::memcpy(raw,&x,sizeof(T));for(auto b:raw){hash^=b;hash*=1099511628211ull;}}long double m=sum/v.size(),lm=ls/v.size();std::cout<<std::setprecision(17)<<"{\"rng_observation\":true,\"n\":"<<v.size()<<",\"mean\":"<<double(m)<<",\"variance\":"<<double(sum2/v.size()-m*m)<<",\"log_mean\":"<<double(lm)<<",\"log_variance\":"<<double(ls2/v.size()-lm*lm)<<",\"finite\":"<<(finite?"true":"false")<<",\"positive\":"<<(positive?"true":"false")<<",\"integer\":"<<(integer?"true":"false")<<",\"min\":"<<*std::min_element(v.begin(),v.end())<<",\"max\":"<<*std::max_element(v.begin(),v.end())<<",\"hash\":\""<<hash<<"\"}"<<std::endl;}
}
