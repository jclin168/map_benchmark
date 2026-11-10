# map_benchmark 全容器綜合評比（std::hash）

已完成 **780/780** 組容器／測項；39 種容器／配置、17 個計時測項、3 個診斷測項。主矩陣每組一次，原始參數，沒有縮減循環。本報告為完整主矩陣結果。

恢復環境交界另重測 sflat RandomDistinct2 一次（原始 5.787578 秒、恢復後 6.495098 秒）；以恢復後樣本作主結果，與其餘 38 個容器保持同一執行時段。選樣依環境時段，與快慢無關；兩份原始結果均保留於 epoch-recheck/。合計 780 組、781 份已保存程序結果，不含環境中斷未留下 checkpoint 的嘗試。

## 範圍與方法

- 全部原有「已註冊」測項；StringHashBench 在原始程式中被註解、Strings.cpp 內容被 #if 0 排除，不是可執行測項。新增 FlatMap64Reserved/Grow 不混入本輪原始 suite。
- 共用 std::hash adapter，保留容器內部 hash mixing、load factor、allocator 與種子政策；sflat 的 process seed 固定為 1。樹型容器不使用 hash，另標示類別。平行容器在此以單執行緒 API 測試，不代表多執行緒效能。
- GCC 14.2、C++17、Release -O3 -DNDEBUG -march=native；每個 executable 以 unity build 編譯，註冊名稱使用 __COUNTER__ 避免跨原始檔行號碰撞。F14 使用所需的三個 Folly source files，不建置其餘 Folly 元件。
- 每個程序單獨執行、固定 CPU affinity；每個測項先依固定順序測 sflat、std、Boost flat、Ankerl、Abseil flat、Google dense、Google sparse，其餘容器以固定亂數順序執行；沒有把執行順序平衡化。不同測項有插入、查詢、析構等不同計時邊界，數字代表原始 workload，不是純 find ns/op。
- 逐階段使用原程式的 expected-result 檢查；不相符會回傳失敗。診斷的 stable-reference=0 是正常屬性結果，不是驗證失敗。
- 每程序 180 秒上限；RSS 7 GiB、整體 cgroup 7.5 GiB 取樣保護線；環境硬上限 8 GiB、無 swap，RLIMIT_AS 保持原本 unlimited。逾時、記憶體停止、crash、sentinel domain 不相容與驗證失敗各自保留，失敗程序的部分階段不納入計時排名。
- RSS 是整個原始 workload 的程序峰值，含輸入、暫存與配置器，不能稱為單一 map 常駐記憶體。endMeasure 有些在 map 析構後，該點 RSS 也不能當作 live-map 用量。極小測項的 peak 可能受程序啟動／exec accounting 底線主導；不要比較其微小記憶體差距。CSV/HTML 另列虛擬位址空間 VmPeak（及 CSV 的最大取樣 VmSize）；虛擬位址預留不等同於實體 RSS，失敗程序僅有已觀測用量，僅供診斷，不與正確完成者做記憶體效率排名。
- 單次測量、共享 VM，沒有信賴區間；小幅差距不可據此視為穩定優勢。

## 全容器總覽

速度倍率為 std::unordered_map / 該容器的幾何平均：15 個非建構計時 workload 各占相同權重，每個 workload 先加總其所有階段秒數。**只有容器與 std baseline 均完成同一組 15 個 workload 才列倍率**；建構另列，失敗缺項不以較少測項補算總分。空表建構迴圈可能被編譯器消除，該微測項不合成吞吐量倍率。相對 std 的速度倍率大於 1 表示較快。完整核心名次另以同一組 15 項的幾何平均耗時排序，相對最快完整者的耗時倍率越小越好；因此即使 std baseline 未完整通過，其他完整容器之間仍可比較。

| Container | 類別 | 計時通過 | 核心覆蓋 | 完整核心名次 | 相對最快完整者耗時 | 相對 std 速度 | 已觀測最高 RSS GiB | 狀態 |
|---|---|---:|---:|---:|---:|---:|---:|---|
| ankerl::unordered_dense::map | flat / dense hash | 17/17 | 15/15 | 1 | 1.00x | — | 1.689 | ok:20 |
| sflat::flat_hash_map | flat / dense hash | 17/17 | 15/15 | 2 | 1.22x | — | 1.215 | ok:20 |
| ankerl::unordered_dense::segmented_map | segmented dense | 17/17 | 15/15 | 3 | 1.27x | — | 1.435 | ok:20 |
| boost::unordered_flat_map 1_93 | flat / dense hash | 17/17 | 15/15 | 4 | 1.38x | — | 1.596 | ok:20 |
| folly::F14ValueMap | flat / dense hash | 17/17 | 15/15 | 5 | 1.62x | — | 1.510 | ok:20 |
| boost::unordered_flat_map no SSE 1_93 | flat / dense hash | 17/17 | 15/15 | 6 | 1.70x | — | 1.596 | ok:20 |
| gtl::parallel_flat_hash_map | flat / dense hash | 17/17 | 15/15 | 7 | 1.79x | — | 1.162 | ok:20 |
| robin_hood::unordered_flat_map | flat / dense hash | 17/17 | 15/15 | 8 | 1.80x | — | 1.689 | ok:20 |
| ska::flat_hash_map | flat / dense hash | 17/17 | 15/15 | 9 | 1.83x | — | 4.502 | ok:20 |
| robin_hood::unordered_node_map | node / allocator variant | 17/17 | 15/15 | 10 | 1.96x | — | 2.252 | ok:20 |
| ska::bytell_hash_map | flat / dense hash | 17/17 | 15/15 | 11 | 2.07x | — | 1.689 | ok:20 |
| boost::unordered_node_map 1_93 | node / allocator variant | 17/17 | 15/15 | 12 | 2.08x | — | 4.010 | ok:20 |
| folly::F14NodeMap | node / allocator variant | 17/17 | 15/15 | 13 | 2.30x | — | 4.379 | ok:20 |
| gtl::node_hash_map | node / allocator variant | 17/17 | 15/15 | 14 | 2.61x | — | 4.587 | ok:20 |
| gtl::parallel_node_hash_map | node / allocator variant | 17/17 | 15/15 | 15 | 2.82x | — | 4.143 | ok:20 |
| std::unordered_map PoolAllocator | node / allocator variant | 17/17 | 15/15 | 16 | 3.23x | — | 2.231 | ok:20 |
| boost::multi_index::hashed_unique | hashed multi-index | 17/17 | 15/15 | 17 | 4.64x | — | 3.698 | ok:20 |
| absl::flat_hash_map | flat / dense hash | 11/17 | 9/15 | — | — | — | 1.689 | ok:14, timeout:6 |
| absl::node_hash_map | node / allocator variant | 11/17 | 9/15 | — | — | — | 4.590 | ok:14, timeout:6 |
| asteria::cow_hashmap | copy-on-write hash | 9/17 | 7/15 | — | — | — | ≥5.499 | ok:12, timeout:6, verification_failed:2 |
| boost::unordered_map 1_93 | node / allocator variant | 16/17 | 14/15 | — | — | — | 3.744 | ok:19, timeout:1 |
| boost::unordered_map PoolAllocator 1_93 | node / allocator variant | 16/17 | 14/15 | — | — | — | 2.273 | ok:19, timeout:1 |
| boost::unordered_map unsynchronized_pool_resource 1_93 | node / allocator variant | 16/17 | 14/15 | — | — | — | 2.364 | ok:19, timeout:1 |
| fph::DynamicFphMap | flat / dense hash | 14/17 | 13/15 | — | — | — | ≥1.861 | ok:17, timeout:3 |
| fph::MetaFphMap | flat / dense hash | 15/17 | 13/15 | — | — | — | ≥1.136 | ok:18, timeout:2 |
| google::dense_hash_map | flat / dense hash | 11/17 | 9/15 | — | — | — | 3.002 | ok:14, timeout:6 |
| google::sparse_hash_map | flat / dense hash | 10/17 | 8/15 | — | — | — | 0.870 | ok:13, timeout:7 |
| gtl::btree_map | ordered tree | 11/17 | 9/15 | — | — | — | ≥1.024 | ok:14, timeout:6 |
| gtl::flat_hash_map | flat / dense hash | 16/17 | 14/15 | — | — | — | 1.689 | ok:19, timeout:1 |
| spp::sparse_hash_map | flat / dense hash | 12/17 | 10/15 | — | — | — | 1.215 | ok:15, timeout:5 |
| jg::dense_hash_map | flat / dense hash | 13/17 | 11/15 | — | — | — | 3.002 | ok:16, timeout:4 |
| emhash7::HashMap | flat / dense hash | 13/17 | 11/15 | — | — | — | 2.275 | ok:16, timeout:4 |
| emhash8::HashMap | flat / dense hash | 13/17 | 11/15 | — | — | — | 1.738 | ok:16, timeout:4 |
| rigtorp::HashMap | flat / dense hash | 11/17 | 9/15 | — | — | — | 3.002 | ok:14, timeout:6 |
| std::unordered_map | node / allocator variant | 16/17 | 14/15 | — | — | — | 3.704 | ok:19, timeout:1 |
| std::unordered_map unsynchronized_pool_resource | node / allocator variant | 16/17 | 14/15 | — | — | — | ≥2.243 | ok:19, timeout:1 |
| tsl::hopscotch_map | flat / dense hash | 11/17 | 9/15 | — | — | — | 3.002 | ok:14, timeout:6 |
| tsl::robin_map | flat / dense hash | 11/17 | 9/15 | — | — | — | ≥7.000 | ok:14, rss_watchdog:1, timeout:5 |
| tsl::sparse_map | flat / dense hash | 13/17 | 11/15 | — | — | — | 1.104 | ok:16, timeout:4 |

## 診斷結果

| 診斷 | 通過程序 | 說明 |
|---|---:|---|
| ShowHash | 39/39 | 1 種不同輸出；用來確認共同 hash adapter |
| ShowHashString | 39/39 | 1 種不同輸出；用來確認共同 hash adapter |
| ShowIsStableReference | 39/39 | 15 種觀測穩定、24 種觀測不穩定 |

穩定引用診斷只觀察原測項的 10,000 次插入，不等同於所有操作的 API 保證；0 並非失敗。各容器觀測值在 overview.csv 的 stable_reference_diagnostic 欄位。

## 分類結果

各分類以完整通過同一組分類測項者的幾何平均耗時排序；所有容器均已嘗試該分類後才列名次。std baseline 未完整通過分類時，相對 std 欄留空。

| 分類 | 測項數 | 可完整比較容器數 | 最快容器 | 相對 std 速度 | sflat 名次 |
|---|---:|---:|---|---:|---:|
| construct | 2 | — | 建構微測項逐項列出，不合成倍率 | — | — |
| copy_reinsert | 2 | 38 | ankerl::unordered_dense::map | 10.18x | 7/38 |
| iteration | 1 | 39 | emhash8::HashMap | 27.56x | 9/39 |
| integer_updates | 3 | 18 | sflat::flat_hash_map | 8.53x | 1/18 |
| integer_find | 3 | 24 | boost::unordered_node_map 1_93 | — | 11/24 |
| string | 3 | 37 | ankerl::unordered_dense::map | 2.64x | 4/37 |
| applications | 3 | 31 | ankerl::unordered_dense::map | 3.09x | 4/31 |

## sflat 逐 workload 的效能差距

每個 workload 只比較完整通過者；全部 39 種配置均已嘗試才列出名次。耗時倍率為 sflat / 該項最快者，大於 1 表示 sflat 花更多時間。這些差距可作為後續 profiling 的優先順序，不代表已確定根因。

| Workload | 通過數 | sflat 名次 | sflat 秒數 | 最快容器 | sflat 耗時／最快耗時 |
|---|---:|---:|---:|---|---:|
| Copy | 39/39 | 14/39 | 6.4598 | tsl::sparse_map | 6.28x |
| GameOfLife_growing | 32/39 | 4/32 | 3.0875 | ankerl::unordered_dense::map | 1.15x |
| GameOfLife_stabilizing | 31/39 | 4/31 | 8.5018 | ankerl::unordered_dense::map | 1.44x |
| AccidentallyQuadratic | 38/39 | 1/38 | 0.8591 | sflat::flat_hash_map | 1.00x |
| IterateIntegers | 39/39 | 9/39 | 5.7492 | emhash8::HashMap | 8.60x |
| RandomDistinct2 | 34/39 | 1/34 | 6.4951 | sflat::flat_hash_map | 1.00x |
| InsertHugeInt | 34/39 | 3/34 | 15.7713 | rigtorp::HashMap | 1.02x |
| RandomInsertErase | 22/39 | 2/22 | 13.1131 | boost::unordered_flat_map 1_93 | 1.19x |
| RandomInsertEraseStrings | 37/39 | 1/37 | 24.6775 | sflat::flat_hash_map | 1.00x |
| knucleotide | 39/39 | 9/39 | 4.4552 | gtl::flat_hash_map | 1.37x |
| RandomFindString | 38/39 | 17/38 | 30.8114 | boost::unordered_node_map 1_93 | 1.42x |
| RandomFindString_1000000 | 37/39 | 3/37 | 37.8273 | ankerl::unordered_dense::map | 1.12x |
| RandomFind_200 | 28/39 | 21/28 | 46.2458 | fph::MetaFphMap | 1.77x |
| RandomFind_2000 | 25/39 | 17/25 | 37.9264 | ska::flat_hash_map | 1.48x |
| RandomFind_500000 | 24/39 | 3/24 | 52.4890 | boost::unordered_node_map 1_93 | 1.04x |

## 主要容器逐 workload 秒數

只列整個 case 完成且驗證成功的秒數；其他狀態不以部分階段秒數替代。完整 39 種與逐階段數據見 CSV/HTML。

| Workload | sflat_flat_hash_map | boost_unordered_flat_map | ankerl_unordered_dense | abseil_flat_hash_map | ktprime_hash_table8 | std_unordered_map |
|---|---:|---:|---:|---:|---:|---:|
| CtorDtorEmptyMap | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0022 | 0.0000 |
| CtorDtorSingleEntryMap | 0.4614 | 0.1793 | 0.1773 | 0.0000 | 0.0851 | 0.1998 |
| Copy | 6.4598 | 3.3132 | 1.5451 | 9.2028 | 1.1013 | 15.5716 |
| GameOfLife_growing | 3.0875 | 2.8444 | 2.6797 | timeout | 49.8443 | 10.2252 |
| GameOfLife_stabilizing | 8.5018 | 7.5898 | 5.9141 | timeout | 69.2910 | 18.3568 |
| AccidentallyQuadratic | 0.8591 | 15.2172 | 1.1761 | 28.9009 | 1.9810 | 12.1042 |
| IterateIntegers | 5.7492 | 6.0711 | 0.6710 | 15.1371 | 0.6682 | 18.4195 |
| RandomDistinct2 | 6.4951 | 10.2870 | 14.0084 | timeout | 15.1970 | 131.4227 |
| InsertHugeInt | 15.7713 | 15.6074 | 26.4980 | 38.3811 | 27.3963 | 137.3160 |
| RandomInsertErase | 13.1131 | 11.0273 | 14.3737 | timeout | timeout | 46.1516 |
| RandomInsertEraseStrings | 24.6775 | 28.1853 | 27.8784 | 28.9254 | 35.4769 | 60.9822 |
| knucleotide | 4.4552 | 4.1899 | 3.4345 | 20.9308 | 4.9209 | 8.5848 |
| RandomFindString | 30.8114 | 25.1017 | 24.3299 | 27.3209 | 25.8035 | 55.2534 |
| RandomFindString_1000000 | 37.8273 | 38.3049 | 33.7284 | 39.5975 | 42.3416 | 125.0060 |
| RandomFind_200 | 46.2458 | 28.8344 | 43.2009 | 111.2294 | timeout | 57.4233 |
| RandomFind_2000 | 37.9264 | 28.6647 | 32.8283 | timeout | timeout | 58.5418 |
| RandomFind_500000 | 52.4890 | 72.7596 | 57.3560 | timeout | timeout | timeout |

## 記憶體保護觸發紀錄

以下為未完成 workload 中止前的已觀測程序用量，不能解讀為完成指定 entry 數後的 map 大小；不納入速度或記憶體效率排名。VmPeak 是虛擬位址空間，不是 RSS。

| 容器 | Workload | 停止原因 | 程序秒數（未完成） | 已觀測 RSS GiB | 已觀測 VmPeak GiB | 已完成階段 |
|---|---|---|---:|---:|---:|---:|
| tsl::robin_map | RandomFind_500000 | rss_watchdog | 47.83 | 7.0001 | 9.0061 | 1 |

## 整數查找逾時所在階段

原程式每種命中率依序測低 32 位、高 32 位。依已完成的原始階段數，推定逾時時下一個未完成階段；這不是該階段完成所需秒數。結果限定本輪 std::hash 與原始 masked 輸入，不同 hash 設定需另行測量。

| Workload | 逾時程序 | 下一階段為高 32 位 | 下一階段為低 32 位 |
|---|---:|---:|---:|
| RandomFind_200 | 11 | 11 | 0 |
| RandomFind_2000 | 14 | 14 | 0 |
| RandomFind_500000 | 14 | 12 | 2 |

## 後續 profiling 目標

[200 次插入整數查找的命中率階段比較](diagnostics/sflat_find200_phases.md)：依已通過的 sflat 與 Boost flat checkpoint 比較，25% 命中率的差距較大；高命中率接近。這是單次測量的觀察，尚未判定根因。

## 已確認的 pinned dependency 問題

asteria-cow_hashmap 在 GameOfLife_stabilizing 的 R-pentomino 輸出 167249，原預期 116。InsertHugeInt 的 clear 100M int 階段也留下 59,122,781 個元素（預期 0）。另以原生 rocket::cow_hashmap API（不經 benchmark adapter）重現：reserve(64)、插入 key=1 後 clear()，size 仍為 1，find(1) 仍命中。當前 revision 的 clear() 對 bucket range 使用 size()，而非整個 bucket range，會殘留元素。

這會影響多次清空的應用測項，不能將異常工作狀態的耗時當作正確 workload 的速度，其記憶體數字也僅描述錯誤執行狀態。原始 timeout／verification_failed 狀態仍完整保留。結論只針對 manifest 記錄的 revision，不代表目前上游版本。

- [最小原生 API 重現程式](diagnostics/asteria_clear.cpp)、[輸出](diagnostics/asteria_clear.txt)、[版本與重現資訊](diagnostics/asteria_clear.json)。

## 詳細檔案

- [互動表格](comparison.html)：選測項與容器類型，可排序所有容器的時間及峰值記憶體。
- [全容器總覽 CSV](overview.csv)、[全部 case 結果 CSV](case_results.csv)、[environment.json](environment.json)、[compile-flags.json](compile-flags.json)、[builds.json](builds.json)。
- runs/：每個程序的 JSON checkpoint；stdout/、stderr/：原始輸出；build-logs/：每個 adapter 的編譯紀錄。
- [續跑環境紀錄](resumptions.json)：環境中斷後保留391個 checkpoint；在相同CPU型號／拓樸與資源上限的恢復環境接續，屬跨執行環境時段的單次 sweep，不是獨立重複樣本。
- 原始階段 CSV raw.csv 在全部程序完成時由 runner 輸出；未完成與失敗 case 的記錄保留供診斷，排名只採整個 case 通過者。
- docs/COMPREHENSIVE.md 說明建置、續跑與重現方式。
