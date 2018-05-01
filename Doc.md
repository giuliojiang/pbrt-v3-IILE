# ml/main_stdio_net.py

Requires to run python with `-u` flag to turn on binary stdio.

Expected stdin format:

* Intensity raster: 32x32x3 = 3072 float (each 4 bytes)
* Distance raster: 32x32x1 = 1024 float (each 4 bytes)
* Normals raster: 32x32x3 = 3072 float (each 4 bytes)
* Intensity normalization value: 1 float
* Distance normalization value: 1 float

Expected stdout format:

* Intensity raster: 32x32x3 = 3072 float (each 4 bytes)
* Magic characters sequence: 'x' '\n'

## Performance

```
Full time from C++: 51ms/iteration
Full time from C++, optimized writes: 48ms/iteration
Full time from C++, optimized read and writes: 47ms/iteration
NN evaluation time: 27ms/iteration
NN evaluation from/to random numpy arrays: 27ms/iteration
NN evaluation with all transforms: 34ms/iteration
```

# Saved images and PBRT internal image representation

In PBRT, images coordiantes X and Y:

* X from left to right
* Y from bottom to top

But the saved images follow

* Y from top to bottom

In the datasets:

* d - uses PBRT exporter
* n - uses custom exporter, Y is reversed
* z - uses custom exporter, Y is reversed
* p - uses PBRT exporter, Y is reversed

The IntensityFilm object handles the Y direction in the same way as PBRT, maintaining consistency with the training dataset. Therefore once an IntensityFilm object is obtained, there is no need to handle manual transformations. Normals and Distance keep their inverted axis, the neural network handles the axes automatically.

# Environment Variables

`IISPT_STDIO_NET_PY_PATH` Location of `main_stdio_net.py` file which contains the python program to evaluate the neural network. Used by PBRT to start the child process. The environment variable is set up by the pbrt launcher.

`IISPT_SCHEDULE_RADIUS_START` Initial radius.

`IISPT_SCHEDULE_RADIUS_RATIO` Radius update multiplier.

`IISPT_SCHEDULE_INTERVAL` Radius interval samples.

`IISPT_DIRECT_SAMPLES` Number of pixel samples in the direct illumination pass.

`IISPT_INDIRECT_PASSES` Number of IISPT indirect passes

`IISPT_RNG_SEED` Initial RNG seed.

# IISPT Render Algorithm

## Classes

### IisptRenderRunner

One render thread. It includes the main loop logic.

Requires shared objects:

* IISPTIntegrator
* IisptScheduleMonitor
* IisptFilmMonitor (includes sample density information)

It creates its own instance of:

* IISPTdIntegrator
* IisptNnConnector (requires `dcamera` and `scene`)
* RNG

The render loop works as follows

* Obtain current __radius__ from the __ScheduleMonitor__. The ScheduleMonitor updates its internal count automatically
* Use the __RNG__ to generate 2 random pixel samples. Look up the density of the samples and select the one that has lower density
* Obtain camera ray and shoot into scene. If no __intersection__ is found, evaluate infinite lights
* Create __auxCamera__ and use the __dIntegrator__ to render a view
* Use the __NnConnector__ to obtain the predicted intensity
* Set the predicted intensity map on the __auxCamera__
* Create a __filmTile__ in the radius section
* For all pixels within __radius__ and whose intersection and materials are compatible with the original intersection, evaluate __Li__ and update the filmTile
* Send the filmTile to the __filmMonitor__

### IisptScheduleMonitor

Maintains the schedule of influence radius and radius update interval.

The radius schedule uses 2 parameters:

* Initial radius. Defaults to 50, overridden by `IISPT_SCHEDULE_RADIUS_START`
* Update multiplier. Defaults to 0.90, overridden by `IISPT_SCHEDULE_RADIUS_RATIO`

When radius is <= 1, only the original pixel is affected.

The radius update interval is the number of IISPT samples generated after the radius changes. A sample is considered to be generated at each call to __get_current_radius()__.

Defaults to 500, overridden by `IISPT_SCHEDULE_INTERVAL`.

### IisptFilmMonitor

Represents the full rendering film used by IISPT.

All the coordinates in the public API are absolute x and y coordinates, and are converted to internal film indexes automatically.

Holds a 2D array of __IisptPixel__.

__TODO__ This replaces the old IisptFilmMonitor class

Public methods:

* constructor(Bounds2i)
* add_sample(int x, int y, Spectrum s)
* get_density(int x, int y)

### IisptPixel

An IisptPixel has:

* x, y, z color coordinates
* sample_count number of samples obtained at the current location

# Iispt Render Algorithm 2

The new render algorithm uses a regular grid of hemispheric samples, and interpolates between them. The rendering frame is subdivided into smaller rectangular chunks, and each pass will first obtain all the hemispheric samples, and then evaluate all the relevant pixels.

# Training generation

## Multiprocessing control

There are some simple flags that can be used to make it easier to control multiprocessing in reference generation mode.

`IISPT_REFERENCE_CONTROL_MOD` defaults to 1

`IISPT_REFERENCE_CONTROL_MATCH` defaults to 0

The pixel index is modded by the MOD value, and the process will only render the reference pixel if the match value equals.

With the default values, every pixel is rendered.

# NN training

## 01

* per scene normalization
* batch normalization ON
* rprop LR=0.0001

## 02

* per scene normalization
* batch normalization ON
* rprop LR=0.00005

## 03

* mean + standard deviation normalization
* batch normalization ON
* rprop LR=0.00003

## 06

* per frame: log, normalization into [0-1], gamma
* backwards: gamma-1, normalization-1 with saved value, log-1
* comparison level: lowest (gamma corrected level)

Downstream Full (left): log, normalize positive, gamma

Downstream Half (right): Divide by mean, Log, Log

Upstream: InvLog, InvLog, Multiply by mean

Distance Downstream: Add 1, Sqrt, Normalize positive, Gamma


# Tiling and interpolation

## New weight

Define the new weight based on closeness in world-coordinates and on normals affinity.

D is the overall distance
P is the normalized position distance
N is the normalized normals distance

```
D = P * N + P
```

When Position is at closest, D is 0.

When Position is at farthest, D is maximal.

```
Weight = max(0, 1-D) + eps
```

Makes sure the weight is positive

When D is 0, weight is 1 + eps

When D is 1, weight is 0 + eps

When D is 1.5, weight is 0 + eps

To compute the normalized position distance:

```
P(a, b) = dist(a, b) / tileDistance
```

To compute a normalized normals distance:

```
N(a, b) = 
    dt = Dot(a, b)
    if dt < 0:
        return 1
    else:
        return 1 - dt
```

When dot product is 1, distance is 0

When dot product is negative, distance is maximal