#ifndef IMAGE_H
#define IMAGE_H

#include <vector>
#include <cmath>
#include <iostream>

static const float GAMMA = 1.8f;

static void applyGamma(std::vector<float> &vals, float gamma) {
    float exp = 1.0f / gamma;
    int n = vals.size();
    for (int i = 0; i < n; i++) {
        float v = vals[i];
        v = std::pow(v, exp);
        vals[i] = v;
    }
}

static void linear(std::vector<float> &vals, float gain,
                   std::vector<float> &out)
{
    if (out.size() != vals.size()) {
        out.resize(vals.size());
    }
    float m = std::pow(2.0f, gain);
    int n = vals.size();
    for (int i = 0; i < n; i++) {
        float v = vals[i];
        std::cout << v << std::endl;
        v *= m;
        out[i] = v;
    }
}

static float computeClipRatio(std::vector<float> &vals)
{
    int clipCount = 0;
    int n = vals.size();
    for (int i = 0; i < n; i++) {
        if (vals[i] > 1.0f) {
            clipCount++;
        }
    }
    return ((float)clipCount) / vals.size();
}

static float computeAverage(std::vector<float> &vals)
{
    double sum = 0.0;
    int n = vals.size();
    for (int i = 0; i < n; i++) {
        sum += vals[i];
    }
    return sum / n;
}

static std::vector<float> autoLinear(std::vector<float> &vals) {
    std::vector<float> out (vals.size());
    float avg = computeAverage(vals);
    if (avg <= 0.0f) {
        return out;
    }
    // 1 = avg * 2^x
    // 1 / avg = 2^x
    // log2 (1 / avg) = x
    float gain = std::log2(1.0f / avg);
    while (1) {
        std::cerr << "autoLinear ["<< gain <<"]\n";
        linear(vals, gain, out);
        float clipRatio = computeClipRatio(out);
        if (clipRatio < 0.05) {
            return out;
        }
        gain -= 1.0f;
    }
}

static void toBytes(std::vector<float> &vals,
                    std::vector<unsigned char> &out)
{
    int n = vals.size();
    for (int i = 0; i < n; i++) {
        float v = vals[i];
        int discrete = int(255.0f * v);
        if (discrete > 255) {
            discrete = 255;
        }
        if (discrete < 0) {
            discrete = 0;
        }
        out[i] = char(discrete);
    }
}

static void tonemapAuto(std::vector<float> &vals,
                                 std::vector<unsigned char> &out) {
    if (out.size() != vals.size()) {
        out.resize(vals.size());
    }
    std::vector<float> linearOut = autoLinear(vals);
    applyGamma(linearOut, GAMMA);
    toBytes(linearOut, out);
}

static void tonemap(std::vector<float> &vals,
                    float gain,
                    std::vector<unsigned char> &out) {
    if (out.size() != vals.size()) {
        out.resize(vals.size());
    }
    std::vector<float> linearOut;
    linear(vals, gain, linearOut);
    applyGamma(linearOut, GAMMA);
    toBytes(linearOut, out);
}

static void flip(std::vector<unsigned char> &vals,
                 int width,
                 int height)
{
    int half = height / 2;
    for (int y = 0; y < half; y++) {
        int specular = height - y - 1;
        for (int x = 0; x < width; x++) {
            int pidx0 = 3 * (y * width + x);
            int pidx1 = 3 * (specular * width + x);
            for (int c = 0; c < 3; c++) {
                int idx0 = pidx0 + c;
                int idx1 = pidx1 + c;
                // TODO loop for each channel
                unsigned char v = vals[idx0];
                vals[idx0] = vals[idx1];
                vals[idx1] = v;
            }
        }
    }
}

#endif // IMAGE_H
