# Compute structural similarity metrics on command line images

import sys
import os
toolsDir = os.path.abspath(os.path.dirname(__file__))
rootDir = os.path.dirname(toolsDir)
mlDir = os.path.join(rootDir, "ml")
sys.path.append(mlDir)

import pfm
import scipy.stats

argv = sys.argv[1:]

referencePath = os.path.abspath(argv[0])
testPath = os.path.abspath(argv[1])
print("Reference {}".format(referencePath))
print("Test {}".format(testPath))

referenceImg = pfm.load(referencePath)
testImg = pfm.load(testPath)
ssimValue = testImg.computeStructuralSimilarity(referenceImg)
print("SSIM {}".format(ssimValue))

# Compute entropy on the test image
data = testImg.data
data = data.flatten()
entropy = scipy.stats.entropy(data)
print("Entropy {}".format(entropy))