#ifndef GENERALUTILS_H
#define GENERALUTILS_H

#include <thread>
#include <memory>
#include <string>
#include <dirent.h>
#include <stdio.h>
#include <chrono>

namespace pbrt {
namespace iile {

static unsigned cpusCountHalf() {
    unsigned count = std::thread::hardware_concurrency();
    return std::max(1u, count / 2);
}

static std::unique_ptr<std::vector<std::string>> listDir(std::string dirName) {
    DIR *d;
    struct dirent *dir;
    std::unique_ptr<std::vector<std::string>> res (
                new std::vector<std::string>()
                );
    d = opendir(dirName.c_str());
    if (d) {
        while ((dir = readdir(d)) != NULL) {
            res->push_back(std::string(dir->d_name));
        }
        closedir(d);
    }
    return res;
}

static void sleepMillis(long millis)
{
    std::this_thread::sleep_for(std::chrono::milliseconds(millis));
}

static bool startsWith(std::string a, std::string b)
{
    return a.find(b) == 0;
}

}
}

#endif // GENERALUTILS_H
