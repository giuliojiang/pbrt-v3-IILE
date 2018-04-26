import os

rootdir = os.path.abspath(os.path.join(__file__, "..", ".."))

mldir = os.path.join(rootdir, "ml")

import sys
sys.path.append(mldir)

import pfm
import iispt_transforms
import math
import plotly
import plotly.plotly as py
import plotly.graph_objs as go

# =============================================================================
# Conf

NUM_BUCKETS = 100
INPUTDIR = "/home/gj/git/pbrt-v3-IISPT-dataset-indirect/breakfast"
SELECTOR = "p"
GAMMA_VALUE = 1.8
NORMALIZATION_INTENSITY = 3.807115077972

# =============================================================================
# Script

flist = []

for f in os.listdir(INPUTDIR):
    fpath = os.path.join(INPUTDIR, f)
    if f.startswith(SELECTOR) and f.endswith(".pfm"):
        flist.append(fpath)

def histogram(images, plotname):
    valmax = None
    valmin = None
    vals = []

    for img in images:
        height, width, _ = img.get_shape()
        for y in range(height):
            for x in range(width):
                pixel = img.get_rgb(x, y)
                for v in pixel:
                    if (valmax is None) or (v > valmax):
                        valmax = v
                    if v > 0.0:
                        if (valmin is None) or (v < valmin):
                            valmin = v
                    
                    vals.append(v)

    print("min {} max {}".format(valmin, valmax))

    # Create buckets data structures
    rng = valmax - valmin
    step = rng / NUM_BUCKETS
    buckets_starts = [0] * NUM_BUCKETS
    buckets = [0] * NUM_BUCKETS

    for i in range(NUM_BUCKETS):
        buckets_starts[i] = valmin + (i * step)
    
    # Populate buckets
    for v in vals:
        # Compute its bucket index
        bindex = int(math.floor((v - valmin)/(float(step))))
        # Exclude left-end out of bounds but include right-end
        if bindex >= NUM_BUCKETS:
            bindex = NUM_BUCKETS - 1
        if bindex >= 0:
            buckets[bindex] += 1
    
    # Print buckets
    for i in range(len(buckets)):
        print("{} - {}".format(buckets_starts[i], buckets[i]))
    
    # Plot
    data = [
        go.Bar(
            x=buckets_starts,
            y=buckets
        )
    ]
    plotly.offline.plot(
        {
            "data": data,
            "layout": go.Layout(title=plotname)
        }
    )

# Generate histogram for raw data
standard_imgs = []
for fpath in flist:
    standard_imgs.append(pfm.load(fpath))
histogram(standard_imgs, "Raw intensity")

# Generate histogram after log transform
log_imgs = []
for fpath in flist:
    img = pfm.load(fpath)
    img.map(iispt_transforms.LogTransform())
    log_imgs.append(img)
histogram(log_imgs, "Log transform")

# GEnerate histogram after log + gamma transform
lg_imgs = []
for fpath in flist:
    img = pfm.load(fpath)
    img.normalize_log_gamma(NORMALIZATION_INTENSITY, GAMMA_VALUE)
    lg_imgs.append(img)
histogram(lg_imgs, "Log + Gamma transform")