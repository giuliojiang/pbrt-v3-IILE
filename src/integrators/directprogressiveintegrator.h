#ifndef DIRECTPROGRESSIVEINTEGRATOR_H
#define DIRECTPROGRESSIVEINTEGRATOR_H

#include "pbrt.h"
#include "integrator.h"
#include "scene.h"
#include "integrators/iisptfilmmonitor.h"
#include "camera.h"

namespace pbrt {

class DirectProgressiveIntegrator
{
public:
    // Fields =================================================================
    std::shared_ptr<const Camera> camera;
    Bounds2i pixelBounds;
    std::unique_ptr<Sampler> sampler;
    std::vector<int> nLightSamples;
    const int maxDepth = 5;

    // Constructor ============================================================
    DirectProgressiveIntegrator(
            std::shared_ptr<const Camera> camera,
            std::unique_ptr<Sampler> sampler,
            Bounds2i pixelBounds
            )
    {
        this->camera = camera;
        this->sampler = std::move(sampler);
        this->pixelBounds = pixelBounds;
    }

    // Methods ================================================================

    Spectrum SpecularReflect(
        const RayDifferential &ray, const SurfaceInteraction &isect,
        const Scene &scene, Sampler &sampler, MemoryArena &arena, int depth) const;

    Spectrum SpecularTransmit(
        const RayDifferential &ray, const SurfaceInteraction &isect,
        const Scene &scene, Sampler &sampler, MemoryArena &arena, int depth) const;

    void preprocess(
            const Scene &scene
            );

    Spectrum Li(const RayDifferential &ray,
                                          const Scene &scene, Sampler &sampler,
                                          MemoryArena &arena, int depth) const;

    void RenderOnePass(
            const Scene &scene,
            IisptFilmMonitor* filmMonitor
            );

};

}

#endif // DIRECTPROGRESSIVEINTEGRATOR_H
