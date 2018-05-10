#include "imagefilm.h"

#include "geometry.h"
#include "imageio.h"
#include <fstream>
#include <csignal>

namespace pbrt {

// Utilities ==================================================================

// Writes a float, little endian
static void write_float_value(std::ofstream &ofs, float val) {
    ofs.write((char *)&val, sizeof(float));
}


// ============================================================================
void ImageFilm::set(int x, int y, PfmItem pixel) {

    int idx = y * width + x;
    data[idx] = pixel;

}

void ImageFilm::set_camera_coord(int xx, int yy, PfmItem pixel)
{
    int x = xx;
    int y = height - 1 - yy;
    set(x, y, pixel);
}

// ============================================================================
PfmItem ImageFilm::get(int x, int y) {

    int idx = y * width + x;
    return data[idx];

}

// ============================================================================
void ImageFilm::write(std::string filename) {

    std::ofstream ofs (filename, std::ios::binary);

    // Write type line
    if (num_components == 1) {
        ofs << "Pf\n";
    } else {
        ofs << "PF\n";
    }

    // Write [xres] [yres]
    ofs << width << " " << height << "\n";

    // Write byte order (little endian)
    ofs << "-1.0\n";

    // Write pixels
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            PfmItem pix = data[y * width + x];
            if (num_components == 1) {
                float val = pix.get_single_component();
                write_float_value(ofs, val);
            } else {
                float r;
                float g;
                float b;
                pix.get_triple_component(r, g, b);
                write_float_value(ofs, r);
                write_float_value(ofs, g);
                write_float_value(ofs, b);
            }
        }
    }

    // Close
    ofs.close();

}

// ============================================================================
void ImageFilm::pbrt_write_image(std::string filename) {

    Bounds2i cropped_pixel_bounds (
                Point2i(0, 0),
                Point2i(width, height)
                );

    Point2i full_resolution (
                width, height
                );

    std::unique_ptr<Float[]> rgb (
                new Float[get_components() * cropped_pixel_bounds.Area()]
                );

    // Populate the array
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            PfmItem item = get(x, y);
            if (num_components == 1) {
                Float it = item.get_single_component();
                rgb[y*width + x] = it;
            } else {
                Float r, g, b;
                item.get_triple_component(r, g, b);
                int pix_index = y * width + x;
                int array_index = 3 * pix_index;
                rgb[array_index + 0] = r;
                rgb[array_index + 1] = g;
                rgb[array_index + 2] = b;
            }
        }
    }

    pbrt::WriteImage(filename, &rgb[0], cropped_pixel_bounds, full_resolution);

}

// ============================================================================

void ImageFilm::set_all(
        PfmItem pix
        )
{
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            set(x, y, pix);
        }
    }
}

// ============================================================================
// Populate from float array

void ImageFilm::populate_from_float_array(float* floats) {
    if (num_components == 1) {
        int fidx = 0;
        int limit = width * height;
        for (int i = 0; i < limit; i++) {
            data[i] = PfmItem(floats[fidx]);
            fidx++;
        }
    } else {
        int fidx = 0;
        int limit = width * height;
        for (int i = 0; i < limit; i++) {
            float r, g, b;
            r = floats[fidx];
            fidx++;
            g = floats[fidx];
            fidx++;
            b = floats[fidx];
            fidx++;
            data[i] = PfmItem(r, g, b);
        }
    }
}

// ============================================================================
// Compute mean

float ImageFilm::computeMean()
{
    double sum = 0.0;
    int count = 0;

    for (int i = 0; i < data.size(); i++) {
        PfmItem item = data[i];
        if (num_components == 1) {
            sum += item.get_single_component();
            count += 1;
        } else {
            float r, g, b;
            item.get_triple_component(r, g, b);
            sum += (r + g + b);
            count += 3;
        }
    }

    return sum / count;
}

// ============================================================================
// Compute mean while purging extraordinarily out-of-range values

float ImageFilm::purgeAndComputeMean()
{
    float threshold = 200.0;

    computeMax();

    float firstMean = computeMean();

    if (firstMean > 0.0 && (maxVal / firstMean) > threshold) {
        // Purge
        if (num_components == 1) {
            set_all(PfmItem(0.0));
        } else {
            set_all(PfmItem(0.0, 0.0, 0.0));
        }
        return 0.0;
    }

    return firstMean;

}

// ============================================================================

float ImageFilm::computeMax()
{
    for (int i = 0; i < data.size(); i++) {
        PfmItem item = data[i];
        if (num_components == 1) {
            float x = item.get_single_component();
            maxVal = std::max(maxVal, x);
        } else {
            float r, g, b;
            item.get_triple_component(r, g, b);
            maxVal = std::max(maxVal, r);
            maxVal = std::max(maxVal, g);
            maxVal = std::max(maxVal, b);
        }
    }

    return maxVal;
}

// ============================================================================
// Map

void ImageFilm::map(std::function<float(float)> func)
{
    for (int i = 0; i < data.size(); i++) {
        PfmItem item = data[i];
        if (num_components == 1) {
            item.r = func(item.r);
        } else {
            item.r = func(item.r);
            item.g = func(item.g);
            item.b = func(item.b);
        }
        data[i] = item;
    }
}

// ============================================================================
// Multiply
void ImageFilm::multiply(float ratio)
{
    map([&](float v) {
        return v * ratio;
    });
}

// ============================================================================
// Log
void ImageFilm::positiveLog()
{
    map([&](float v) {
        float vv = v;
        if (vv <= 0.0) {
            vv = 0.0;
        }
        return std::log(1.0 + vv);
    });
}

// ============================================================================
// PositiveLogInverse
void ImageFilm::positiveLogInverse()
{
    map([&](float v) {
        float y = v;
        if (y < 0.0) {
            y = 0.0;
        }
        return std::exp(y) - 1.0;
    });
}

// ============================================================================
// Add
void ImageFilm::add(float amount)
{
    map([&](float v) {
        return v + amount;
    });
}

// ============================================================================
// Normalize
void ImageFilm::normalize(float minVal, float maxVal)
{
    float mid = (minVal + maxVal) / 2.0;
    float r = maxVal - mid;
    if (r == 0) {
        r = 1.0;
    }

    map([&](float v) {
        float x = v;
        x = x - mid;
        x = x / r;
        if (x < -1.0) {
            return -1.0f;
        } else if (x > 1.0) {
            return 1.0f;
        } else {
            return x;
        }
    });
}

// ============================================================================
void ImageFilm::testPrintValueSamples()
{
    for (int i = 0; i < data.size(); i += 51) {
        if (num_components == 1) {
            float val = data[i].get_single_component();
            std::cerr << " " << val;
        } else {
            float r, g, b;
            data[i].get_triple_component(r, g, b);
            std::cerr << " ["<< r <<"]["<< g <<"]["<< b <<"]";
        }
    }
    std::cerr << std::endl;
}

} // namespace pbrt
