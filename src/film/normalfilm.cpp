#include "normalfilm.h"

namespace pbrt {

// ============================================================================
void NormalFilm::set_camera_coord(int x, int y, Normal3f n) {
    film->set_camera_coord(x, y, PfmItem(n.x, n.y, n.z));
}

// ============================================================================
void NormalFilm::write(std::string filename) {
    film->write(filename);
}

// ============================================================================
void NormalFilm::clear()
{
    film->set_all(PfmItem(0.0, 0.0, 0.0));
}

}// namespace pbrt
