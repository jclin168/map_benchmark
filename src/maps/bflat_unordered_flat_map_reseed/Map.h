#pragma once
#define BFLAT_RESEED_AVALANCHING 1
#include "Hash.h"
#include <bflat/unordered_flat_map.hpp>
static const char* MapName = "bflat::unordered_flat_map (reseed avalanching)";
template<class Key, class Val, class H = Hash<Key>>
using Map = bflat::unordered_flat_map<Key, Val, H>;
