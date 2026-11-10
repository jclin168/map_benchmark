cmake_minimum_required(VERSION 3.16)
project (map_benchmark)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
# set(CMAKE_CXX_EXTENSIONS OFF)


SET(CMAKE_CXX_FLAGS_RELEASE "-DNDEBUG -O3 -march=native")
list(APPEND FOLLY_CXX_FLAGS "-DNDEBUG -march=native")

#SET(CMAKE_CXX_FLAGS_RELEASE "-O3")
#list(APPEND FOLLY_CXX_FLAGS "-O3")

option(MAP_BENCH_USE_GOLD "Link with the optional GNU gold linker" OFF)
if(MAP_BENCH_USE_GOLD)
  add_link_options(-fuse-ld=gold)
endif()
#SET(CMAKE_STATIC_LINKER_FLAGS "-fuse-ld=gold ${CMAKE_STATIC_LINKER_FLAGS}")



file(GLOB SRC_BENCHMARKS "src/benchmarks/*.cpp")
file(GLOB SRC_APP "src/app/*.cpp")

file(GLOB INC_HASHES "src/hashes/*")
file(GLOB INC_MAPS "src/maps/*")

# external code #####################################################################

# boost: use locally built boost version
set(BOOST_ROOT "/home/martinus/dev/boost_1_82_0_install" CACHE PATH "Boost library path" )
#list(APPEND CMAKE_PREFIX_PATH /home/martinus/Downloads/boost_1_81_0)
set(MAP_BENCH_BOOST_SOURCE_DIR "" CACHE PATH "Optional modular Boost source tree (headers)")
set(BOOST_INCLUDE_DIR "" CACHE PATH "Optional Boost headers, compatible with the regex profile")
set(MAP_BENCH_MAPS "" CACHE STRING "Semicolon-separated adapter directory names; empty selects all")
set(MAP_BENCH_HASHES "" CACHE STRING "Semicolon-separated hash directory names; empty selects all")
set(MAP_BENCH_ANKERL_DIR "${CMAKE_SOURCE_DIR}/external/martinus__unordered_dense" CACHE PATH "Ankerl source tree")
set(MAP_BENCH_ABSEIL_DIR "${CMAKE_SOURCE_DIR}/external/abseil__abseil-cpp" CACHE PATH "Abseil source tree")
function(select_adapters result folder selection header)
  if(${selection})
    set(selected)
    foreach(name IN LISTS ${selection})
      set(dir "${CMAKE_SOURCE_DIR}/src/${folder}/${name}")
      if(NOT EXISTS "${dir}/${header}")
        message(FATAL_ERROR "Unknown ${folder} adapter: ${name}")
      endif()
      list(APPEND selected "${dir}")
    endforeach()
    set(${result} "${selected}" PARENT_SCOPE)
  endif()
endfunction()
select_adapters(INC_MAPS maps MAP_BENCH_MAPS Map.h)
select_adapters(INC_HASHES hashes MAP_BENCH_HASHES Hash.h)
# Regex selectors from the fork remain supported; explicit lists take precedence.
set(MAPS ".*" CACHE STRING "Regex of map directory names")
set(HASHES ".*" CACHE STRING "Regex of hash directory names")
if(NOT MAP_BENCH_MAPS)
  list(FILTER INC_MAPS INCLUDE REGEX "maps[\\/](${MAPS})$")
endif()
if(NOT MAP_BENCH_HASHES)
  list(FILTER INC_HASHES INCLUDE REGEX "hashes[\\/](${HASHES})$")
endif()
if(MAP_BENCH_BOOST_SOURCE_DIR)
  file(GLOB Boost_INCLUDE_DIRS "${MAP_BENCH_BOOST_SOURCE_DIR}/libs/*/include")
elseif(INC_MAPS MATCHES "_pool")
  find_package(Boost 1.81 COMPONENTS container REQUIRED)
elseif(BOOST_INCLUDE_DIR)
  set(Boost_INCLUDE_DIRS "${BOOST_INCLUDE_DIR}")
elseif(INC_MAPS MATCHES "boost_|folly_")
  find_package(Boost 1.81 REQUIRED)
endif()

set(MAP_BENCH_SFLAT_SEED "" CACHE STRING "Optional reproducible SFLAT_PROCESS_SEED")
if(NOT MAP_BENCH_SFLAT_SEED STREQUAL "")
  add_compile_definitions(SFLAT_PROCESS_SEED=${MAP_BENCH_SFLAT_SEED})
endif()
include(CTest)


# absl stuff: see https://github.com/abseil/abseil-cpp/tree/master/CMake
if(MSVC)
    # /wd4005  macro-redefinition
    # /wd4068  unknown pragma
    # /wd4244  conversion from 'type1' to 'type2'
    # /wd4267  conversion from 'size_t' to 'type2'
    # /wd4800  force value to bool 'true' or 'false' (performance warning)
    add_compile_options(/wd4005 /wd4068 /wd4244 /wd4267 /wd4800)
    add_definitions(/DNOMINMAX /DWIN32_LEAN_AND_MEAN=1 /D_CRT_SECURE_NO_WARNINGS)
endif()
set(ABSL_PROPAGATE_CXX_STD ON)
add_subdirectory("${MAP_BENCH_ABSEIL_DIR}" abseil EXCLUDE_FROM_ALL)

# pthread, required by absl see https://github.com/abseil/abseil-cpp/issues/183#issuecomment-458453010
set(CMAKE_THREAD_PREFER_PTHREAD TRUE)
set(THREADS_PREFER_PTHREAD_FLAG TRUE)
find_package(Threads REQUIRED)

# folly
# install dependencies, see https://github.com/facebook/folly
# sudo apt-get install \
#   g++ \
#   cmake \
#   libboost-all-dev \
#   libevent-dev \
#   libdouble-conversion-dev \
#   libgoogle-glog-dev \
#   libgflags-dev \
#   libiberty-dev \
#   liblz4-dev \
#   liblzma-dev \
#   libsnappy-dev \
#   make \
#   zlib1g-dev \
#   binutils-dev \
#   libjemalloc-dev \
#   libssl-dev \
#   pkg-config

# make sure we get SSE and crc support!
# see https://github.com/facebook/folly/blob/master/folly/container/detail/F14Table.cpp#L26

# folly is disabled by default
option(ENABLE_FOLLY "enable facebook folly build" FALSE)
option(MAP_BENCH_FOLLY_MINIMAL "Build only Folly sources required by F14" OFF)
option(MAP_BENCH_UNITY_BUILD "Build each benchmark executable as one translation unit" OFF)
if (ENABLE_FOLLY)
    if(MAP_BENCH_FOLLY_MINIMAL)
      set(FOLLY_SOURCE_DIR "${CMAKE_SOURCE_DIR}/external/facebook__folly")
      set(FOLLY_CONFIG_DIR "${CMAKE_BINARY_DIR}/folly-config")
      file(MAKE_DIRECTORY "${FOLLY_CONFIG_DIR}/folly")
      file(WRITE "${FOLLY_CONFIG_DIR}/folly/folly-config.h"
        "#pragma once\n#define FOLLY_HAVE_PTHREAD 1\n#define FOLLY_HAVE_LIBGFLAGS 0\n#define FOLLY_HAVE_LIBGLOG 0\n#define FOLLY_HAVE_WEAK_SYMBOLS 1\n#define FOLLY_HAVE_MALLOC_USABLE_SIZE 1\n#define FOLLY_HAVE_INT128_T 1\n#define FOLLY_HAVE_UNALIGNED_ACCESS 1\n#define FOLLY_HAVE_VLA 1\n#define FOLLY_SUPPLY_MISSING_INT128_TRAITS 0\n")
      add_library(folly STATIC
        "${FOLLY_SOURCE_DIR}/folly/container/detail/F14Table.cpp"
        "${FOLLY_SOURCE_DIR}/folly/lang/SafeAssert.cpp"
        "${FOLLY_SOURCE_DIR}/folly/lang/ToAscii.cpp")
      target_include_directories(folly PUBLIC "${FOLLY_CONFIG_DIR}" "${FOLLY_SOURCE_DIR}" ${Boost_INCLUDE_DIRS})
      target_link_libraries(folly PUBLIC Threads::Threads)
    else()
      add_subdirectory("external/facebook__folly")
    endif()
else ()
    list(FILTER INC_MAPS EXCLUDE REGEX "maps[\\/]folly_")
endif ()


# build stuff #####################################################################

# use ccache
find_program(CCACHE_PROGRAM ccache)
if(CCACHE_PROGRAM)
    set_property(GLOBAL PROPERTY RULE_LAUNCH_COMPILE "${CCACHE_PROGRAM}")
endif(CCACHE_PROGRAM)

# I like colors, even with ninja build
if ("${CMAKE_CXX_COMPILER_ID}" STREQUAL "GNU")
    add_compile_options (-fdiagnostics-color=always)
elseif ("${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang")
    add_compile_options (-fcolor-diagnostics)
endif ()

# The controlled profile and its adapter tests apply only to these interfaces.
set(MAP_BENCH_FLAT64_ADAPTERS sflat_flat_hash_map boost_unordered_flat_map
    ankerl_unordered_dense abseil_flat_hash_map google_dense_hash_map google_sparse_hash_map)

# create targets for all map - hash pairs

foreach(HASH_DIR ${INC_HASHES})
    get_filename_component(HASH_NAME ${HASH_DIR} NAME_WE)
    add_custom_target("${HASH_NAME}_all") # aggregate of map targets
endforeach(HASH_DIR ${INC_HASHES})

foreach(MAP_DIR ${INC_MAPS})
    get_filename_component(MAP_NAME ${MAP_DIR} NAME_WE)
    add_custom_target("${MAP_NAME}_all") # aggregate of hash targets
    foreach(HASH_DIR ${INC_HASHES})
        # executable name: mapname_hashname
        get_filename_component(HASH_NAME ${HASH_DIR} NAME_WE)
        set(EXECUTABLE_NAME "bench_${MAP_NAME}__${HASH_NAME}")

        # collect .cpp files in current hash and map directory
        file(GLOB SRC_MAP_DIR "${MAP_DIR}/*.cpp")
        file(GLOB SRC_HASH_DIR "${HASH_DIR}/*.cpp")

        set(MAP_BENCH_SOURCES ${SRC_BENCHMARKS})
        if(NOT MAP_NAME IN_LIST MAP_BENCH_FLAT64_ADAPTERS)
            list(REMOVE_ITEM MAP_BENCH_SOURCES "${CMAKE_SOURCE_DIR}/src/benchmarks/FlatMap64.cpp")
        endif()
        add_executable(${EXECUTABLE_NAME} ${SRC_APP} ${MAP_BENCH_SOURCES} ${SRC_MAP_DIR} ${SRC_HASH_DIR})
        if(MAP_BENCH_UNITY_BUILD)
          set_target_properties(${EXECUTABLE_NAME} PROPERTIES UNITY_BUILD ON UNITY_BUILD_BATCH_SIZE 0)
        endif()
        target_include_directories(${EXECUTABLE_NAME} PRIVATE "src/app" "external" ${MAP_DIR} ${HASH_DIR} ${FOLLY_DIR})
        if(BUILD_TESTING AND MAP_NAME IN_LIST MAP_BENCH_FLAT64_ADAPTERS)
          set(TEST_NAME "adapter_${MAP_NAME}__${HASH_NAME}")
          add_executable(${TEST_NAME} EXCLUDE_FROM_ALL tests/adapter_smoke.cpp)
          target_include_directories(${TEST_NAME} PRIVATE "src/app" "external" ${MAP_DIR} ${HASH_DIR})
          add_test(NAME ${TEST_NAME} COMMAND ${TEST_NAME})
        endif()

        if (EXISTS "${MAP_DIR}/dependencies.cmake")
            include("${MAP_DIR}/dependencies.cmake")
        endif ()

        if (EXISTS "${HASH_DIR}/dependencies.cmake")
            include("${HASH_DIR}/dependencies.cmake")
        endif ()

        if(BUILD_TESTING AND MAP_NAME IN_LIST MAP_BENCH_FLAT64_ADAPTERS)
          set(BENCH_TARGET "${EXECUTABLE_NAME}")
          set(EXECUTABLE_NAME "${TEST_NAME}")
          if(EXISTS "${MAP_DIR}/dependencies.cmake")
            include("${MAP_DIR}/dependencies.cmake")
          endif()
          if(EXISTS "${HASH_DIR}/dependencies.cmake")
            include("${HASH_DIR}/dependencies.cmake")
          endif()
          set(EXECUTABLE_NAME "${BENCH_TARGET}")
          add_dependencies(${EXECUTABLE_NAME} ${TEST_NAME})
        endif()
        add_dependencies("${HASH_NAME}_all" ${EXECUTABLE_NAME})
        add_dependencies("${MAP_NAME}_all" ${EXECUTABLE_NAME})
    endforeach(HASH_DIR ${INC_HASHES})
endforeach(MAP_DIR ${INC_MAPS})
