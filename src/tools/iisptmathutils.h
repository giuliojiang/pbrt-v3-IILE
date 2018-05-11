#ifndef IISPTMATHUTILS_H
#define IISPTMATHUTILS_H

#include <cmath>
#include <numeric>

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

// ============================================================================
static float weighting_distance_positions(
        Point2i a,
        Point2i b,
        float tile_distance
        )
{
    float pdist = points_distance(a, b);
    float res;
    if (tile_distance != 0.0) {
        res = pdist / tile_distance;
    } else {
        res = pdist;
    }
    if (res < 0.0) {
        return 0.0;
    }
    if (res > 1.0) {
        return 1.0;
    }
    return res;
}

// ============================================================================
static float weighting_distance_normals(
        Vector3f a,
        Vector3f b
        )
{
    // Check for invalid vectors
    float al = a.Length();
    float bl = b.Length();
    if (al <= 0.0 || bl <= 0.0) {
        return 1.0;
    }

    a = a / al;
    b = b / bl;

    float dt = Dot(a, b);
    if (dt < 0.0) {
        return 1.0;
    } else {
        return 1.0 - dt;
    }
}

// ============================================================================
static float weighting_normals(
        Vector3f a,
        Vector3f b
        )
{
    // Check for invalid vectors
    float al = a.Length();
    float bl = b.Length();
    if (al <= 0.0 || bl <= 0.0) {
        return 0.0;
    }

    // Normalize
    a = a / al;
    b = b / bl;

    // Compute dot product
    float dt = Dot(a, b);
    if (dt < 0.0) {
        return 0.0;
    } else {
        return dt;
    }
}

// ============================================================================
static void weights_to_probabilities(
        std::vector<float> &weights
        )
{
    float totweight = 0.0;
    for (int i = 0; i < weights.size(); i++) {
        float w = weights[i];
        totweight += w;
    }
    if (totweight > 0.0) {
        for (int i = 0; i < weights.size(); i++) {
            float w = weights[i];
            weights[i] = w / totweight;
        }
    }
}

// ============================================================================
static int positiveModulo(int i, int n) {
    return (i % n + n) % n;
}

// ============================================================================
static float clamp(float x, float min, float max) {
    if (x < min) {
        return min;
    }
    if (x > max) {
        return max;
    }
    return x;
}

// ============================================================================
// Returns the importance of the left side
static float linearRatio(float left, float right) {
    if (left + right <= 0.0) {
        return 0.5;
    }
    return right / (left + right);
}

// ============================================================================
// Returns the importance for point A
static float linearRatioDistance(Point2i x, Point2i a, Point2i b, Point2i &out) {
    float left = Distance(a, x);
    float right = Distance(b, x);
    float leftRatio = linearRatio(left, right);
    out = (a * leftRatio) + (b * (1.0 - leftRatio));
    return leftRatio;
}

// ============================================================================
static void meanStd(std::vector<float> &v, float &meanOut, float &stddevOut)
{
    double sum = std::accumulate(std::begin(v), std::end(v), 0.0);
    double m =  sum / v.size();

    double accum = 0.0;
    std::for_each (std::begin(v), std::end(v), [&](const double d) {
        accum += (d - m) * (d - m);
    });

    double stdev = sqrt(accum / (v.size()-1));

    meanOut = m;
    stddevOut = stdev;
}

} // namespace iispt

} // namespace pbrt

#endif // IISPTMATHUTILS_H
