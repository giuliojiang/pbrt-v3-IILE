#include "iisptrenderrunner.h"
#include "lightdistrib.h"

#include <chrono>

namespace pbrt {

// ============================================================================
// Estimate direct (evaluate 1 hemisphere pixel)
// Output is scaled by 1/pp(x)
//        which is the probability of sampling the specific
//        pp is not a 0-1 probability but it's 1-centered
//        for a uniform distribution
// See intensityfilm.cpp for more detail
static Spectrum estimate_direct(
        const Interaction &it,
        float rx, // input uniform random floats
        float ry,
        HemisphericCamera* auxCamera
        ) {

    bool specular = false; // Default value

    BxDFType bsdfFlags =
        specular ? BSDF_ALL : BxDFType(BSDF_ALL & ~BSDF_SPECULAR);
    Spectrum Ld(0.f);

    // Sample light source with multiple importance sampling
    Vector3f wi;
    Float lightPdf = 1.0 / 6.28;
    Float scatteringPdf = 0;
    VisibilityTester visibility;

    // Sample_Li with custom code to sample from hemisphere instead -----------
    // Writes into wi the vector towards the light source. Derived from hem_x and hem_y
    // For the hemisphere, lightPdf would be a constant (probably 1/(2pi))
    // We don't need to have a visibility object

    // Get jacobian-adjusted sample, camera coordinates
    float pp_prob;
    Spectrum Li = auxCamera->get_light_sample_nn_importance(
                rx,
                ry,
                &wi,
                &pp_prob
                );
    if (pp_prob <= 1e-5) {
        return Spectrum(0.0);
    }

    // Combine incoming light, BRDF and viewing direction ---------------------
    if (lightPdf > 0 && !Li.IsBlack()) {
        // Compute BSDF or phase function's value for light sample

        Spectrum f;

        if (it.IsSurfaceInteraction()) {

            // Evaluate BSDF for light sampling strategy
            const SurfaceInteraction &isect = (const SurfaceInteraction &)it;

            f = isect.bsdf->f(isect.wo, wi, bsdfFlags) * AbsDot(wi, isect.shading.n);

            scatteringPdf = isect.bsdf->Pdf(isect.wo, wi, bsdfFlags);

        } else {

            // Evaluate phase function for light sampling strategy
            const MediumInteraction &mi = (const MediumInteraction &)it;
            Float p = mi.phase->p(mi.wo, wi);
            f = Spectrum(p);
            scatteringPdf = p;

        }

        if (!f.IsBlack()) {
            // Compute effect of visibility for light source sample
            // Always unoccluded visibility using hemispherical map

            // Add light's contribution to reflected radiance
            if (!Li.IsBlack()) {
                Ld += f * Li / lightPdf;
            }
        }
    }

    // Skipping sampling BSDF with multiple importance sampling
    // because we gather all information from lights (hemisphere)

    return Ld / pp_prob;

}

// ============================================================================
// Sample hemisphere
Spectrum IisptRenderRunner::sample_hemisphere(
        const Interaction &it,
        HemisphericCamera* auxCamera
        )
{
    Spectrum L(0.f);

    auxCamera->compute_cdfs();

    for (int i = 0; i < HEMISPHERIC_IMPORTANCE_SAMPLES; i++) {
        float rx = rng->uniform_float();
        float ry = rng->uniform_float();
        L += estimate_direct(it, rx, ry, auxCamera);
    }

    return L / HEMISPHERIC_IMPORTANCE_SAMPLES;

}

// ============================================================================
IisptRenderRunner::IisptRenderRunner(
        IISPTIntegrator* iispt_integrator,
        std::shared_ptr<IisptScheduleMonitor> schedule_monitor,
        std::shared_ptr<IisptFilmMonitor> film_monitor,
        std::shared_ptr<const Camera> main_camera,
        std::shared_ptr<Camera> dcamera,
        std::shared_ptr<Sampler> sampler,
        int thread_no,
        Bounds2i pixel_bounds
        )
{
    this->iispt_integrator = iispt_integrator;

    this->schedule_monitor = schedule_monitor;

    this->film_monitor = film_monitor;

    this->d_integrator = CreateIISPTdIntegrator(dcamera);
    // Preprocess is called on run()

    std::cerr << "iisptrenderrunner.cpp: Creating NN connector\n";
    this->nn_connector = std::unique_ptr<IisptNnConnector>(
                new IisptNnConnector()
                );
    std::cerr << "iisptrenderrunner.cpp: NN connector created\n";

    // TODO remove fixed seed
    this->rng = std::unique_ptr<IisptRng>(
                new IisptRng(thread_no)
                );

    this->sampler = std::unique_ptr<Sampler>(
                sampler->Clone(thread_no)
                );

    this->dcamera = dcamera;

    this->thread_no = thread_no;

    this->pixel_bounds = pixel_bounds;

    this->main_camera = main_camera;
}

// ============================================================================
void IisptRenderRunner::run(const Scene &scene)
{
    std::cerr << "iisptrenderrunner.cpp: Preprocessing on d integrator\n";
    d_integrator->Preprocess(scene);
    int loop_count = 0;
    std::cerr << "iisptrenderrunner.cpp: Creating light distribution\n";
    std::unique_ptr<LightDistribution> lightDistribution =
            CreateLightSampleDistribution(std::string("spatial"), scene);
    float radius = 0.0;

    std::cerr << "iisptrenderrunner.cpp: Starting render loop\n";

    while (1) {

        std::cerr << "iisptrenderrunner.cpp loop count " << loop_count << " radius ["<< radius <<"]" << std::endl;

        if (stop) {
            return;
        }

        MemoryArena arena;

        // --------------------------------------------------------------------
        //    * Obtain current __radius__ from the __ScheduleMonitor__. The ScheduleMonitor updates its internal count automatically
        radius = schedule_monitor->get_current_radius();

        // --------------------------------------------------------------------
        //    * Use the __RNG__ to generate 2 random pixel samples. Look up the density of the samples and select the one that has lower density
        int pix1x;
        int pix1y;
        generate_random_pixel(&pix1x, &pix1y);

        int pix2x;
        int pix2y;
        generate_random_pixel(&pix2x, &pix2y);

        double pix1d = film_monitor->get_pixel_sampling_density(pix1x, pix1y);
        double pix2d = film_monitor->get_pixel_sampling_density(pix2x, pix2y);

        int x;
        int y;
        if (pix1d < pix2d) {
            x = pix1x;
            y = pix1y;
        } else {
            x = pix2x;
            y = pix2y;
        }
        Point2i pixel = Point2i(x, y);


        // --------------------------------------------------------------------
        //    * Obtain camera ray and shoot into scene. If no __intersection__ is found, evaluate infinite lights

        // sampler->StartPixel(pixel);
        sampler_next_pixel();
        if (!InsideExclusive(pixel, pixel_bounds)) {
            continue;
        }

        CameraSample camera_sample =
                sampler->GetCameraSample(pixel);

        RayDifferential r;
        Float ray_weight =
                main_camera->GenerateRayDifferential(
                    camera_sample,
                    &r
                    );
        r.ScaleDifferentials(1.0); // Not scaling based on samples per
                                     // pixel here

        SurfaceInteraction isect;
        Spectrum beta;
        Spectrum background;
        RayDifferential ray;

        // Find intersection point
        bool intersection_found = find_intersection(
                    r,
                    scene,
                    arena,
                    &isect,
                    &ray,
                    &beta,
                    &background
                    );

        if (!intersection_found) {
            // Record background light
            film_monitor->add_sample(
                        pixel,
                        background,
                        1.0
                        );
            continue;
        } else if (intersection_found && beta.y() <= 0.0) {
            // Intersection found but black pixel
            film_monitor->add_sample(
                        pixel,
                        Spectrum(0.0),
                        1.0
                        );
            continue;
        }

        // The intersection object is isect

        // --------------------------------------------------------------------
        //    * Create __auxCamera__ and use the __dIntegrator__ to render a view

        // Invert normal if surface normal points inwards
        Normal3f surface_normal = isect.n;
        Vector3f sf_norm_vec = Vector3f(isect.n.x, isect.n.y, isect.n.z);
        Vector3f ray_vec = Vector3f(ray.d.x, ray.d.y, ray.d.z);
        if (Dot(sf_norm_vec, ray_vec) > 0.0) {
            surface_normal = Normal3f(
                        -isect.n.x,
                        -isect.n.y,
                        -isect.n.z
                        );
        }

        // aux_ray is centered at the intersection point
        // points towards the intersection surface normal
        Ray aux_ray = isect.SpawnRay(Vector3f(surface_normal));

        // Create aux camera
        std::unique_ptr<HemisphericCamera> aux_camera (
                    CreateHemisphericCamera(
                        PbrtOptions.iisptHemiSize,
                        PbrtOptions.iisptHemiSize,
                        dcamera->medium,
                        aux_ray.o,
                        Point3f(aux_ray.d.x, aux_ray.d.y, aux_ray.d.z),
                        pixel,
                        std::string("/tmp/null")
                        )
                    );


        // Run dintegrator render
        d_integrator->RenderView(scene, aux_camera.get());

        // --------------------------------------------------------------------
        //    * Use the __NnConnector__ to obtain the predicted intensity

        // Obtain intensity, normals, distance maps

        std::unique_ptr<IntensityFilm> aux_intensity =
                d_integrator->get_intensity_film(aux_camera.get());

        NormalFilm* aux_normals =
                d_integrator->get_normal_film();

        DistanceFilm* aux_distance =
                d_integrator->get_distance_film();

        // Use NN Connector

        int communicate_status = -1;
        std::shared_ptr<IntensityFilm> nn_film =
                nn_connector->communicate(
                    aux_intensity.get(),
                    aux_distance,
                    aux_normals,
                    iispt_integrator->get_normalization_intensity(),
                    iispt_integrator->get_normalization_distance(),
                    communicate_status
                    );

        if (communicate_status) {
            std::cerr << "NN communication issue" << std::endl;
            raise(SIGKILL);
        }

        // --------------------------------------------------------------------
        //    * Set the predicted intensity map on the __auxCamera__

        aux_camera->set_nn_film(nn_film);

        // --------------------------------------------------------------------
        //    * For all pixels within __radius__ and whose intersection and materials are compatible with the original intersection, evaluate __Li__ and update the filmTile

        // TODO move from a square area to a circular area

        // TODO add special case for very small radius

        int filter_start_x = std::max(
                    film_monitor->get_film_bounds().pMin.x,
                    (int) std::round(((float) x) - radius)
                    );

        int filter_end_x = std::min(
                    film_monitor->get_film_bounds().pMax.x,
                    (int) std::round(((float) x) + radius)
                    );

        int filter_start_y = std::max(
                    film_monitor->get_film_bounds().pMin.y,
                    (int) std::round(((float) y) - radius)
                    );

        int filter_end_y = std::min(
                    film_monitor->get_film_bounds().pMax.y,
                    (int) std::round(((float) y) + radius)
                    );

        // Temporary ----------------------------------------------------------
        // Evaluate for all pixels in the image
        Bounds2i bounds = film_monitor->get_film_bounds();
        std::chrono::steady_clock::time_point time_start =
                std::chrono::steady_clock::now();
        for (int fy = bounds.pMin.y; fy < bounds.pMax.y; fy++) {
            std::cerr << fy << std::endl;
            for (int fx = bounds.pMin.x; fx < bounds.pMax.x; fx++) {

                Point2i f_pixel = Point2i(fx, fy);

                sampler_next_pixel();
                CameraSample f_camera_sample =
                        sampler->GetCameraSample(f_pixel);

                RayDifferential f_r;
                main_camera->GenerateRayDifferential(
                    f_camera_sample,
                    &f_r
                    );
                f_r.ScaleDifferentials(1.0);

                SurfaceInteraction f_isect;
                Spectrum f_beta;
                Spectrum f_background;
                RayDifferential f_ray;

                // Find intersection point
                bool f_intersection_found = find_intersection(
                            f_r,
                            scene,
                            arena,
                            &f_isect,
                            &f_ray,
                            &f_beta,
                            &f_background
                            );

                if (!f_intersection_found) {
                    // No intersection found, record background
                    film_monitor->add_sample(
                                f_pixel,
                                f_background,
                                1.0
                                );
                    continue;
                } else if (f_intersection_found && f_beta.y() <= 0.0) {
                    // Intersection found but black pixel
                    // Nothing to do
                    continue;
                }

                // Valid intersection found

                // TODO check if intersection is within valid range
                // and that has similar material and normal facing

                // Compute scattering functions for surface interaction
                f_isect.ComputeScatteringFunctions(f_ray, arena);
                if (!isect.bsdf) {
                    // This should not be possible, because find_intersection()
                    // would have skipped the intersection
                    // so do nothing
                    continue;
                }

                // wo is vector towards viewer, from intersection
                Vector3f wo = f_isect.wo;
                Float wo_length = Dot(wo, wo);
                if (wo_length == 0) {
                    std::cerr << "iisptrenderrunner.cpp: Detected a 0 length wo" << std::endl;
                    raise(SIGKILL);
                    exit(1);
                }

                Spectrum L (0.0);

                // Sample one direct lighting
                const Distribution1D* distribution = lightDistribution->Lookup(f_isect.p);
                L += path_uniform_sample_one_light(
                            f_isect,
                            scene,
                            arena,
                            false,
                            distribution
                            );

                // Compute emitted light if ray hit an area light source
                L += f_isect.Le(wo);

                // Compute hemispheric contribution
                L += sample_hemisphere(
                            f_isect,
                            aux_camera.get()
                            );

                // Record sample
                film_monitor->add_sample(
                            f_pixel,
                            f_beta * L,
                            1.0);
            }
        }
        std::chrono::steady_clock::time_point time_end =
                std::chrono::steady_clock::now();
        auto elapsed_milliseconds =
                std::chrono::duration_cast<std::chrono::milliseconds>(
                    time_end - time_start
                    ).count();
        std::cerr << "iisptrenderrunner.cpp: Full frame evaluation loop took ["<< elapsed_milliseconds <<"] milliseconds\n";
        return;
        // end temporary ------------------------------------------------------

        for (int fy = filter_start_y; fy <= filter_end_y; fy++) {
            for (int fx = filter_start_x; fx <= filter_end_x; fx++) {

                // Compute filter weights
                double f_weight_scaling;
                double f_weight = compute_filter_weight(
                            x,
                            y,
                            fx,
                            fy,
                            radius,
                            &f_weight_scaling
                            );

                if (f_weight < 0.003) {
                    continue;
                }

                Point2i f_pixel = Point2i(fx, fy);

                sampler_next_pixel();
                CameraSample f_camera_sample =
                        sampler->GetCameraSample(f_pixel);

                RayDifferential f_r;
                main_camera->GenerateRayDifferential(
                    f_camera_sample,
                    &f_r
                    );
                f_r.ScaleDifferentials(1.0);

                SurfaceInteraction f_isect;
                Spectrum f_beta;
                Spectrum f_background;
                RayDifferential f_ray;

                // Find intersection point
                bool f_intersection_found = find_intersection(
                            f_r,
                            scene,
                            arena,
                            &f_isect,
                            &f_ray,
                            &f_beta,
                            &f_background
                            );

                if (!f_intersection_found) {
                    // No intersection found, record background
                    film_monitor->add_sample(
                                f_pixel,
                                f_background,
                                f_weight
                                );
                    continue;
                } else if (f_intersection_found && f_beta.y() <= 0.0) {
                    // Intersection found but black pixel
                    // Nothing to do
                    continue;
                }

                // Valid intersection found

                // TODO check if intersection is within valid range
                // and that has similar material and normal facing

                // Compute scattering functions for surface interaction
                f_isect.ComputeScatteringFunctions(f_ray, arena);
                if (!isect.bsdf) {
                    // This should not be possible, because find_intersection()
                    // would have skipped the intersection
                    // so do nothing
                    continue;
                }

                // wo is vector towards viewer, from intersection
                Vector3f wo = f_isect.wo;
                Float wo_length = Dot(wo, wo);
                if (wo_length == 0) {
                    std::cerr << "iisptrenderrunner.cpp: Detected a 0 length wo" << std::endl;
                    raise(SIGKILL);
                    exit(1);
                }

                Spectrum L (0.0);

                // Sample one direct lighting
                const Distribution1D* distribution = lightDistribution->Lookup(f_isect.p);
                L += path_uniform_sample_one_light(
                            f_isect,
                            scene,
                            arena,
                            false,
                            distribution
                            );

                // Compute emitted light if ray hit an area light source
                L += f_isect.Le(wo);

                // Compute hemispheric contribution
                L += sample_hemisphere(
                            f_isect,
                            aux_camera.get()                            );

                // Record sample
                film_monitor->add_sample(
                            f_pixel,
                            f_beta * L,
                            f_weight * f_weight_scaling);

            }
        }

        loop_count++;
        if (loop_count > 2000) {
            stop = true;
        }

    }
}

// ============================================================================

void IisptRenderRunner::generate_random_pixel(int *x, int *y)
{
    Bounds2i bounds = film_monitor->get_film_bounds();
    int xmin = bounds.pMin.x;
    int xmax = bounds.pMax.x;
    int ymin = bounds.pMin.y;
    int ymax = bounds.pMax.y;
    int width = xmax - xmin;
    int height = ymax - ymin;
    int randx = rng->uniform_uint32(width);
    int randy = rng->uniform_uint32(height);
    *x = randx + xmin;
    *y = randy + ymin;
}

// ============================================================================

// If intersection is found, a SurfaceInteraction is returned with a Beta value
// Otherwise, a background color is returned
// If beta_out is 0, then the current pixel always is black and doesn't need
// to be further evaluated
// <ray_out> returns the ray used to find the returned intersection
bool IisptRenderRunner::find_intersection(
        RayDifferential r,
        const Scene &scene,
        MemoryArena &arena,
        SurfaceInteraction* isect_out,
        RayDifferential* ray_out,
        Spectrum* beta_out,
        Spectrum* background_out
        )
{

    Spectrum beta (1.0);
    RayDifferential ray (r);

    for (int bounces = 0; bounces < 24; ++bounces) {

        // Compute intersection
        SurfaceInteraction isect;

        bool found_intersection = scene.Intersect(ray, &isect);

        // If no intersection, returned beta-scaled background radiance
        if (!found_intersection) {
            Spectrum L (0.0);
            for (const auto &light : scene.infiniteLights) {
                L += beta * light->Le(ray);
            }
            *background_out = L;
            return false;
        }

        // Compute scattering functions
        isect.ComputeScatteringFunctions(ray, arena, true);
        if (!isect.bsdf) {
            // If BSDF is null, skip this intersection
            ray = isect.SpawnRay(ray.d);
            continue;
        }

        // Skip light sampling

        // Sample BSDF for new path direction
        Vector3f wo = -ray.d;
        Vector3f wi;
        Float pdf;
        BxDFType flags;
        Spectrum f =
                isect.bsdf->Sample_f(
                    wo,
                    &wi,
                    sampler->Get2D(),
                    &pdf,
                    BSDF_ALL,
                    &flags
                    );
        // If BSDF is black or contribution is null,
        // return a 0 beta
        if (f.IsBlack() || pdf == 0.f) {
            *beta_out = Spectrum(0.0);
            return true;
        }
        // Check for specular bounce
        bool specular_bounce = (flags & BSDF_SPECULAR) != 0;
        if (!specular_bounce) {
            // The current bounce is not specular, so we stop here
            // and let IISPT proceed from the current point
            // No need to update Beta here
            *isect_out = isect;
            *ray_out = ray;
            *beta_out = beta;
            return true;
        }
        // Follow the specular bounce
        // Update beta value
        beta *= f * AbsDot(wi, isect.shading.n) / pdf;
        // Check for zero beta
        if (beta.y() < 0.f || isNaN(beta.y())) {
            *beta_out = Spectrum(0.0);
            return true;
        }
        // Spawn the new ray
        ray = isect.SpawnRay(wi);

        // Skip subsurface scattering

        // Skip RR termination

    }

    // Max depth reached, return 0 beta
    *beta_out = Spectrum(0.0);
    return true;
}

// ============================================================================
// Compute weights
// Gaussian filtering weight
double IisptRenderRunner::compute_filter_weight(
        int cx, // Centre sampling pixel
        int cy,
        int fx, // Current filter pixel
        int fy,
        float radius, // Filter radius,
        double* scaling_factor // Scaling factor to obtain a gaussian curve
                               // which has point X=0, Y=1
        )
{
    double sigma = radius / 3.0;

    // Compute distance
    double dx2 = (double) (cx - fx);
    dx2 = dx2 * dx2;
    double dy2 = (double) (cy - fy);
    dy2 = dy2 * dy2;
    double distance = std::sqrt(
                dx2 + dy2
                );

    // Compute gaussian weight
    double gaussian_weight = iispt::gauss(sigma, distance);
    *scaling_factor = 1.0 / iispt::gauss(sigma, 0.0);
    return gaussian_weight;
}

// ============================================================================

Spectrum IisptRenderRunner::path_uniform_sample_one_light(
        Interaction &it,
        const Scene &scene,
        MemoryArena &arena,
        bool handleMedia,
        const Distribution1D* lightDistrib
        )
{
    // Randomly choose a single light to sample
    int nLights = int(scene.lights.size());
    if (nLights == 0) {
        return Spectrum(0.0);
    }

    int lightNum;
    float lightPdf;
    if (lightDistrib) {
        lightNum = lightDistrib->SampleDiscrete(sampler->Get1D(), &lightPdf);
        if (lightPdf == 0) {
            return Spectrum(0.0);
        }
    } else {
        lightNum = std::min((int)(sampler->Get1D() * nLights), nLights - 1);
        lightPdf = Float(1) / nLights;
    }

    const std::shared_ptr<Light> &light = scene.lights[lightNum];
    Point2f uLight = sampler->Get2D();
    Point2f uScattering = sampler->Get2D();
    return estimate_direct_lighting(it, uScattering, *light, uLight,
                          scene, arena, handleMedia, false) / lightPdf;
}

// ============================================================================

Spectrum IisptRenderRunner::estimate_direct_lighting(
        Interaction &it,
        const Point2f &uScattering,
        const Light &light,
        const Point2f &uLight,
        const Scene &scene,
        MemoryArena &arena,
        bool handleMedia,
        bool specular
        )
{
    BxDFType bsdfFlags =
        specular ? BSDF_ALL : BxDFType(BSDF_ALL & ~BSDF_SPECULAR);
    Spectrum Ld(0.f);
    // Sample light source with multiple importance sampling
    Vector3f wi;
    Float lightPdf = 0, scatteringPdf = 0;
    VisibilityTester visibility;
    Spectrum Li = light.Sample_Li(it, uLight, &wi, &lightPdf, &visibility);
    if (lightPdf > 0 && !Li.IsBlack()) {
        // Compute BSDF or phase function's value for light sample
        Spectrum f;
        if (it.IsSurfaceInteraction()) {
            // Evaluate BSDF for light sampling strategy
            const SurfaceInteraction &isect = (const SurfaceInteraction &)it;
            f = isect.bsdf->f(isect.wo, wi, bsdfFlags) *
                AbsDot(wi, isect.shading.n);
            scatteringPdf = isect.bsdf->Pdf(isect.wo, wi, bsdfFlags);
        } else {
            // Evaluate phase function for light sampling strategy
            const MediumInteraction &mi = (const MediumInteraction &)it;
            Float p = mi.phase->p(mi.wo, wi);
            f = Spectrum(p);
            scatteringPdf = p;
        }
        if (!f.IsBlack()) {
            // Compute effect of visibility for light source sample
            if (handleMedia) {
                Li *= visibility.Tr(scene, *sampler);
            } else {
              if (!visibility.Unoccluded(scene)) {
                Li = Spectrum(0.f);
              }
            }

            // Add light's contribution to reflected radiance
            if (!Li.IsBlack()) {
                if (IsDeltaLight(light.flags)) {
                    Ld += f * Li / lightPdf;
                } else {
                    Float weight =
                        PowerHeuristic(1, lightPdf, 1, scatteringPdf);
                    Ld += f * Li * weight / lightPdf;
                }
            }
        }
    }

    // Sample BSDF with multiple importance sampling
    if (!IsDeltaLight(light.flags)) {
        Spectrum f;
        bool sampledSpecular = false;
        if (it.IsSurfaceInteraction()) {
            // Sample scattered direction for surface interactions
            BxDFType sampledType;
            const SurfaceInteraction &isect = (const SurfaceInteraction &)it;
            f = isect.bsdf->Sample_f(isect.wo, &wi, uScattering, &scatteringPdf,
                                     bsdfFlags, &sampledType);
            f *= AbsDot(wi, isect.shading.n);
            sampledSpecular = (sampledType & BSDF_SPECULAR) != 0;
        } else {
            // Sample scattered direction for medium interactions
            const MediumInteraction &mi = (const MediumInteraction &)it;
            Float p = mi.phase->Sample_p(mi.wo, &wi, uScattering);
            f = Spectrum(p);
            scatteringPdf = p;
        }
        if (!f.IsBlack() && scatteringPdf > 0) {
            // Account for light contributions along sampled direction _wi_
            Float weight = 1;
            if (!sampledSpecular) {
                lightPdf = light.Pdf_Li(it, wi);
                if (lightPdf == 0) {
                    return Ld;
                }
                weight = PowerHeuristic(1, scatteringPdf, 1, lightPdf);
            }

            // Find intersection and compute transmittance
            SurfaceInteraction lightIsect;
            Ray ray = it.SpawnRay(wi);
            Spectrum Tr(1.f);
            bool foundSurfaceInteraction =
                handleMedia ? scene.IntersectTr(ray, *sampler, &lightIsect, &Tr)
                            : scene.Intersect(ray, &lightIsect);

            // Add light contribution from material sampling
            Spectrum Li(0.f);
            if (foundSurfaceInteraction) {
                if (lightIsect.primitive->GetAreaLight() == &light) {
                    Li = lightIsect.Le(-wi);
                }
            } else {
                Li = light.Le(ray);
            }
            if (!Li.IsBlack()) {
                Ld += f * Li * Tr * weight / scatteringPdf;
            }
        }
    }
    return Ld;
}

// ============================================================================
// This method increments the sampler pixel count to make sure that we
// never use two pixel values more than once, increasing sampling diversity

void IisptRenderRunner::sampler_next_pixel()
{

    int x = sampler_pixel_counter.x;
    int y = sampler_pixel_counter.y;
    if (x == INT_MAX) {
        x = -1;
        y++;
    }
    x++;
    sampler_pixel_counter = Point2i(x, y);
    sampler->StartPixel(sampler_pixel_counter);

}

}
