#ifndef GENERALUTILS_H
#define GENERALUTILS_H

#include <thread>

namespace pbrt {
namespace iile {

static unsigned cpusCount() {
    unsigned count = std::thread::hardware_concurrency();
    if (count == 0) {
        return 2; // Could not detect, return default value
    }
    return count;
}

}
}

#endif // GENERALUTILS_H
