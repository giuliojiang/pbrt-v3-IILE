#include "distancefilm.h"

namespace pbrt {

// ============================================================================
void DistanceFilm::set_camera_coord(int x, int y, float val) {
    film->set_camera_coord(x, y, PfmItem(val));
}

// ============================================================================
void DistanceFilm::write(std::string filename) {
    film->write(filename);
}

// ============================================================================
void DistanceFilm::clear()
{
    film->set_all(PfmItem(0.0, 0.0, 0.0));
}

} // namespace pbrt
