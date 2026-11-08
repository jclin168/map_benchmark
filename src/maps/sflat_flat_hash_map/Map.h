#pragma once

#include "Hash.h"
#include "jclin168__sflat_hash_map/include/sflat/flat_hash_map.hpp"

static const char* MapName = "sflat::flat_hash_map";

template <class Key, class Val, class H = Hash<Key>>
using Map = sflat::flat_hash_map<Key, Val, H>;
