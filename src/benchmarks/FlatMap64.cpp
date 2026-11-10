// A controlled 64-bit profile within map_benchmark's existing registry/timer.
#include "bench.h"
#include <algorithm>
#include <cstdlib>
#include <limits>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>
namespace {
uint64_t permute64(uint64_t x) {
    x += UINT64_C(0x9e3779b97f4a7c15);
    x = (x ^ (x >> 30)) * UINT64_C(0xbf58476d1ce4e5b9);
    x = (x ^ (x >> 27)) * UINT64_C(0x94d049bb133111eb);
    return x ^ (x >> 31);
}
uint64_t nextKey(uint64_t& cursor) {
    for (;;) {
        auto k = permute64(cursor++);
        // Uniform common corpus valid for both Google sentinel policies.
        if (k < (std::numeric_limits<uint64_t>::max)() - 1) return k;
    }
}
size_t entries() {
    const char* s = std::getenv("MAP_BENCH_N");
    size_t n = s ? std::stoull(s) : 1000000;
    if (!n) throw std::invalid_argument("MAP_BENCH_N must be positive");
    return n;
}
uint64_t seed() {
    const char* s = std::getenv("MAP_BENCH_SEED");
    return s ? std::stoull(s) : 42;
}
template<class M> auto& nativeMap(M& m) {
#ifdef MAP_BENCH_GOOGLE_ADAPTER
    // Input domain was validated before timing; use the native API here.
    return static_cast<typename M::native_type&>(m);
#else
    return m;
#endif
}
void run(Bench& bench, bool reserved) {
    const size_t n = entries();
    constexpr uint64_t mask = UINT64_C(0x123456789abcdef0);
    std::vector<uint64_t> keys(n);
    uint64_t cursor = 0, expected_sum = 0;
    for (auto& k : keys) { k = nextKey(cursor); expected_sum += k ^ mask; }
    const auto miss_cursor = cursor;
    std::mt19937_64 rng(seed());
    bench.setMemoryBaseline();
    std::string name = std::string(reserved ? "reserve+insert" : "insert_grow") + " n=" + std::to_string(n);
    bench.beginMeasure(name.c_str());
    using M = Map<uint64_t,uint64_t>;
    M map;
    if (reserved) map.reserve(n);
    auto& native = nativeMap(map);
    for (auto k : keys) native.insert(typename M::value_type(k,k ^ mask));
    bench.endMeasure(n,map.size());
    if (!reserved) return;
    std::shuffle(keys.begin(),keys.end(),rng);
    uint64_t found = 0, sum = 0;
    bench.beginMeasure("find_hit_random");
    for (auto k : keys) {
        auto it = native.find(k);
        if (it != native.end()) { ++found; sum += it->second; }
    }
    bench.endMeasure(expected_sum,sum);
    if (found != n) throw std::runtime_error("hit count mismatch");
    cursor = miss_cursor;
    for (auto& k : keys) k = nextKey(cursor);
    found = 0;
    bench.beginMeasure("find_miss");
    for (auto k : keys) found += native.find(k) != native.end();
    bench.endMeasure(0,found);
}
}
BENCHMARK(FlatMap64Reserved) { run(bench,true); }
BENCHMARK(FlatMap64Grow) { run(bench,false); }
