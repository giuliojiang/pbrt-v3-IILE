#if defined(_MSC_VER)
#define NOMINMAX
#pragma once
#endif

#ifndef PBRT_CAMERAS_HEMISPHERIC_H
#define PBRT_CAMERAS_HEMISPHERIC_H

// cameras/hemispheric.h*
#include "camera.h"
#include "film.h"
#include "film/intensityfilm.h"

namespace pbrt {

// ============================================================================

// HemisphericCamera Declarations
class HemisphericCamera : public Camera {

private:
    // Fields -----------------------------------------------------------------
    std::shared_ptr<IntensityFilm> nn_film = nullptr;

    // Location and direction of this camera
    Vector3f look_direction;
    Point3f originPosition;

public:

    // Constructor ------------------------------------------------------------
    HemisphericCamera(
            const AnimatedTransform &CameraToWorld,
            Float shutterOpen,
            Float shutterClose,
            Film* film,
            const Medium* medium,
            Vector3f look_direction,
            Point3f originPosition,
            std::unique_ptr<Transform> WorldToCamera
            ) :
        Camera(CameraToWorld, shutterOpen, shutterClose, film, medium)
    {

        this->look_direction = look_direction;
        this->originPosition = originPosition;
        this->WorldToCamera = std::move(WorldToCamera);

    }

    // Public methods =========================================================

    Float GenerateRay(
            const CameraSample &sample,
            Ray *
            ) const;

    Spectrum getLightSample(
            int x,
            int y,
            Vector3f* wi
            );

    void set_nn_film(
            std::shared_ptr<IntensityFilm> nn_film
            );

    Spectrum get_light_sample_nn(
            int x,
            int y,
            Vector3f* wi
            );

    Spectrum get_light_sample_nn_importance(
            float rx, // Random rx and ry uniform floats
            float ry,
            Vector3f* wi,
            float* prob // Probability of getting the selected sample
            );

    void compute_cdfs();

    Vector3f get_look_direction() {
        return this->look_direction;
    }

    Point3f getOriginPosition() {
        return this->originPosition;
    }

};

// ============================================================================

HemisphericCamera* CreateHemisphericCamera(
        int xres,
        int yres,
        const Medium *medium,
        Point3f pos,
        Vector3f dir,
        std::string output_file_name
        );


} // namespace pbrt


#endif // HEMISPHERIC_H
