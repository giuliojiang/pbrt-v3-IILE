#ifndef IISPTMATHUTILS_H
#define IISPTMATHUTILS_H

#include <cmath>

#include "geometry.h"

namespace pbrt {

namespace iispt {

// ============================================================================
static double gauss(
        double sigma,
        double x
        )
{
    double gauss_left =
            (1.0)
            /
            (
                std::sqrt(
                    2.0 * M_PI * sigma * sigma
                    )
            );
    double gauss_right =
            std::exp(
                -1.0 * (
                    (
                        x * x
                        )
                    /
                    (
                        2 * sigma * sigma
                        )
                    )
                );
    return gauss_left * gauss_right;
}

// ============================================================================
static float points_distance(
        Point2i a,
        Point2i b
        )
{
    float dx2 = a.x - b.x;
    dx2 = dx2 * dx2;
    float dy2 = a.y - b.y;
    dy2 = dy2 * dy2;
    return std::sqrt(dx2 + dy2);
}

// ============================================================================
static bool bounds2i_equals(
        Bounds2i a,
        Bounds2i b
        )
{
    return
            (a.pMin.x == b.pMin.x) &&
            (a.pMin.y == b.pMin.y) &&
            (a.pMax.x == b.pMax.x) &&
            (a.pMax.y == b.pMax.y);
}

} // namespace iispt

} // namespace pbrt

#endif // IISPTMATHUTILS_H
