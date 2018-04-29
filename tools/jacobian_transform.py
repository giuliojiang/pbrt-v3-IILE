import os

rootdir = os.path.abspath(os.path.join(__file__, "..", ".."))

mldir = os.path.join(rootdir, "ml")

import sys
sys.path.append(mldir)

import pfm

argv = sys.argv[1:]

argv0 = argv[0]
argv1 = argv[1]

img = pfm.load(argv0)

img.jacobian_transform()
img.save_png(argv1, 0.0, 1.8)