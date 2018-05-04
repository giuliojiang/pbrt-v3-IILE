#ifndef NORMALFILM_H
#define NORMALFILM_H

#include <memory>
#include <film/imagefilm.h>
#include "geometry.h"

namespace pbrt {

class NormalFilm
{

private:

    // Fields =================================================================
    std::shared_ptr<ImageFilm> film;

public:

    virtual ~NormalFilm() = default;

    // Constructor ============================================================
    NormalFilm(
            int width,
            int height
            )
    {
        film = std::shared_ptr<ImageFilm>(
                    new ImageFilm(
                        width, height, 3
                        )
                    );
    }

    // Set pixel ==============================================================
    void set_camera_coord(int x, int y, Normal3f n);

    // Write image ============================================================
    void write(std::string filename);

    // Get Image Film =========================================================
    std::shared_ptr<ImageFilm> get_image_film() {
        return film;
    }

    // Clear ==================================================================
    void clear();
};

} // namespace pbrt

#endif // NORMALFILM_H
