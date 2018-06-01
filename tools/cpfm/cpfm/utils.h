#ifndef UTILS_H
#define UTILS_H

#include <csignal>
#include <cstdlib>
#include <string>
#include <sstream>
#include <vector>
#include <iterator>

static void terminate()
{
    std::exit(1);
    std::raise(SIGKILL);
}

static bool hasEnding (std::string const &fullString, std::string const &ending) {
    if (fullString.length() >= ending.length()) {
        return (0 == fullString.compare (fullString.length() - ending.length(), ending.length(), ending));
    } else {
        return false;
    }
}

template<typename Out>
static void split(const std::string &s, char delim, Out result) {
    std::stringstream ss(s);
    std::string item;
    while (std::getline(ss, item, delim)) {
        *(result++) = item;
    }
}

static std::vector<std::string> split(const std::string &s, char delim) {
    std::vector<std::string> elems;
    split(s, delim, std::back_inserter(elems));
    return elems;
}

#endif // UTILS_H
