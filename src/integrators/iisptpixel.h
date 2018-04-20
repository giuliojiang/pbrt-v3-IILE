#ifndef IISPTPIXEL_H
#define IISPTPIXEL_H

namespace pbrt {

struct IisptPixel {
    double r = 0.0;
    double g = 0.0;
    double b = 0.0;
    double weight = 0.0;

    void normalize()
    {
        if (weight > 0.0) {
            r /= weight;
            g /= weight;
            b /= weight;
        }
        weight = 1.0;
    }

};



}

#endif // IISPTPIXEL_H
