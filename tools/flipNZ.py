# This little script finds all N and Z files in the
# target directory and flips them on the Y axis

import os

rootdir = os.path.abspath(os.path.join(__file__, "..", ".."))
mldir = os.path.join(rootdir, "ml")

import sys
sys.path.append(mldir)

import pfm

TARGETDIR = "/home/gj/git/pbrt-v3-IISPT-dataset-indirect"

def process(fp):
    img = pfm.load(fp)
    img.flipY()
    img.save_pfm(fp)

for root, subdirs, files in os.walk(TARGETDIR):

    for fn in files:

        fp = os.path.join(root, fn)

        stem, ext = os.path.splitext(fn)

        if  (ext == ".pfm") and ((stem.startswith("n_")) or (stem.startswith("z_"))):

            print("PROCESSING {}".format(fn))
            process(fp)