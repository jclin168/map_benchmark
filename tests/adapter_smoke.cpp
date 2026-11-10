#include "Map.h"
#include <cstdint>
#include <cstdio>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <unordered_map>
void require(bool b) { if (!b) throw std::runtime_error("adapter smoke mismatch"); }
template<class K> void test(const K& missing) {
    Map<K,uint64_t> map;
    std::unordered_map<K,uint64_t> ref;
    map.reserve(1000);
    for (size_t i=0;i<1000;++i) {
        K k;
        if constexpr(std::is_same<K,std::string>::value) k="key-"+std::to_string(i);
        else k=static_cast<K>(i);
        auto a=map.emplace(k,i);auto b=ref.emplace(k,i);
        require(a.second==b.second);
        require(!map.emplace(k,i+1).second);
    }
    require(map.size()==ref.size()&&map.find(missing)==map.end());
    const auto& c=map;
    for(const auto& kv:ref)require(c.find(kv.first)!=c.end()&&c.find(kv.first)->second==kv.second);
    auto copy=map;
    for(auto it=ref.begin();it!=ref.end();) {
        auto k=it->first;
        if(it->second%2==0) {require(map.erase(k)==1);it=ref.erase(it);}else ++it;
    }
    require(copy.size()==1000&&map.size()==ref.size());
    uint64_t sum=0,expected=0;
    for(auto& kv:map)sum+=kv.second;
    for(auto& kv:ref)expected+=kv.second;
    require(sum==expected);
    auto k=map.begin()->first;map.erase(map.begin());ref.erase(k);require(map.size()==ref.size());
    map.clear();require(map.empty());map[missing]=123;require(map.find(missing)->second==123);
#ifdef MAP_BENCH_GOOGLE_ADAPTER
    bool rejected=false;
    try {map[GoogleBenchmarkMarkers<K>::deleted()]=1;}catch(const std::invalid_argument&){rejected=true;}
    require(rejected);
#endif
}
int main(){test<uint64_t>(9000000);test<int>(9000000);test<std::string>("absent");std::puts("adapter smoke PASS");}
