#!/usr/bin/env python3
# =============================================================================
# Path and imports
import os
toolsDir = os.path.abspath(os.path.dirname(__file__))
rootDir = os.path.dirname(toolsDir)
mlDir = os.path.join(rootDir, "ml")
import sys
sys.path.append(mlDir)

import pfm

# =============================================================================
argv = sys.argv[1:]
if len(argv) < 1:
    print("Usage: ./pfm_to_png.py <input.pfm>")
    sys.exit(0)

def processOne(inputPath):
    print("Processing {}".format(inputPath))
    inputDir = os.path.dirname(inputPath)
    inputFilename = os.path.basename(inputPath)
    stem, ext = os.path.splitext(inputFilename)
    if ext != ".pfm":
        print("Expected a .pfm file as input")
        sys.exit(0)
    outFilename = "{}.png".format(stem)
    outFilepath = os.path.join(inputDir, outFilename)

    # Load the PFM
    img = pfm.load(inputPath)
    autoExposure = img.computeAutoexposure()
    img.save_png(outFilepath, autoExposure, 2.2, reverse=True)

for anArg in argv:
    processOne(anArg)