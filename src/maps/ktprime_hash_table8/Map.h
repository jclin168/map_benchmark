#pragma once

#include "Hash.h"
#if __has_include("ktprime__emhash/include/emhash/hash_table8.hpp")
#include "ktprime__emhash/include/emhash/hash_table8.hpp"
#else
#include "ktprime__emhash/hash_table8.hpp"
#endif

static const char* MapName = "emhash8::HashMap";

template <class Key, class Val, class H = Hash<Key>>
using Map = emhash8::HashMap<Key, Val, H>;
