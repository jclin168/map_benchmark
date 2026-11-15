// Effective clock probe: iterations per ns of a dependent add loop (about 1.3 at 2.5 GHz here).
// g++ -O2 tools/clk.cpp -o results/<dir>/clk ; taskset -c 2 results/<dir>/clk
#include <chrono>
#include <cstdio>
int main(){ for(int r=0;r<5;r++){ auto c0=std::chrono::steady_clock::now(); unsigned long z=1;
 for(int i=0;i<200000000;++i){ z+=i; asm volatile("":"+r"(z)); }
 printf("%.3f ",2e8/std::chrono::duration<double,std::nano>(std::chrono::steady_clock::now()-c0).count()); } puts(""); }
