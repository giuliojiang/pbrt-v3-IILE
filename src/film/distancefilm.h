#ifndef DISTANCEFILM_H
#define DISTANCEFILM_H

#include <memory>
#include <film/imagefilm.h>

namespace pbrt {

class DistanceFilm
{

private:
    int width;
    int height;
    std::shared_ptr<ImageFilm> film;

public:

    // Constructor ============================================================
    DistanceFilm(
            int width,
            int height
            ) :
        width(width),
        height(height)
    {
        film = std::shared_ptr<ImageFilm>(
                new ImageFilm(
                    width,
                    height,
                    1
                )
        );
    }

    // Set pixel ==============================================================
    void set(int x, int y, float val);

    // Write image ============================================================
    void write(std::string filename);
};

} // namespace pbrt

#endif // DISTANCEFILM_H