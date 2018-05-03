# This little script deletes all normal maps from a training directory
# by matching for files starting with n_ and with .pfm extension

import os

TARGETDIR = "/home/gj/git/pbrt-v3-IISPT-dataset-indirect"

for root, subdirs, files in os.walk(TARGETDIR):

    for fn in files:

        fp = os.path.join(root, fn)

        stem, ext = os.path.splitext(fn)

        if (stem.startswith("n_")) and (ext == ".pfm"):

            print("DELETE {}".format(fn))
            os.remove(fp)