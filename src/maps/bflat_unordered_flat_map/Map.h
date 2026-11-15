#pragma once
#include "Hash.h"
#include <bflat/unordered_flat_map.hpp>
static const char* MapName = "bflat::unordered_flat_map";
template<class Key, class Val, class H = Hash<Key>>
using Map = bflat::unordered_flat_map<Key, Val, H>;
