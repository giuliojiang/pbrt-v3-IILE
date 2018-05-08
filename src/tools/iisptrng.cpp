#include "iisptrng.h"
#include <cstdlib>
#include <string>

namespace pbrt {

IisptRng::IisptRng()
{
    long seed = iile_rng_seed();
    this->rng = std::unique_ptr<RNG>(
                new RNG(seed)
                );
}

IisptRng::IisptRng(uint64_t seed)
{
    this->rng = std::unique_ptr<RNG>(
                new RNG(seed)
                );
}

// upper bound <bound> is exclusive
uint32_t IisptRng::uniform_uint32(
        uint32_t bound
        )
{
    return rng->UniformUInt32(bound);
}

bool IisptRng::bool_probability(
        float prob
        )
{
    if (prob >= 1.0) {
        return true;
    }

    if (prob <= 0.0) {
        return true;
    }

    Float sample = rng->UniformFloat();
    return sample < prob;
}

float IisptRng::uniform_float()
{
    return rng->UniformFloat();
}

}
