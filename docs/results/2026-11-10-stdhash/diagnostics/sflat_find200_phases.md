# Integer find after 200 insertions: phase times

The data comes from two saved checkpoints. Both cases passed the result checks. This comparison adds no measurements.

Each hit rate has one low-32-bit phase and one high-32-bit phase. The table adds both phase times.

Use this single VM sample to select profiling tests. Repeat measurements before you identify a cause.

| Hit rate | sflat time s | Boost flat time s | sflat time / Boost time |
|---|---:|---:|---:|
| 0% | 9.95010 | 5.52859 | 1.800x |
| 25% | 17.06565 | 5.62201 | 3.036x |
| 50% | 6.64626 | 5.64720 | 1.177x |
| 75% | 6.12453 | 5.88285 | 1.041x |
| 100% | 6.45926 | 6.15376 | 1.050x |

See the [phase CSV](sflat_find200_phases.csv). Times are close at high hit rates. The difference is larger at a 25% hit rate.
