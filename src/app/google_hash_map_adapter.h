#pragma once
// Compatibility for sparsehash 2.0.4. The native sentinel restrictions remain
// explicit: dense reserves two keys, sparse reserves the deleted marker.
#include <sparsehash/dense_hash_map>
#include <sparsehash/sparse_hash_map>
#include <limits>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <utility>

template<class Key> struct GoogleBenchmarkMarkers {
    static Key empty() { return (std::numeric_limits<Key>::max)(); }
    static Key deleted() { return static_cast<Key>((std::numeric_limits<Key>::max)() - 1); }
};
template<> struct GoogleBenchmarkMarkers<std::string> {
    static std::string empty() { return "\xff-map-benchmark-empty-\xff"; }
    static std::string deleted() { return "\xff-map-benchmark-deleted-\xff"; }
};
template<class Key, class Val, class H, bool Dense>
class GoogleMapAdapter : public std::conditional_t<Dense,
    google::dense_hash_map<Key,Val,H>, google::sparse_hash_map<Key,Val,H>> {
    using Base = std::conditional_t<Dense,
        google::dense_hash_map<Key,Val,H>, google::sparse_hash_map<Key,Val,H>>;
    static void require_key(const Key& k) {
        if (is_reserved_key(k)) throw std::invalid_argument("Google sparsehash reserved sentinel key");
    }
public:
    using native_type = Base;
    using typename Base::iterator;
    using typename Base::const_iterator;
    using typename Base::value_type;
    using typename Base::size_type;
    GoogleMapAdapter() {
        if constexpr(Dense) this->set_empty_key(GoogleBenchmarkMarkers<Key>::empty());
        this->set_deleted_key(GoogleBenchmarkMarkers<Key>::deleted());
    }
    static bool is_reserved_key(const Key& k) {
        return k == GoogleBenchmarkMarkers<Key>::deleted() ||
            (Dense && k == GoogleBenchmarkMarkers<Key>::empty());
    }
    void reserve(size_t n) { Base::resize(n); }
    Val& operator[](const Key& k) { require_key(k); return Base::operator[](k); }
    Val& operator[](Key&& k) { require_key(k); return Base::operator[](k); }
    iterator find(const Key& k) { return is_reserved_key(k) ? Base::end() : Base::find(k); }
    const_iterator find(const Key& k) const { return is_reserved_key(k) ? Base::end() : Base::find(k); }
    size_type count(const Key& k) const { return is_reserved_key(k) ? 0 : Base::count(k); }
    using Base::erase;
    size_type erase(const Key& k) { return is_reserved_key(k) ? 0 : Base::erase(k); }
    template<class K, class V> std::pair<iterator,bool> emplace(K&& k, V&& v) {
        value_type value(std::forward<K>(k),std::forward<V>(v));
        require_key(value.first);
        return Base::insert(value);
    }
    // These overloads guard sentinels for the insert forms used by benchmarks.
    std::pair<iterator,bool> insert(const value_type& v) { require_key(v.first); return Base::insert(v); }
    std::pair<iterator,bool> insert(value_type&& v) { require_key(v.first); return Base::insert(v); }
};
