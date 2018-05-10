#include "iisptrenderrunner.h"
#include "lightdistrib.h"

#include <chrono>
#include <csignal>

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
        int rx, // Random numbers between 0 and IISPT HEMI SIZE
        int ry,
        HemisphericCamera* auxCamera,
        IisptRng* rng
        ) {

    bool specular = false; // Default value

    BxDFType bsdfFlags =
        specular ? BSDF_ALL : BxDFType(BSDF_ALL & ~BSDF_SPECULAR);
    Spectrum Ld(0.f);

    // Sample light source with multiple importance sampling
    Vector3f wi;
    Float lightPdf = 1.0 / 6.28;
    Float BSDF_RATIO = 0.10;
    Float EM_RATIO = 0.5;
    Float scatteringPdf = 0;
    VisibilityTester visibility;

    // Sample_Li with custom code to sample from hemisphere instead -----------
    // Writes into wi the vector towards the light source. Derived from hem_x and hem_y
    // For the hemisphere, lightPdf would be a constant (probably 1/(2pi))
    // We don't need to have a visibility object

    // Get jacobian-adjusted sample, camera coordinates
    Spectrum Li = auxCamera->get_light_sample_nn(
                rx,
                ry,
                &wi
                );

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
                Float weight = PowerHeuristic(1, lightPdf, 1, scatteringPdf);
                Ld += EM_RATIO * f * Li * weight / lightPdf;
            }
        }
    }

    // Sample BSDF with multiple importance sampling
    {
        Spectrum f;
        bool sampledSpecular = false;
        if (it.IsSurfaceInteraction()) {
            // Sample scattered direction for surface interactions
            BxDFType sampledType;
            const SurfaceInteraction &isect = (const SurfaceInteraction &) it;
            Point2f uScattering (
                        rng->uniform_float(),
                        rng->uniform_float()
                        );
            f = isect.bsdf->Sample_f(
                        isect.wo,
                        &wi,
                        uScattering,
                        &scatteringPdf,
                        bsdfFlags,
                        &sampledType
                        );
            f *= AbsDot(wi, isect.shading.n);
            sampledSpecular = (sampledType & BSDF_SPECULAR) != 0;
        } else {
            // Sample scattered direction for medium interactions
            const MediumInteraction &mi = (const MediumInteraction &) it;
            Point2f uScattering (
                        rng->uniform_float(),
                        rng->uniform_float()
                        );
            Float p = mi.phase->Sample_p(mi.wo, &wi, uScattering);
            f = Spectrum(p);
            scatteringPdf = p;
        }

        if (!f.IsBlack() && scatteringPdf > 0) {
            // Account for light contributions along sampled direction _wi_
            Float weight = 1;
            if (!sampledSpecular) {
                weight = PowerHeuristic(1, scatteringPdf, 1, lightPdf);
            }

            // Compute Li
            Spectrum Li = auxCamera->getLightSampleNn(wi);
            if (!Li.IsBlack()) {
                Ld += BSDF_RATIO * f * Li * weight / scatteringPdf;
            }
        }
    }

    return Ld;

}

// ============================================================================
// Sample hemisphere with multiple cameras and weights
Spectrum IisptRenderRunner::sample_hemisphere(
        const Interaction &it,
        std::vector<float> &weights,
        std::vector<HemisphericCamera*> &cameras
        )
{
    Spectrum L(0.f);

    int samples_taken = 0;

    for (int i = 0; i < cameras.size(); i++) {
        HemisphericCamera* a_camera = cameras[i];
        if (a_camera != NULL) {
            a_camera->compute_cdfs();
        }
        float a_weight = weights[i];

        // Attempt HEMISPHERIC_IMPORTANCE_SAMPLES to sample this camera
        // The expected number of samples across all the cameras will be
        // HEMISPHERIC_IMPORTANCE_SAMPLES
        for (int j = 0; j < HEMISPHERIC_IMPORTANCE_SAMPLES; j++) {
            float rr = rng->uniform_float();
            if (rr < a_weight) {
                samples_taken++;
                if (a_camera != NULL) {
                    int rx = rng->uniform_uint32(PbrtOptions.iisptHemiSize);
                    int ry = rng->uniform_uint32(PbrtOptions.iisptHemiSize);
                    L += estimate_direct(it, rx, ry, a_camera, rng.get());
                }
            }
        }
    }

    if (samples_taken > 0) {
        return L / samples_taken;
    } else {
        return Spectrum(0.0);
    }
}

// ============================================================================
IisptRenderRunner::IisptRenderRunner(std::shared_ptr<IisptScheduleMonitor> schedule_monitor,
        std::shared_ptr<IisptFilmMonitor> film_monitor_indirect,
        std::shared_ptr<IisptFilmMonitor> film_monitor_direct,
        std::shared_ptr<const Camera> main_camera,
        std::shared_ptr<Camera> dcamera,
        std::shared_ptr<Sampler> sampler,
        int thread_no,
        Bounds2i pixel_bounds,
        std::shared_ptr<IisptNnConnector> nnConnector)
{
    this->schedule_monitor = schedule_monitor;

    this->film_monitor_indirect = film_monitor_indirect;

    this->film_monitor_direct = film_monitor_direct;

    this->dcamera = dcamera;

    this->pixel_bounds = pixel_bounds;

    this->nn_connector = std::move(nnConnector);

    this->rng = std::unique_ptr<IisptRng>(
                new IisptRng(thread_no)
                );

    this->sampler = std::unique_ptr<Sampler>(
                sampler->Clone(thread_no)
                );

    this->thread_no = thread_no;

    this->main_camera = main_camera;
}

// ============================================================================

void IisptRenderRunner::run(const Scene &scene)
{
    std::cerr << "iisptrenderrunner.cpp: Thread " << thread_no << " " << "iisptrenderrunner.cpp: New tiled renderer thread " << this->thread_no << std::endl;;

    // dintegrator
    std::shared_ptr<IISPTdIntegrator> d_integrator = CreateIISPTdIntegrator(this->dcamera);

    // Read number of passes environment variable
    char* num_passes_env = std::getenv("IISPT_INDIRECT_PASSES");
    int num_passes = 2;
    if (num_passes_env != NULL) {
        num_passes = std::stoi(std::string(num_passes_env));
    }

    d_integrator->Preprocess(scene);
    lightDistribution =
            CreateLightSampleDistribution(std::string("spatial"), scene);

    std::cerr << "iisptrenderrunner.cpp: Thread " << thread_no << " " << "iisptrenderrunner.cpp: start render loop\n";

    while (1) {

        // Obtain the current task
        IisptScheduleMonitorTask sm_task = schedule_monitor->next_task();

        // Check pass number for finish
        if (sm_task.pass > num_passes) {
            break;
        }

        std::cerr << "iisptrenderrunner.cpp: Thread " << thread_no << " " << "iisptrenderrunner.cpp PASS " << sm_task.pass << std::endl;

        MemoryArena arena;

        // sm_task end points are exclusive
        std::cerr << "iisptrenderrunner.cpp: Thread " << thread_no << " " << "Obtained new task: ["<< sm_task.x0 <<"]["<< sm_task.y0 <<"]-["<< sm_task.x1 <<"]["<< sm_task.y1 <<"] tilesize ["<< sm_task.tilesize <<"]\n";

        // Use a HashMap to store the hemi points
        std::unordered_map<
                IisptPoint2i,
                std::shared_ptr<HemisphericCamera>
                > hemi_points;

        // Check the iteration space of the tiles
        int tile_x = sm_task.x0;
        int tile_y = sm_task.y0;
        while (1) {
            // Process current tile
            std::cerr << "iisptrenderrunner.cpp: Thread " << thread_no << " " << "Hemi point ["<< tile_x <<"] ["<< tile_y <<"]\n";
            IisptPoint2i hemi_key;
            hemi_key.x = tile_x;
            hemi_key.y = tile_y;

            Point2i pixel (tile_x, tile_y);

            // Obtain camera ray and shoot into scene.

            sampler_next_pixel();

            CameraSample camera_sample =
                    sampler->GetCameraSample(pixel);

            RayDifferential r;
            main_camera->GenerateRayDifferential(
                        camera_sample,
                        &r
                        );
            r.ScaleDifferentials(1.0);

            // Find intersection

            SurfaceInteraction isect;
            Spectrum beta;
            Spectrum background;
            RayDifferential ray;
            Spectrum area_out;

            bool intersection_found = find_intersection(
                        r,
                        scene,
                        arena,
                        &isect,
                        &ray,
                        &beta,
                        &background,
                        &area_out
                        );

            if (!intersection_found || beta.y() <= 0.0) {

                // Set a black hemi
                hemi_points[hemi_key] = nullptr;

            } else {

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

                // Create 1spp sampler
                std::unique_ptr<Sampler> one_spp_sampler (
                            CreateSobolSampler(
                                Bounds2i(
                                    Point2i(0, 0),
                                    Point2i(PbrtOptions.iisptHemiSize,
                                            PbrtOptions.iisptHemiSize)
                                    ),
                                1
                                )
                            );

                // Create aux camera
                std::unique_ptr<HemisphericCamera> aux_camera (
                            CreateHemisphericCamera(
                                PbrtOptions.iisptHemiSize,
                                PbrtOptions.iisptHemiSize,
                                dcamera->medium,
                                aux_ray.o,
                                aux_ray.d,
                                std::string("/tmp/null")
                                )
                            );

                // Run dintegrator render
                d_integrator->RenderView(
                            scene,
                            aux_camera.get(),
                            one_spp_sampler.get()
                            );

                // Use NN Connector

                // Obtain intensity, normals, distance maps

                std::unique_ptr<IntensityFilm> aux_intensity =
                        d_integrator->get_intensity_film(aux_camera.get());

                NormalFilm* aux_normals =
                        d_integrator->get_normal_film();

                DistanceFilm* aux_distance =
                        d_integrator->get_distance_film();

                // Normalize the maps
                float intensityMean = normalizeMapsDownstream(
                            aux_intensity.get(),
                            aux_normals,
                            aux_distance
                            );

                int communicate_status = -1;
                std::shared_ptr<IntensityFilm> nn_film =
                        nn_connector->communicate(
                            aux_intensity.get(),
                            aux_distance,
                            aux_normals,
                            communicate_status
                            );

                // Upstream transforms on returned intensity
                transformMapsUpstream(nn_film.get(), intensityMean);

                if (communicate_status) {
                    std::cerr << "iisptrenderrunner.cpp: Thread " << thread_no << " " << "NN communication issue" << std::endl;
                    raise(SIGKILL);
                }

                aux_camera->set_nn_film(nn_film);

                hemi_points[hemi_key] = std::move(aux_camera);

            }

            // Advance to the next tile
            bool advance_tile_y = false;
            if (tile_x == sm_task.x1 - 1) {
                // This was the last tile of the row, go to next row
                tile_x = sm_task.x0;
                advance_tile_y = true;
            } else if (tile_x >= sm_task.x1) {
                std::cerr << "iisptrenderrunner.cpp: Thread " << thread_no << " " << "iisptrenderrunner: ERROR tile has gone past the end\n";
                std::raise(SIGKILL);
            } else {
                // Advance x only
                tile_x = std::min(
                            tile_x + sm_task.tilesize,
                            sm_task.x1 - 1
                            );
            }

            if (advance_tile_y) {
                if (tile_y == sm_task.y1 - 1) {
                    // This was the last row,
                    // complete the loop
                    break;
                } else {
                    // Advance to the next row
                    tile_y = std::min(
                                tile_y + sm_task.tilesize,
                                sm_task.y1 - 1
                                );
                }
            }
        }

        // Evaluate pixels in the task

        // A neighbour hemi point is one of the 4 points closest
        // to a film pixel

        // Neigh:
        //     0 S - top left
        //     1 R - top right
        //     2 B - bottom left
        //     3 E - bottom right

        // Collect vectors for new additions
        std::vector<Point2i> additions_pt;
        std::vector<Spectrum> additions_spectrum;
        std::vector<double> additions_weights;

        std::cerr << "iisptrenderrunner.cpp: Thread " << thread_no << " " << "iisptrenderrunner.cpp: Start hemi evaluation\n";

        for (int fy = sm_task.y0; fy < sm_task.y1; fy++) {
            for (int fx = sm_task.x0; fx < sm_task.x1; fx++) {

                Point2i f_pixel (fx, fy);

                Point2i neigh_s (
                            fx - (iispt::positiveModulo(fx - sm_task.x0, sm_task.tilesize)),
                            fy - (iispt::positiveModulo(fy - sm_task.y0, sm_task.tilesize))
                            );

                Point2i neigh_e (
                            std::min(
                                neigh_s.x + sm_task.tilesize,
                                sm_task.x1 - 1
                                ),
                            std::min(
                                neigh_s.y + sm_task.tilesize,
                                sm_task.y1 - 1
                                )
                            );

                Point2i neigh_r (
                            neigh_e.x,
                            neigh_s.y
                            );

                Point2i neigh_b (
                            neigh_s.x,
                            neigh_e.y
                            );

                std::vector<Point2i> neighbour_points (4);
                neighbour_points[0] = neigh_s;
                neighbour_points[1] = neigh_e;
                neighbour_points[2] = neigh_r;
                neighbour_points[3] = neigh_b;

                std::vector<HemisphericCamera*> hemi_sampling_cameras (4);

                auto hemi_point_get = [&](Point2i pt) {
                    IisptPoint2i pt_key;
                    pt_key.x = pt.x;
                    pt_key.y = pt.y;
                    if (hemi_points.count(pt_key) <= 0) {
                        std::cerr << "iisptrenderrunner.cpp: Thread " << thread_no << " " << "iisptrenderrunner.cpp: hemi_points does not have key ["<< pt.x <<"]["<< pt.y <<"]\n";
                        std::raise(SIGKILL);
                    }
                    std::shared_ptr<HemisphericCamera> a_cmr =
                            hemi_points.at(pt_key);
                    if (a_cmr == nullptr) {
                        return (HemisphericCamera*) NULL;
                    } else {
                        return a_cmr.get();
                    }
                };

                for (int i = 0; i < 4; i++) {
                    hemi_sampling_cameras[i] =
                            hemi_point_get(neighbour_points[i]);
                }

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
                Spectrum area_out;

                // Find intersection point
                bool f_intersection_found = find_intersection(
                            f_r,
                            scene,
                            arena,
                            &f_isect,
                            &f_ray,
                            &f_beta,
                            &f_background,
                            &area_out
                            );

                if (!f_intersection_found) {
                    // No intersection found
                    // Do nothing.
                    // Background is recorded in the direct illumination pass
                    continue;
                } else if (f_intersection_found && f_beta.y() <= 0.0) {
                    // Intersection found but black pixel
                    // Nothing to do
                    continue;
                }

                // Valid intersection found

                // Compute weights and probabilities for neighbours
                std::vector<float> hemi_sampling_weights (4);
                compute_fpixel_weights(
                            neighbour_points,
                            hemi_sampling_cameras,
                            f_pixel,
                            f_isect,
                            sm_task.tilesize,
                            f_ray,
                            hemi_sampling_weights // << output
                            );

                // Compute scattering functions for surface interaction
                f_isect.ComputeScatteringFunctions(f_ray, arena);
                if (!f_isect.bsdf) {
                    // This should not be possible, because find_intersection()
                    // would have skipped the intersection
                    // so do nothing
                    continue;
                }

                // wo is vector towards viewer, from intersection
                Vector3f wo = f_isect.wo;
                Float wo_length = Dot(wo, wo);
                if (wo_length == 0) {
                    std::cerr << "iisptrenderrunner.cpp: Thread " << thread_no << " " << "iisptrenderrunner.cpp: Detected a 0 length wo" << std::endl;
                    raise(SIGKILL);
                    exit(1);
                }

                Spectrum L (0.0);

                // Compute hemispheric contribution
                L += sample_hemisphere(
                            f_isect,
                            hemi_sampling_weights,
                            hemi_sampling_cameras
                            );

                // Record sample
                additions_pt.push_back(f_pixel);
                additions_spectrum.push_back(f_beta * L);
                additions_weights.push_back(1.0);
            }
        }

        std::cerr << "iisptrenderrunner.cpp: Thread " << thread_no << " " << "iisptrenderrunner.cpp: End hemi evaluation\n";

        film_monitor_indirect->add_n_samples(
                    additions_pt,
                    additions_spectrum,
                    additions_weights
                    );

    }

}

// ============================================================================

// Render direct illumination components
void IisptRenderRunner::run_direct(const Scene &scene)
{
    std::cerr << "iisptrenderrunner.cpp: Thread " << thread_no << " " << "iisptrenderrunner.cpp: starting direct illumination pass\n";

    std::unique_ptr<DirectLightingIntegrator> directIntegrator (
                new DirectLightingIntegrator(
                    LightStrategy::UniformSampleAll,
                    5,
                    main_camera,
                    sampler->Clone(0),
                    film_monitor_indirect->get_film_bounds()
                    )
                );

    directIntegrator->Render(scene, false);

    std::unique_ptr<IntensityFilm> directFilm = main_camera->film->to_intensity_film();

    std::cerr << "iisptrenderrunner.cpp: Thread " << thread_no << " " << "iisptrenderrunner.cpp: Completed direct pass loop\n";

    film_monitor_direct->addFromIntensityFilm(directFilm.get());

    std::cerr << "iisptrenderrunner.cpp: Thread " << thread_no << " " << "iisptrenderrunner.cpp: Completed direct pass add_n_samples\n";
}

// ============================================================================

void IisptRenderRunner::generate_random_pixel(int *x, int *y)
{
    Bounds2i bounds = film_monitor_indirect->get_film_bounds();
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
        Spectrum* background_out,
        Spectrum* emitted_out
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

        // Possibly add emitted light at intersection
        // It's always a specular bounce
        if (found_intersection) {
            Spectrum emittedOutUpdated = *emitted_out + (beta * isect.Le(-ray.d));
            *emitted_out = emittedOutUpdated;
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

// ============================================================================
// Compute weights for individual pixels

void IisptRenderRunner::compute_fpixel_weights(
        std::vector<Point2i> &neighbour_points,
        std::vector<HemisphericCamera*> &hemi_sampling_cameras,
        Point2i f_pixel,
        SurfaceInteraction &f_isect,
        int tilesize,
        RayDifferential &f_ray,
        std::vector<float> &out_probabilities
        )
{

    int len = neighbour_points.size();

    // Invert surface normal if pointing inwards
    Normal3f surface_normal = f_isect.n;
    Vector3f sf_norm_vec = Vector3f(f_isect.n.x, f_isect.n.y, f_isect.n.z);
    Vector3f ray_vec = Vector3f(f_ray.d.x, f_ray.d.y, f_ray.d.z);
    if (Dot(sf_norm_vec, ray_vec) > 0.0) {
        surface_normal = Normal3f(
                    -f_isect.n.x,
                    -f_isect.n.y,
                    -f_isect.n.z
                    );
    }
    // Aux ray
    Ray aux_ray = f_isect.SpawnRay(Vector3f(surface_normal));

    // Weighting distances for positions
    std::vector<float> wdpos (len);
    for (int i = 0; i < len; i++) {
        wdpos[i] = iispt::weighting_distance_positions(
                    f_pixel,
                    neighbour_points[i],
                    tilesize
                    );
    }

    // Weighting distance for normals
    std::vector<float> wdnor (len);
    for (int i = 0; i < len; i++) {
        if (!hemi_sampling_cameras[i]) {
            wdnor[i] = 0.0f;
        } else {
            wdnor[i] = iispt::weighting_distance_normals(
                        aux_ray.d,
                        hemi_sampling_cameras[i]->get_look_direction()
                        );
        }
    }

    // Weighting overall distance
    std::vector<float> wod (len);
    for (int i = 0; i < len; i++) {
        wod[i] = wdpos[i] * wdnor[i] + wdpos[i];
    }

    // Final weights
    for (int i = 0; i < len; i++) {
        out_probabilities[i] = std::max(0.0, 1.0 - wod[i]) + 0.001;
    }

    // Weights to probabilities
    iispt::weights_to_probabilities(out_probabilities);
}

void IisptRenderRunner::compute_fpixel_weights_3d(
        std::vector<Point2i> &neighbour_points,
        std::vector<HemisphericCamera*> &hemi_sampling_cameras,
        Point2i f_pixel,
        SurfaceInteraction &f_isect,
        int tilesize,
        RayDifferential &f_ray,
        std::vector<float> &out_probabilities
        )
{
    int len = neighbour_points.size();

    // Invert surface normal if pointing inwards
    Normal3f surface_normal = f_isect.n;
    Vector3f sf_norm_vec = Vector3f(f_isect.n.x, f_isect.n.y, f_isect.n.z);
    Vector3f ray_vec = Vector3f(f_ray.d.x, f_ray.d.y, f_ray.d.z);
    if (Dot(sf_norm_vec, ray_vec) > 0.0) {
        surface_normal = Normal3f(
                    -f_isect.n.x,
                    -f_isect.n.y,
                    -f_isect.n.z
                    );
    }
    // Aux ray
    Ray aux_ray = f_isect.SpawnRay(Vector3f(surface_normal));

    // Compute weights for 3D positions using bilinear interpolation

    // Left side interpolation
    Point2i leftSideFPixel (neighbour_points[0].x, f_pixel.y);
    Point2i interpolationLeftPoint;
    float interpolationS = iispt::linearRatioDistance(
                leftSideFPixel,
                neighbour_points[0],
                neighbour_points[2],
                interpolationLeftPoint
                );
    float interpolationB = 1.0f - interpolationS;

    // Right side interpolation
    Point2i rightSideFPixel (neighbour_points[1].x, f_pixel.y);
    Point2i interpolationRightPoint;
    float interpolationR = iispt::linearRatioDistance(
                rightSideFPixel,
                neighbour_points[1],
                neighbour_points[3],
                interpolationRightPoint
                );
    float interpolationE = 1.0f - interpolationR;

    // Horizontal interpolation
    Point2i interpolationCentral;
    float interpolationHL = iispt::linearRatioDistance(
                f_pixel,
                interpolationLeftPoint,
                interpolationRightPoint,
                interpolationCentral
                );
    float interpolationHR = 1.0f - interpolationHL;

    // Compute final interpolation values
    std::vector<float> positionWeights (len);
    positionWeights[0] = interpolationHL * interpolationS;
    positionWeights[1] = interpolationHR * interpolationR;
    positionWeights[2] = interpolationHL * interpolationB;
    positionWeights[3] = interpolationHR * interpolationE;

    // Compute weights for 3D normals
    std::vector<float> normalWeights (len);
    for (int i = 0; i < len; i++) {
        normalWeights[i] = iispt::weighting_normals(aux_ray.d, hemi_sampling_cameras[i]->get_look_direction());
    }

    // Final weights
    for (int i = 0; i < len; i++) {
        out_probabilities[i] = positionWeights[i] * normalWeights[i] + 0.0001;
    }

    // Weights to probabilities
    iispt::weights_to_probabilities(out_probabilities);

}

// ============================================================================
void IisptRenderRunner::compute_fpixel_weights_simple(
        std::vector<Point2i> &neighbour_points,
        std::vector<HemisphericCamera*> &hemi_sampling_cameras,
        Point2i f_pixel,
        SurfaceInteraction &f_isect,
        int tilesize,
        RayDifferential &f_ray,
        std::vector<float> &out_probabilities
        )
{
    int len = neighbour_points.size();

    float total_distance = 0.0;
    std::vector<float> distances (len);
    for (int i = 0; i < len; i++) {
        float a_distance = iispt::points_distance(
                    f_pixel, neighbour_points[i]
                    );
        total_distance += a_distance;
        distances[i] = a_distance;
    }

    // Divide by total distance
    if (total_distance > 0.0) {
        for (int i = 0; i < len; i++) {
            distances[i] = distances[i] / total_distance;
        }
    }

    // Invert
    for (int i = 0; i < len; i++) {
        out_probabilities[i] = 1.0 - distances[i];
    }

    // To probabilities
    iispt::weights_to_probabilities(out_probabilities);
}

// ============================================================================
// <return> the mean value of the Intensity Film
float IisptRenderRunner::normalizeMapsDownstream(
        IntensityFilm* intensity,
        NormalFilm* normals,
        DistanceFilm* distance
        )
{
    // Intensity --------------------------------------------------------------

    // Compute mean of intensity
    std::shared_ptr<ImageFilm> intensityFilm = intensity->get_image_film();
    float intensityMean = intensityFilm->computeMean();

    // Divide by 10*mean
    float multRatio = intensityMean == 0.0 ?
                0.0 :
                (1.0 / (10.0 * intensityMean));
    intensityFilm->multiply(multRatio);

    // Log
    intensityFilm->positiveLog();

    // Subtract 0.1
    intensityFilm->add(-0.1);

    // Normals ----------------------------------------------------------------

    normals->get_image_film()->normalize(-1.0, 1.0);

    // Distance ---------------------------------------------------------------

    std::shared_ptr<ImageFilm> distanceFilm = distance->get_image_film();

    float zMean = distanceFilm->computeMean();

    // Add 1
    distanceFilm->add(1.0);

    // Divide by 10 * (mean + 1)
    float distanceDiv = 10.0 * (zMean + 1.0);
    if (distanceDiv == 0) {
        distanceDiv = 1.0;
    }
    distanceFilm->multiply(1.0 / distanceDiv);

    // Log
    distanceFilm->positiveLog();

    // Subtract 0.1
    distanceFilm->add(-0.1);

    return intensityMean;
}

// ============================================================================
void IisptRenderRunner::transformMapsUpstream(
        IntensityFilm* intensity,
        float targetMean
        )
{
    std::shared_ptr<ImageFilm> intensityFilm = intensity->get_image_film();

    // Log inverse
    intensityFilm->positiveLogInverse();

    // Compute actual mean
    float actualMean = intensityFilm->computeMean();

    float multiplier;
    if (actualMean > 0.0) {
        multiplier = targetMean / actualMean;
    } else {
        multiplier = 1.0;
    }

    // Multiply by 10*mean
    intensityFilm->multiply(multiplier);
}

// ============================================================================
float IisptRenderRunner::tileToTileMinimumDistance(
        std::vector<HemisphericCamera*> &hemiSamplingCameras
        )
{
    float minDistance = -1.0;
    int len = hemiSamplingCameras.size();
    for (int i = 0; i < len; i++) {
        for (int j = i + 1; j < len; j++) {
            float aDistance = Distance(
                        hemiSamplingCameras[i]->getOriginPosition(),
                        hemiSamplingCameras[j]->getOriginPosition()
                        );
            if (minDistance < 0.0 || aDistance < minDistance) {
                minDistance = aDistance;
            }
        }
    }
    return minDistance;
}

}
