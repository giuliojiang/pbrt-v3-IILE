# Compute structural similarity metrics on command line images

import sys
import os
toolsDir = os.path.abspath(os.path.dirname(__file__))
rootDir = os.path.dirname(toolsDir)
mlDir = os.path.join(rootDir, "ml")
sys.path.append(mlDir)

import pfm
import scipy.stats
import numpy

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

# Compute SNR
mean = numpy.mean(data)
std = numpy.std(data)
print("SNR {}".format(mean / std))

# Shannon entropy

def nozero(x):
    if x <= 0.0:
        return 0.000001
    return x

# data = testImg.data
# print(data.shape)
# a = data.transpose((2, 0, 1))
# a = numpy.vectorize(nozero)(a)
# a = a / a.sum()
# print(a.shape)
# shannon = -numpy.sum(a*numpy.log2(a))
# print("Shannon entropy {}".format(shannon))