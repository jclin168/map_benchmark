
### std_hash, total seconds

| benchmark | sflat_flat_hash_map | bflat_unordered_flat_map | ankerl_unordered_dense | boost_unordered_flat_map | abseil_flat_hash_map | std_unordered_map |
|---|---|---|---|---|---|---|
| AccidentallyQuadratic | 1.5 | **1.3** | 3.1 | 25.4 | 41.1 | 9.2 |
| Copy | **1.3** | 3.0 | 2.8 | 5.6 | 13.0 | 32.4 |
| GameOfLife_growing | 4.2 | 4.6 | 4.3 | **3.6** | timeout | 17.3 |
| GameOfLife_stabilizing | 11.6 | 12.4 | 10.9 | **10.1** | timeout | 37.2 |
| InsertHugeInt | **30.6** | 35.2 | 56.7 | 54.9 | 52.1 | 146.7 |
| IterateIntegers | 11.9 | 8.7 | **1.9** | 9.5 | 18.5 | 24.9 |
| RandomDistinct2 | **12.2** | 13.7 | 37.6 | 28.9 | 264.1 | 81.0 |
| RandomFindString | 44.1 | 35.9 | **34.2** | 35.9 | 41.3 | 88.2 |
| RandomFindString_1000000 | **56.6** | 64.2 | 65.4 | 69.0 | 74.8 | 223.4 |
| RandomFind_200 | **58.8** | 61.6 | 78.5 | 61.1 | 198.1 | 199.6 |
| RandomFind_2000 | 65.4 | 66.0 | 82.5 | **64.5** | timeout | 211.6 |
| RandomFind_500000 | 92.9 | **91.6** | 109.8 | 92.7 | timeout | timeout |
| RandomInsertErase | 15.9 | **15.9** | 25.2 | 18.6 | timeout | 73.0 |
| RandomInsertEraseStrings | **18.4** | 19.3 | 29.4 | 20.0 | 21.6 | 58.3 |
| knucleotide | 7.3 | 7.3 | **5.5** | 8.7 | 24.3 | 26.6 |

### std_hash, peak MB

| benchmark | sflat_flat_hash_map | bflat_unordered_flat_map | ankerl_unordered_dense | boost_unordered_flat_map | abseil_flat_hash_map | std_unordered_map |
|---|---|---|---|---|---|---|
| AccidentallyQuadratic | 308.8 | **282.7** | 380.9 | 295.9 | 326.9 | 795.2 |
| Copy | **75.2** | 130.6 | 98.9 | 96.7 | 136.9 | 125.3 |
| GameOfLife_growing | 2.3 | 2.1 | **2.0** | 2.3 | timeout | 3.0 |
| GameOfLife_stabilizing | **1.0** | 1.1 | 1.1 | 1.1 | timeout | 1.2 |
| InsertHugeInt | **1266.5** | 1490.4 | 1728.5 | 1632.5 | 1728.9 | 3791.2 |
| IterateIntegers | 2.1 | **1.9** | 1.9 | 2.0 | 2.3 | 2.7 |
| RandomDistinct2 | **634.9** | 662.8 | 864.7 | 816.8 | 864.8 | 1898.8 |
| RandomFindString | 21.5 | 21.4 | **15.8** | 20.7 | 18.3 | 18.6 |
| RandomFindString_1000000 | 87.2 | 83.0 | 78.9 | 116.3 | 123.9 | **72.7** |
| RandomFind_200 | 0.6 | 0.6 | 0.6 | 0.6 | 0.7 | **0.5** |
| RandomFind_2000 | 0.8 | 0.7 | 0.7 | 0.7 | timeout | **0.7** |
| RandomFind_500000 | 20.7 | 22.3 | **17.8** | 32.5 | timeout | timeout |
| RandomInsertErase | 288.8 | 269.5 | **235.1** | 384.8 | timeout | 348.2 |
| RandomInsertEraseStrings | 73.3 | 77.5 | 96.6 | 153.2 | 98.4 | **71.7** |
| knucleotide | 127.9 | 127.7 | 127.4 | 127.6 | 128.3 | **125.4** |

### ankerl_hash, total seconds

| benchmark | sflat_flat_hash_map | bflat_unordered_flat_map | ankerl_unordered_dense | boost_unordered_flat_map | abseil_flat_hash_map | std_unordered_map |
|---|---|---|---|---|---|---|
| AccidentallyQuadratic | **1.6** | 31.7 | 3.1 | 25.3 | 13.7 | 9.7 |
| Copy | **1.4** | 2.9 | 2.8 | 5.6 | 13.4 | 32.4 |
| GameOfLife_growing | 5.5 | 4.5 | 4.3 | **3.6** | 5.6 | 19.6 |
| GameOfLife_stabilizing | 14.4 | 12.5 | 10.8 | **10.0** | 15.8 | 51.2 |
| InsertHugeInt | **31.0** | 35.2 | 57.5 | 55.3 | 53.0 | 152.1 |
| IterateIntegers | 11.9 | 8.7 | **1.9** | 9.6 | 18.3 | 25.0 |
| RandomDistinct2 | **13.3** | 13.6 | 38.1 | 28.7 | 29.5 | 99.9 |
| RandomFindString | 40.4 | 31.2 | **29.3** | 30.7 | 37.6 | 107.8 |
| RandomFindString_1000000 | 77.6 | **73.6** | 84.9 | 80.3 | 89.6 | 246.6 |
| RandomFind_200 | 80.2 | 62.8 | 78.6 | **61.5** | 68.4 | 216.1 |
| RandomFind_2000 | 84.9 | 66.1 | 83.5 | **63.1** | 75.6 | 234.9 |
| RandomFind_500000 | 107.2 | **91.0** | 110.4 | 91.7 | 114.8 | timeout |
| RandomInsertErase | 17.5 | **15.5** | 25.6 | 18.2 | 23.3 | 75.8 |
| RandomInsertEraseStrings | 19.2 | **18.2** | 28.4 | 20.5 | 22.3 | 64.1 |
| knucleotide | 8.7 | 7.2 | **5.7** | 8.7 | 9.8 | 33.5 |

### ankerl_hash, peak MB

| benchmark | sflat_flat_hash_map | bflat_unordered_flat_map | ankerl_unordered_dense | boost_unordered_flat_map | abseil_flat_hash_map | std_unordered_map |
|---|---|---|---|---|---|---|
| AccidentallyQuadratic | 308.7 | **272.6** | 380.9 | 295.9 | 326.9 | 795.1 |
| Copy | **75.2** | 130.6 | 98.9 | 96.7 | 136.9 | 125.3 |
| GameOfLife_growing | 2.3 | 2.1 | **1.9** | 2.3 | 2.7 | 3.0 |
| GameOfLife_stabilizing | 1.0 | 1.1 | 1.1 | **0.9** | 1.2 | 1.2 |
| InsertHugeInt | **1266.5** | 1490.3 | 1728.5 | 1632.5 | 1728.9 | 3791.3 |
| IterateIntegers | 2.1 | **1.9** | 2.0 | 2.0 | 2.2 | 2.7 |
| RandomDistinct2 | **634.8** | 662.7 | 864.7 | 816.8 | 864.9 | 1898.8 |
| RandomFindString | 21.5 | 21.6 | **15.8** | 18.3 | 19.2 | 18.7 |
| RandomFindString_1000000 | 87.3 | 83.0 | 78.8 | 116.3 | 123.8 | **72.7** |
| RandomFind_200 | 0.6 | 0.6 | **0.5** | 0.5 | 0.7 | 0.6 |
| RandomFind_2000 | 0.8 | **0.7** | 0.7 | 0.7 | 0.8 | 0.7 |
| RandomFind_500000 | 20.8 | 22.4 | **17.7** | 32.5 | 34.8 | timeout |
| RandomInsertErase | 288.8 | 269.5 | **235.1** | 384.8 | 408.8 | 348.3 |
| RandomInsertEraseStrings | 73.2 | 77.5 | 96.6 | 153.2 | 98.3 | **70.7** |
| knucleotide | 127.9 | 127.7 | 127.5 | 127.8 | 128.3 | **125.4** |
