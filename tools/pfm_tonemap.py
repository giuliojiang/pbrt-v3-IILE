#!/usr/bin/env python3

'''
PFM tonemapping utility.
If an exposure value is provided, it will be used.
If none is provided, autoexposure is used.
'''

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
if not ((len(argv) == 1) or (len(argv) == 2)):
    print("Usage: ./pfm_to_png.py <input.pfm> [exposure]")
    sys.exit(0)

inputPath = os.path.abspath(argv[0])
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

# Autoexposure or manual exposure
if len(argv) == 2:
    exposure = float(argv[1])
else:
    exposure = img.computeAutoexposure()

img.save_png(outFilepath, exposure, 2.2, reverse=True)
