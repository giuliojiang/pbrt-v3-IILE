

// cameras/hemispheric.cpp*
#include "cameras/hemispheric.h"
#include "paramset.h"
#include "sampler.h"
#include "stats.h"
#include "filters/gaussian.h"

#include <iostream>

namespace pbrt {

Float HemisphericCamera::GenerateRay(
        const CameraSample &sample,
        Ray* ray
        ) const {

    ProfilePhase prof(Prof::GenerateCameraRay);
    // Compute environment camera ray direction
    Float theta = Pi * sample.pFilm.y / film->fullResolution.y;
    Float phi = Pi * sample.pFilm.x / film->fullResolution.x;
    Vector3f dir(std::sin(theta) * std::cos(phi), std::cos(theta),
                 std::sin(theta) * std::sin(phi));
    *ray = Ray(Point3f(0, 0, 0), dir, Infinity,
               Lerp(sample.time, shutterOpen, shutterClose));
    ray->medium = medium;
    *ray = CameraToWorld(*ray);

    // Testing ----------------------------------------------------------------

    // Show input camera sample coordinates

    // Show computed world ray

    // Backwards-compute the camera pixel

    return 1;

}

Spectrum HemisphericCamera::getLightSample(
        int x,
        int y,
        Vector3f* wi
        ) {
    Float theta = Pi * y / film->fullResolution.y;
    Float phi = Pi * x / film->fullResolution.x;
    Vector3f dir(std::sin(theta) * std::cos(phi), std::cos(theta),
                 std::sin(theta) * std::sin(phi));
    Ray ray = Ray(Point3f(0, 0, 0), dir, Infinity,
               Lerp(0.0, shutterOpen, shutterClose));
    ray = CameraToWorld(ray);
    *wi = ray.d;

    return film->get_pixel_as_spectrum(Point2i(x, y));
}

HemisphericCamera* CreateHemisphericCamera(
        int xres,
        int yres,
        const Medium *medium,
        Point3f pos,
        Point3f dir,
        Point2i originalPixel
        ) {

    // Create lookAt transform
    const Vector3f up = (dir.x == 0.0 && dir.y == 0.0) ?
                Vector3f(0.f, 1.f, 0.f) :      // Normal already pointing towards Z, set Up vector to be in Y
                Vector3f(0.f, 0.f, 1.f);       // Set up vector to be in Z


    const Point3f look = Point3f(pos.x+dir.x, pos.y+dir.y, pos.z+dir.z);
    const Point3f posAdjusted = Point3f(pos.x+(2), pos.y+(0.1*dir.y), pos.z+(0.1*dir.z));
    const Transform* cameraTransform = new Transform(LookAt(pos, look, up).GetInverseMatrix());

    AnimatedTransform cam2world (
                cameraTransform,
                0.,
                cameraTransform,
                0.);

    // Create film
    const Point2i resolution (xres, yres);
    const Bounds2f cropWindow (Point2f(0., 0.), Point2f(1., 1.));
    std::unique_ptr<Filter> filter (new GaussianFilter(Vector2f(2.f, 2.f), 2.f));
    Float scale = 1.;
    Float diagonal = 35.;
    Float maxSampleLuminance = Infinity;
    // TODO change output file name
    Film* film = new Film(resolution, cropWindow, std::move(filter), diagonal,
                          "aux_" + std::to_string(originalPixel.x) + "_" + std::to_string(originalPixel.y) + ".png",
                          scale, maxSampleLuminance);

    Float shutteropen = 0.f;
    Float shutterclose = 1.f;

    return new HemisphericCamera(cam2world, shutteropen, shutterclose,
                                 film, medium);

}

}
