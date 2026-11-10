#pragma once
#include "Hash.h"
#include "google_hash_map_adapter.h"
#define MAP_BENCH_GOOGLE_ADAPTER 1
static const char* MapName = "google::sparse_hash_map";
template<class Key, class Val, class H = Hash<Key>>
using Map = GoogleMapAdapter<Key, Val, H, false>;
