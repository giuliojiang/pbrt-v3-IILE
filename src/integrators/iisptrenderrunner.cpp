#include "iisptrenderrunner.h"

namespace pbrt {

// ============================================================================
IisptRenderRunner::IisptRenderRunner(
        std::shared_ptr<IISPTIntegrator> iispt_integrator,
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

    this->d_integrator = std::unique_ptr(
                CreateIISPTdIntegrator(camera)
                );

    this->nn_connector = std::unique_ptr(
                new IisptNnConnector()
                );

    // TODO remove fixed seed
    this->rng = std::unique_ptr(
                new RNG(thread_no)
                );

    this->sampler = std::shared_ptr<Sampler>(
                sampler->Clone(thread_no)
                );

    this->dcamera = dcamera;

    this->thread_no = thread_no;

    this->pixel_bounds = pixel_bounds;

    this->main_camera = main_camera;
}

// ============================================================================
IisptRenderRunner::run()
{
    while (1) {

        // --------------------------------------------------------------------
        //    * Obtain current __radius__ from the __ScheduleMonitor__. The ScheduleMonitor updates its internal count automatically
        float radius = schedule_monitor->get_current_radius();

        // --------------------------------------------------------------------
        //    * Use the __RNG__ to generate 2 random pixel samples. Look up the density of the samples and select the one that has lower density
        int pix1x;
        int pix1y;
        generate_random_pixel(&pix1x, &pix1y);

        int pix2x;
        int pix2y;
        generate_random_pixel(&pix2x, &pix2y);

        int pix1d = film_monitor->get_pixel_sampling_density(pix1x, pix1y);
        int pix2d = film_monitor->get_pixel_sampling_density(pix2x, pix2y);

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
        //    * Create a __filmTile__ in the radius section
        std::shared_ptr<IisptFilmTile> film_tile =
                film_monitor->create_film_tile(
                    x,
                    y,
                    radius
                    );

        // --------------------------------------------------------------------
        //    * Obtain camera ray and shoot into scene. If no __intersection__ is found, evaluate infinite lights

        sampler->StartPixel(pixel);
        if (!InsideExclusive(pixel, pixel_bounds)) {
            continue;
        }

        CameraSample camera_sample =
                sampler->GetCameraSample(pixel);

        RayDifferential ray;
        Float ray_weight =
                main_camera->GenerateRayDifferential(
                    camera_sample,
                    &ray
                    );
        ray.ScaleDifferentials(1.0); // Not scaling based on samples per
                                     // pixel here

        // TODO the PBRT film is additive because it assumes that the
        // number of samples per pixel is already known.
        // We need to implement a custom film data structure that is able
        // to work with arbitrary number of samples


        // --------------------------------------------------------------------
        //    * Create __auxCamera__ and use the __dIntegrator__ to render a view

        // --------------------------------------------------------------------
        //    * Use the __NnConnector__ to obtain the predicted intensity

        // --------------------------------------------------------------------
        //    * Set the predicted intensity map on the __auxCamera__

        // --------------------------------------------------------------------
        //    * For all pixels within __radius__ and whose intersection and materials are compatible with the original intersection, evaluate __Li__ and update the filmTile

        // --------------------------------------------------------------------
        //    * Send the filmTile to the __filmMonitor__

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
    int randx = rng->UniformUInt32(width);
    int randy = rng->UniformUInt32(height);
    *x = randx + xmin;
    *y = randy + ymin;
}

}