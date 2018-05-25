#include "directprogressiveintegrator.h"

namespace pbrt {

void DirectProgressiveIntegrator::preprocess(
        const Scene &scene
        )
{
    // Compute number of samples to use for each light
    for (const auto &light : scene.lights)
        nLightSamples.push_back(sampler->RoundCount(light->nSamples));

    // Request samples for sampling all lights
    for (int i = 0; i < maxDepth; ++i) {
        for (size_t j = 0; j < scene.lights.size(); ++j) {
            sampler->Request2DArray(nLightSamples[j]);
            sampler->Request2DArray(nLightSamples[j]);
        }
    }
}

Spectrum DirectProgressiveIntegrator::Li(const RayDifferential &ray,
                                      const Scene &scene, Sampler &sampler,
                                      MemoryArena &arena, int depth) const {
    ProfilePhase p(Prof::SamplerIntegratorLi);
    Spectrum L(0.f);
    // Find closest ray intersection or return background radiance
    SurfaceInteraction isect;
    if (!scene.Intersect(ray, &isect)) {
        for (const auto &light : scene.lights) L += light->Le(ray);
        return L;
    }

    // Compute scattering functions for surface interaction
    isect.ComputeScatteringFunctions(ray, arena);
    if (!isect.bsdf)
        return Li(isect.SpawnRay(ray.d), scene, sampler, arena, depth);
    Vector3f wo = isect.wo;
    // Compute emitted light if ray hit an area light source
    L += isect.Le(wo);
    if (scene.lights.size() > 0) {
        // Compute direct lighting for _DirectLightingIntegrator_ integrator
        L += UniformSampleAllLights(isect, scene, arena, sampler,
                                    nLightSamples);
    }
    if (depth + 1 < maxDepth) {
        Vector3f wi;
        // Trace rays for specular reflection and refraction
        L += SpecularReflect(ray, isect, scene, sampler, arena, depth);
        L += SpecularTransmit(ray, isect, scene, sampler, arena, depth);
    }
    return L;
}


void DirectProgressiveIntegrator::RenderOnePass(
        const Scene &scene,
        IisptFilmMonitor* filmMonitor
        )
{
    // Compute number of tiles, _nTiles_, to use for parallel rendering
    Bounds2i sampleBounds = camera->film->GetSampleBounds();

    int x0 = sampleBounds.pMin.x;
    int x1 = sampleBounds.pMax.x;
    int y0 = sampleBounds.pMin.y;
    int y1 = sampleBounds.pMax.y;
    Bounds2i tileBounds (Point2i(x0, y0), Point2i(x1, y1));

    std::vector<Point2i> additionPoints;
    std::vector<Spectrum> additionSpectrums;
    std::vector<double> additionWeights;

    MemoryArena arena;

    // Get _FilmTile_ for tile
    std::unique_ptr<FilmTile> filmTile =
        camera->film->GetFilmTile(tileBounds);

    for (Point2i pixel : tileBounds) {
        {
            sampler->StartPixel(pixel);
        }

        // Do this check after the StartPixel() call; this keeps
        // the usage of RNG values from (most) Samplers that use
        // RNGs consistent, which improves reproducability /
        // debugging.
        if (!InsideExclusive(pixel, pixelBounds))
            continue;

        // Run the pixel loop only once to force rendering a single pass
        {
            // Initialize _CameraSample_ for current sample
            CameraSample cameraSample =
                sampler->GetCameraSample(pixel);

            // Generate camera ray for current sample
            RayDifferential ray;
            Float rayWeight =
                camera->GenerateRayDifferential(cameraSample, &ray);
            ray.ScaleDifferentials(
                1 / std::sqrt((Float)sampler->samplesPerPixel));

            // Evaluate radiance along camera ray
            Spectrum L(0.f);
            if (rayWeight > 0) L = Li(ray, scene, *sampler, arena, 0);

            // Issue warning if unexpected radiance value returned
            if (L.HasNaNs()) {
                LOG(ERROR) << StringPrintf(
                    "Not-a-number radiance value returned "
                    "for pixel (%d, %d), sample %d. Setting to black.",
                    pixel.x, pixel.y,
                    (int)sampler->CurrentSampleNumber());
                L = Spectrum(0.f);
            } else if (L.y() < -1e-5) {
                LOG(ERROR) << StringPrintf(
                    "Negative luminance value, %f, returned "
                    "for pixel (%d, %d), sample %d. Setting to black.",
                    L.y(), pixel.x, pixel.y,
                    (int)sampler->CurrentSampleNumber());
                L = Spectrum(0.f);
            } else if (std::isinf(L.y())) {
                  LOG(ERROR) << StringPrintf(
                    "Infinite luminance value returned "
                    "for pixel (%d, %d), sample %d. Setting to black.",
                    pixel.x, pixel.y,
                    (int)sampler->CurrentSampleNumber());
                L = Spectrum(0.f);
            }
            VLOG(1) << "Camera sample: " << cameraSample << " -> ray: " <<
                ray << " -> L = " << L;

            // Add camera ray's contribution to image
            additionPoints.push_back(pixel);
            additionSpectrums.push_back(L);
            additionWeights.push_back(rayWeight);

            // Free _MemoryArena_ memory from computing image sample
            // value
            arena.Reset();
        }

    }

    filmMonitor->add_n_samples(additionPoints, additionSpectrums, additionWeights);


}

Spectrum DirectProgressiveIntegrator::SpecularReflect(
    const RayDifferential &ray, const SurfaceInteraction &isect,
    const Scene &scene, Sampler &sampler, MemoryArena &arena, int depth) const {
    // Compute specular reflection direction _wi_ and BSDF value
    Vector3f wo = isect.wo, wi;
    Float pdf;
    BxDFType type = BxDFType(BSDF_REFLECTION | BSDF_SPECULAR);
    Spectrum f = isect.bsdf->Sample_f(wo, &wi, sampler.Get2D(), &pdf, type);

    // Return contribution of specular reflection
    const Normal3f &ns = isect.shading.n;
    if (pdf > 0.f && !f.IsBlack() && AbsDot(wi, ns) != 0.f) {
        // Compute ray differential _rd_ for specular reflection
        RayDifferential rd = isect.SpawnRay(wi);
        if (ray.hasDifferentials) {
            rd.hasDifferentials = true;
            rd.rxOrigin = isect.p + isect.dpdx;
            rd.ryOrigin = isect.p + isect.dpdy;
            // Compute differential reflected directions
            Normal3f dndx = isect.shading.dndu * isect.dudx +
                            isect.shading.dndv * isect.dvdx;
            Normal3f dndy = isect.shading.dndu * isect.dudy +
                            isect.shading.dndv * isect.dvdy;
            Vector3f dwodx = -ray.rxDirection - wo,
                     dwody = -ray.ryDirection - wo;
            Float dDNdx = Dot(dwodx, ns) + Dot(wo, dndx);
            Float dDNdy = Dot(dwody, ns) + Dot(wo, dndy);
            rd.rxDirection =
                wi - dwodx + 2.f * Vector3f(Dot(wo, ns) * dndx + dDNdx * ns);
            rd.ryDirection =
                wi - dwody + 2.f * Vector3f(Dot(wo, ns) * dndy + dDNdy * ns);
        }
        return f * Li(rd, scene, sampler, arena, depth + 1) * AbsDot(wi, ns) /
               pdf;
    } else
        return Spectrum(0.f);
}

Spectrum DirectProgressiveIntegrator::SpecularTransmit(
    const RayDifferential &ray, const SurfaceInteraction &isect,
    const Scene &scene, Sampler &sampler, MemoryArena &arena, int depth) const {
    Vector3f wo = isect.wo, wi;
    Float pdf;
    const Point3f &p = isect.p;
    const Normal3f &ns = isect.shading.n;
    const BSDF &bsdf = *isect.bsdf;
    Spectrum f = bsdf.Sample_f(wo, &wi, sampler.Get2D(), &pdf,
                               BxDFType(BSDF_TRANSMISSION | BSDF_SPECULAR));
    Spectrum L = Spectrum(0.f);
    if (pdf > 0.f && !f.IsBlack() && AbsDot(wi, ns) != 0.f) {
        // Compute ray differential _rd_ for specular transmission
        RayDifferential rd = isect.SpawnRay(wi);
        if (ray.hasDifferentials) {
            rd.hasDifferentials = true;
            rd.rxOrigin = p + isect.dpdx;
            rd.ryOrigin = p + isect.dpdy;

            Float eta = bsdf.eta;
            Vector3f w = -wo;
            if (Dot(wo, ns) < 0) eta = 1.f / eta;

            Normal3f dndx = isect.shading.dndu * isect.dudx +
                            isect.shading.dndv * isect.dvdx;
            Normal3f dndy = isect.shading.dndu * isect.dudy +
                            isect.shading.dndv * isect.dvdy;

            Vector3f dwodx = -ray.rxDirection - wo,
                     dwody = -ray.ryDirection - wo;
            Float dDNdx = Dot(dwodx, ns) + Dot(wo, dndx);
            Float dDNdy = Dot(dwody, ns) + Dot(wo, dndy);

            Float mu = eta * Dot(w, ns) - Dot(wi, ns);
            Float dmudx =
                (eta - (eta * eta * Dot(w, ns)) / Dot(wi, ns)) * dDNdx;
            Float dmudy =
                (eta - (eta * eta * Dot(w, ns)) / Dot(wi, ns)) * dDNdy;

            rd.rxDirection =
                wi + eta * dwodx - Vector3f(mu * dndx + dmudx * ns);
            rd.ryDirection =
                wi + eta * dwody - Vector3f(mu * dndy + dmudy * ns);
        }
        L = f * Li(rd, scene, sampler, arena, depth + 1) * AbsDot(wi, ns) / pdf;
    }
    return L;
}

}
