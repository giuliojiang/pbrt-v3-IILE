pbrt, Version 3 - Intelligent Indirect Lighting Estimation
===============

# Quickstart

Quickstart and installation info: https://github.com/giuliojiang/pbrt-v3-IILE/wiki

# Intro

This repository holds the source code to the version of pbrt that is
described in the third edition of *Physically Based Rendering: From
Theory to Implementation*, by [Matt Pharr](http://pharr.org/matt), [Wenzel
Jakob](http://www.mitsuba-renderer.org/~wenzel/), and Greg Humphreys.  As
before, the code is available under the BSD license.

The [pbrt website](http://pbrt.org) has general information about
both the *Physically Based Rendering* book as well as many other resources
for pbrt.

This version has been modified to implement IILE.

# IILE

Intelligent Indirect Light Estimation uses machine learning to obtain high-quality
radiance maps of indirect illumination. This integrator accelerates
rendering of scenes with high amounts of global illumination.

Example scenes
--------------

Over 8GB of example scenes are available for download. (Many are new and
weren't available with previous versions of pbrt.)  See the [pbrt-v3 scenes
page](http://pbrt.org/scenes-v3.html) on the pbrt website for information
about how to download them.

After downloading them, see the `README.md.html` file in the scene
distribution for more information about the scenes and preview images.

Additional resources
--------------------

* There is a [pbrt Google
  Groups](https://groups.google.com/forum/#!forum/pbrt) mailing list that can
  be a helpful resource.
* Please see the [User's Guide](http://pbrt.org/users-guide.html) for more
  information about how to check out and build the system as well as various
  additional information about working with pbrt.
* Should you find a bug in pbrt, please report it in the [bug
  tracker](https://github.com/mmp/pbrt-v3/issues).
* Please report any errors you find in the *Physically Based Rendering*
  book to authors@pbrt.org.

Note: we tend to let bug reports and book errata emails pile up for a few
months for processing them in batches. Don't think we don't appreciate
them. :-)

Building pbrt
-------------

A detailed guide for downloading and building PBRTv3-OSR from source
is here: https://osr.jstudios.ovh/CompileFromSource

While the original PBRTv3 supports Linux, OSX and Windows, PBRTv3-OSR has only
been developed for Linux.

To check out pbrt together with all dependencies, be sure to use the
`--recursive` flag when cloning the repository, i.e.
```bash
$ git clone --recursive https://github.com/giuliojiang/pbrt-v3-IILE/
```
If you accidentally already cloned pbrt without this flag (or to update an
pbrt source tree after a new submodule has been added, run the following
command to also fetch the dependencies:
```bash
$ git submodule update --init --recursive
```

### Debug and Release Builds ###

By default, the build files that are created that will compile an optimized
release build of pbrt. These builds give the highest performance when
rendering, but many runtime checks are disabled in these builds and
optimized builds are generally difficult to trace in a debugger.

To build a debug version of pbrt, set the `CMAKE_BUILD_TYPE` flag to
`Debug` when you run cmake to create build files to make a debug build. For
example, when running cmake from the command line, provide it with the
argument `-DCMAKE_BUILD_TYPE=Debug`. Then build pbrt using the resulting
build files. (You may want to keep two build directories, one for release
builds and one for debug builds, so that you don't need to switch back and
forth.)

Debug versions of the system run much more slowly than release
builds. Therefore, in order to avoid surprisingly slow renders when
debugging support isn't desired, debug versions of pbrt print a banner
message indicating that they were built for debugging at startup time.

### Build Configurations ###

There are two configuration settings that must be set at compile time. The
first controls whether pbrt uses 32-bit or 64-bit values for floating-point
computation, and the second controls whether tristimulus RGB values or
sampled spectral values are used for rendering.  (Both of these aren't
amenable to being chosen at runtime, but must be determined at compile time
for efficiency).

To change them from their defaults (respectively, 32-bit
and RGB.), edit the file `src/core/pbrt.h`.

To select 64-bit floating point values, remove the comment symbol before
the line:
```
//#define PBRT_FLOAT_AS_DOUBLE
```
and recompile the system.

To select full-spectral rendering, comment out the first of these two
typedefs and remove the comment from the second one:
```
typedef RGBSpectrum Spectrum;
// typedef SampledSpectrum Spectrum;
```
Again, don't forget to recompile after making this change.

# PBRT-IILE options

The use of `bin/pbrt` as launcher is recommended.

## Command line options

```
--reference=<nTiles>
```

Disables normal rendering, and enables rendering of reference hemispheric images for training data. Note: `iispt` integrator needs to be selected for this to be effective.

`<nTiles>` specifies the number of hemispheric reference images rendered per dimension.

The output is saved into the current working directory, in subfolder `reference/`.

```
--reference_samples=<nsamples>
```

Sets the path tracing samples to be used in reference mode.

## .pbrt file

To enable the IILE integrator, use `iispt` as integrator. For example

```
Sampler "sobol" "integer pixelsamples" 1
Integrator "iispt"
```

## Additional info

[Additional info and setup, including environment variables](Doc.md)
