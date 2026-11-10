#include <functional>
#include <cstdint>
#include <cstdio>
#include "rocket/cow_hashmap.hpp"
#include "rocket/throw.cpp"
int main() {
  for (uint32_t key=1; key<128; ++key) {
    rocket::cow_hashmap<uint32_t,bool,std::hash<uint32_t>> map;
    map.reserve(64);
    map.try_emplace(key,true);
    const auto before=map.size();
    map.clear();
    if (!map.empty()) {
      std::printf("Native API: key=%u before_clear=%zu after_clear=%zu still_found=%d\n", key,before,map.size(),map.find(key)!=map.end());
      return 1;
    }
  }
  std::puts("clear passed");
}
