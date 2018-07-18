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

This version has been modified to implement One Shot Radiance.

Example scenes
--------------

Over 8GB of example scenes are available for download. (Many are new and
weren't available with previous versions of pbrt.)  See the [pbrt-v3 scenes
page](http://pbrt.org/scenes-v3.html) on the pbrt website for information
about how to download them.

After downloading them, see the `README.md.html` file in the scene
distribution for more information about the scenes and preview images.

One Shot Radiance specific example scenes will be coming soon.

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

# PBRT-IILE options

The use of `bin/pbrt` as launcher is recommended.

Move usage information here: https://osr.jstudios.ovh/UsageInfo

## Additional info (dev)

[Additional info and setup, including environment variables](Doc.md)
