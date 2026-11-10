#include "bench.h"

#include <fstream>
#include <regex>

void help(std::vector<std::string> const& args) {
    std::cout << "TODO this should print a help" << std::endl;
}

int main(int cargi, char** cargv) {
    if (cargi == 2 && std::string(cargv[1]) == "--list") {
        BenchRegistry::list();
        return 0;
    }
    auto ret = BenchRegistry::run(cargi == 2 ? cargv[1] : "");
    if (ret == -1) {
        BenchRegistry::list();
    }
    exit(ret);
}
