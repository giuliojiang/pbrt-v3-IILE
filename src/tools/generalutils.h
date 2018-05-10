#ifndef GENERALUTILS_H
#define GENERALUTILS_H

#include <thread>

namespace pbrt {
namespace iile {

static unsigned cpusCountHalf() {
    unsigned count = std::thread::hardware_concurrency();
    return std::max(1u, count / 2);
}

}
}

#endif // GENERALUTILS_H
