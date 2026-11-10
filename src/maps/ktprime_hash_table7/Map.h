#pragma once

#include "Hash.h"
#if __has_include("ktprime__emhash/include/emhash/hash_table7.hpp")
#include "ktprime__emhash/include/emhash/hash_table7.hpp"
#else
#include "ktprime__emhash/hash_table7.hpp"
#endif

static const char* MapName = "emhash7::HashMap";

template <class Key, class Val, class H = Hash<Key>>
using Map = emhash7::HashMap<Key, Val, H>;
