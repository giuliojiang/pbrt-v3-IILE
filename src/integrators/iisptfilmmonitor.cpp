#include "iisptfilmmonitor.h"

namespace pbrt {

// ============================================================================
IisptFilmMonitor::IisptFilmMonitor(
        Bounds2i film_bounds
        ) {

    this->film_bounds = film_bounds;

    // Initialize sampling density map
    Vector2i film_diagonal = film_bounds.Diagonal();
    for (int y = 0; y <= film_diagonal.y; y++) {
        std::vector<IisptPixel> row;
        for (int x = 0; x <= film_diagonal.x; x++) {
            IisptPixel pix;
            row.push_back(pix);
        }
        pixels.push_back(row);
    }
}

// ============================================================================

void IisptFilmMonitor::add_sample(Point2i pt, Spectrum s, double weight)
{
    std::unique_lock<std::recursive_mutex> lock (mutex);

    execute_on_pixel([&](int fx, int fy) {
        IisptPixel pix = (pixels[fy])[fx];
        pix.weight += weight;

        float rgb[3];
        s.ToRGB(rgb);
        pix.r += rgb[0];
        pix.g += rgb[1];
        pix.b += rgb[2];

        (pixels[fy])[fx] = pix;
    }, pt.x, pt.y);

}

// ============================================================================

void IisptFilmMonitor::add_n_samples(
        std::vector<Point2i> &pts,
        std::vector<Spectrum> &ss,
        std::vector<double> &weights
        )
{
    std::unique_lock<std::recursive_mutex> lock (mutex);

    for (int i = 0; i < pts.size(); i++) {
        Point2i pt = pts[i];
        execute_on_pixel([&](int fx, int fy) {
            IisptPixel pix = (pixels[fy])[fx];
            pix.weight += weights[i];

            float rgb[3];
            ss[i].ToRGB(rgb);
            pix.r += rgb[0];
            pix.g += rgb[1];
            pix.b += rgb[2];

            (pixels[fy])[fx] = pix;
        }, pt.x, pt.y);
    }

}

// ============================================================================

void IisptFilmMonitor::addFromIntensityFilm(
        IntensityFilm* intensityFilm
        )
{
    std::unique_lock<std::recursive_mutex> lock (mutex);

    // The intensity film is straight up while the film monitor
    // data is in camera format

    std::shared_ptr<ImageFilm> imageFilm = intensityFilm->get_image_film();
    int height = imageFilm->get_height();
    int width = imageFilm->get_width();
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            PfmItem item = imageFilm->get(x, height - 1 - y);
            IisptPixel pix = (pixels[y])[x];
            pix.weight += 1.0;
            float r, g, b;
            item.get_triple_component(r, g, b);
            pix.r += r;
            pix.g += g;
            pix.b += b;

            (pixels[y])[x] = pix;
        }
    }

}

// ============================================================================

Bounds2i IisptFilmMonitor::get_film_bounds()
{
    std::unique_lock<std::recursive_mutex> lock (mutex);

    return film_bounds;
}

// ============================================================================

void IisptFilmMonitor::execute_on_pixel(
        std::function<void (int, int)> func,
        int x,
        int y)
{
    int xstart = get_film_bounds().pMin.x;
    int ystart = get_film_bounds().pMin.y;
    int film_x = x - xstart;
    int film_y = y - ystart;
    func(film_x, film_y);
}

// ============================================================================

std::shared_ptr<IntensityFilm> IisptFilmMonitor::to_intensity_film_priv(
        bool reversed)
{
    Vector2i diagonal = film_bounds.Diagonal();
    int width = diagonal.x + 1;
    int height = diagonal.y + 1;
    std::cerr << "Width and height are ["<< width <<"] ["<< height <<"]" << std::endl;
    std::cerr << "Computed assuming exclusive pMax are ["<< (film_bounds.pMax.x - film_bounds.pMin.x) <<"] ["<< (film_bounds.pMax.y - film_bounds.pMin.y) <<"]" << std::endl;

    std::shared_ptr<IntensityFilm> intensity_film (
                new IntensityFilm(
                    width,
                    height
                    )
                );

    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            IisptPixel pix = (pixels[y])[x];
            if (pix.weight > 0.0) {
                double r = pix.r / (pix.weight);
                double g = pix.g / (pix.weight);
                double b = pix.b / (pix.weight);
                if (reversed) {
                    intensity_film->set_camera_coord(
                                x,
                                y,
                                (float) r,
                                (float) g,
                                (float) b
                                );
                } else {
                    intensity_film->set(
                                x,
                                y,
                                (float) r,
                                (float) g,
                                (float) b
                                );
                }
            }
        }
    }

    return intensity_film;
}

// ============================================================================

std::shared_ptr<IntensityFilm> IisptFilmMonitor::to_intensity_film()
{
    std::unique_lock<std::recursive_mutex> lock (mutex);

    std::shared_ptr<IntensityFilm> intensity_film =
            to_intensity_film_priv(false);

    return intensity_film;
}

// ============================================================================
// Reverse intensity film
// If the current film is a camera film and output is for viewing

std::shared_ptr<IntensityFilm> IisptFilmMonitor::to_intensity_film_reversed()
{
    std::unique_lock<std::recursive_mutex> lock (mutex);

    std::shared_ptr<IntensityFilm> intensity_film =
            to_intensity_film_priv(true);

    return intensity_film;
}

// ============================================================================

void IisptFilmMonitor::merge_from(
        IisptFilmMonitor* other
        )
{
    std::unique_lock<std::recursive_mutex> lock (mutex);

    if (!iispt::bounds2i_equals(
                this->film_bounds,
                other->film_bounds
                )) {
        std::cerr << "iisptfilmmonitor.cpp::merge_from film bounds don't match!\n";
        std::raise(SIGKILL);
    }

    for (int y = film_bounds.pMin.y; y < film_bounds.pMax.y; y++) {
        for (int x = film_bounds.pMin.x; x < film_bounds.pMax.x; x++) {
            execute_on_pixel([&](int fx, int fy) {
                IisptPixel pix = (pixels[fy])[fx];
                IisptPixel ot = (other->pixels[fy])[fx];

                // Normalize the pixels
                pix.normalize();
                ot.normalize();

                pix.r += ot.r;
                pix.g += ot.g;
                pix.b += ot.b;
                (pixels[fy])[fx] = pix;
            }, x, y);
        }
    }

}

} // namespace pbrt
