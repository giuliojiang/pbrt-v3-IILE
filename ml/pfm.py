# This class defines the PFM image format loader and
# saver
# The loaded class uses a numpy array as storage format
# for easy use in PyTorch

import numpy
import struct
import math
import scipy.misc
import PIL
import array
import sys
import scipy.signal
from skimage.measure import compare_ssim as ssim
import scipy.ndimage
import time

import iispt_transforms


# =============================================================================
# Class definitions

class PfmImage:

    # self.data is a numpy array
    # with shape (height, width, channels)
    # of float32 values

    # -------------------------------------------------------------------------
    def __init__(self, data, location):
        self.data = data
        self.location = location
    
    # -------------------------------------------------------------------------
    def makeCopy(self):
        newData = numpy.copy(self.data)
        return PfmImage(newData, self.location)

    # -------------------------------------------------------------------------
    def clear(self):
        shape = self.data.shape
        self.data = numpy.zeros(shape, dtype=numpy.float32)
    
    # -------------------------------------------------------------------------
    def print_shape(self):
        print(self.data.shape)

    # -------------------------------------------------------------------------
    def get_shape(self):
        return self.data.shape
    
    # -------------------------------------------------------------------------
    def print_array(self):
        print(self.data)

    # -------------------------------------------------------------------------
    def print_samples(self):
        height, width, channels = self.data.shape
        y = 0
        while y < height:
            x = 0
            while x < width:
                for c in range(channels):
                    sys.stdout.write(" {}".format(self.data[y, x, c]))
                x += 5
            y += 5
        print()
    
    # -------------------------------------------------------------------------
    def get_numpy_array(self):
        return self.data
    
    # -------------------------------------------------------------------------
    def get_mean(self):
        return numpy.mean(self.data)
    
    # -------------------------------------------------------------------------
    def map(self, f):
        f = numpy.vectorize(f)
        self.data = f(self.data)

    # -------------------------------------------------------------------------
    def get_rgb(self, x, y):
        res = []
        res.append(self.data[y, x, 0])
        res.append(self.data[y, x, 1])
        res.append(self.data[y, x, 2])
        return res

    # -------------------------------------------------------------------------
    def jacobian_transform(self):
        height, width, channels = self.data.shape
        for y in range(height):
            abs_vertical_value = float(y) / float(height)
            polar_vertical_value = (math.pi / 2.0) * abs_vertical_value
            polar_vertical_value += (math.pi / 4.0)
            jacobian_factor = math.sin(polar_vertical_value)
            for x in range(width):
                for c in range(channels):
                    self.data[y, x, c] = self.data[y, x, c] * jacobian_factor

    # -------------------------------------------------------------------------
    # Flips the entire image on the Y axis
    def flipY(self):
        height, width, channels = self.data.shape
        res = numpy.zeros(shape=(height, width, channels), dtype=numpy.float32)

        # X, Y, C are in the output image
        # YY is in the original image
        for y in range(height):
            yy = height - 1 - y
            for x in range(width):
                for c in range(channels):
                    res[y, x, c] = self.data[yy, x, c]
        self.data = res

    # -------------------------------------------------------------------------
    # Given min and max vals in the original range,
    # Remaps everything into the [-1, +1] range
    # And clips any values that stay outside
    def normalize(self, min_val, max_val):
        self.data = iispt_transforms.npNormalize(self.data, min_val, max_val)
    
    # -------------------------------------------------------------------------
    # Applies a natural logarithm on the value
    # And normalizes according to given max_value
    def normalize_log(self, max_value):
        self.map(iispt_transforms.LogTransform())
        self.normalize(0.0, max_value)
    
    # -------------------------------------------------------------------------
    # Applies a natural logarithm followed by a gamma curve
    # to boost the smaller values
    # Normalizes according to the given max_value
    def normalize_log_gamma(self, max_value, gamma):
        self.map(iispt_transforms.IntensitySequence(max_value, gamma))

    # -------------------------------------------------------------------------
    # 1 - Apply the square root
    # 2 - Normalize according to the max value. Min value is -1
    #     for the pixels that have no intersection
    def normalize_sqrt(self, max_value):
        self.map(iispt_transforms.SqrtTransform())
        self.normalize(-1.0, max_value)

    # -------------------------------------------------------------------------
    # 1 - Apply the square root
    # 2 - Normalize according to max value into [0,1]
    # 3 - Apply gamma correction
    def normalize_sqrt_gamma(self, max_value, gamma):
        self.map(iispt_transforms.DistanceSequence(max_value, gamma))
    
    # -------------------------------------------------------------------------
    # <return> mean
    def normalize_intensity_downstream_full(self):
        mean = numpy.mean(self.data)
        # Divide by 10 mean
        self.data = iispt_transforms.npDivide(self.data, 10.0*mean)
        # Log transform
        self.data = iispt_transforms.npLog(self.data)
        # Subtract 0.1
        self.data = iispt_transforms.npSub(self.data, 0.1)
        # return
        return mean

    # -------------------------------------------------------------------------
    # Normalize with mean at 0.0
    # Log
    # Log
    def normalize_intensity_downstream_half(self):
        mean = numpy.mean(self.data)
        # Divide by 10 mean
        self.data = iispt_transforms.npDivide(self.data, 10.0*mean)
        # Log transform
        self.data = iispt_transforms.npLog(self.data)
    
    # -------------------------------------------------------------------------
    # Inv Log
    # Inv Log
    # Multiply by original mean
    def normalize_intensity_upstream(self, omean):
        self.map(iispt_transforms.IntensityUpstreamSequence(omean))

    # -------------------------------------------------------------------------
    def normalize_distance_downstream_full(self):
        mean = numpy.mean(self.data)
        # Add 1
        self.data = iispt_transforms.npAdd(self.data, 1.0)
        # Divide by (10 * (mean + 1))
        self.data = iispt_transforms.npDivide(self.data, (10.0 * (mean + 1.0)))
        # Log
        self.data = iispt_transforms.npLog(self.data)
        # Subtract 0.1
        self.data = iispt_transforms.npSub(self.data, 0.1)

    # -------------------------------------------------------------------------
    def divideMean(self):
        mean = numpy.mean(self.data)
        if mean > 0.0:
            self.data = self.data / mean
    
    # -------------------------------------------------------------------------
    # Write out to .pfm file
    def save_pfm(self, out_path):
        print("Writing {}".format(out_path))
        out_file = open(out_path, "wb")

        # Write identifier line
        if self.data.shape[2] == 3:
            out_file.write(b"PF\n")
        else:
            out_file.write(b"Pf\n")

        # Write dimensions line
        height, width, channels = self.data.shape
        out_file.write("{} {}\n".format(width, height).encode())

        # Write scale factor and endianness
        out_file.write(b"1\n")

        # Write pixel values
        for y in range(height):
            for x in range(width):
                for c in range(channels):
                    write_float_32(out_file, self.data[y, x, c])

        out_file.close()
    
    # -------------------------------------------------------------------------
    # Write out to LDR PNG file, with exposure and gamma settings
    def save_png(self, out_path, exposure, gamma, reverse=False):

        exposure = float(exposure)
        gamma = float(gamma)
        # Create bytebuffer
        height, width, channels = self.data.shape
        buff = bytearray()

        # Triplicate values if single channel
        if channels == 1:
            d = numpy.concatenate([self.data, self.data, self.data], axis=2)
        elif channels == 3:
            d = self.data
        else:
            raise Exception("Unsupported channels {}".format(channels))

        # Adjust according to exposure and gamma
        exposureMult = 2.0**exposure
        d = d * exposureMult
        d = numpy.clip(d, 0.0, 1.0)
        gammaPow = 1.0 / gamma
        d = numpy.power(d, gammaPow)
        d = d * 255.0

        # Flip Y if necessary
        if reverse:
            d = numpy.flip(d, 0)

        # Flatten
        d = d.flatten()

        # Change type
        d = d.astype(numpy.uint8)

        im = PIL.Image.frombytes(
            "RGB",
            (width, height),
            d.tobytes()
        )
        im.save(out_path)


    # -------------------------------------------------------------------------
    # Compute autoexposure
    # Steps exposure values one at a time starting from 20
    # Until less than 10% of the pixels are clipped in the upper bound
    def computeAutoexposure(self):
        currentExposure = 20.0
        height, width, channels = self.data.shape
        while True:
            clippedCount = 0.0
            totalCount = float(width * height * channels)

            multiplier = 2.0**currentExposure
            t = self.data * multiplier
            clippedCount = (t > 1.0).sum()
            clippedRatio = float(clippedCount) / totalCount

            if clippedRatio < 0.10:
                return currentExposure
            else:
                currentExposure -= 1.0
    
    # -------------------------------------------------------------------------
    # Compute L1 loss
    # Average of absolute differences
    def computeL1Loss(self, other):
        height, width, channels = self.data.shape
        totalCount = float(height * width * channels)

        differenceSum = 0.0

        for y in range(height):
            for x in range(width):
                for c in range(channels):
                    va = self.data[y, x, c]
                    vb = other.data[y, x, c]
                    differenceSum += abs(va - vb)
        
        return differenceSum / totalCount
    
    # -------------------------------------------------------------------------
    # Compute cross correlation
    def computeCrossCorrelation(self, other):
        height, width, channels = self.data.shape

        crossCorrelation = 0.0

        for c in range(channels):
            imgA = numpy.zeros((height, width), dtype=numpy.float32)
            imgB = numpy.zeros((height, width), dtype=numpy.float32)
            for y in range(height):
                for x in range(width):
                    imgA[y, x] = self.data[y, x, c]
                    imgB[y, x] = other.data[y, x, c]
            # Normalize the 2 images
            imgAMean = numpy.mean(imgA)
            imgAStd = numpy.std(imgA)
            imgA = imgA - imgAMean
            if imgAStd > 0.0:
                imgA = imgA / imgAStd
            imgBMean = numpy.mean(imgB)
            imgBStd = numpy.std(imgB)
            imgB = imgB - imgBMean
            if imgBStd > 0.0:
                imgB = imgB / imgBStd
            crossCorrelation += numpy.mean(scipy.signal.correlate2d(imgA, imgB))
        
        return crossCorrelation

    # -------------------------------------------------------------------------
    # Compute structural similarity
    # <other> should be the ground truth
    def computeStructuralSimilarity(self, other):
        height, width, channels = self.data.shape
        h2, w2, _ = other.data.shape
        height = min(height, h2)
        width = min(width, w2)
        similarityMeasures = 0.0

        for c in range(channels):
            imgA = numpy.zeros((height, width), dtype=numpy.float32)
            imgB = numpy.zeros((height, width), dtype=numpy.float32)
            for y in range(height):
                for x in range(width):
                    imgA[y, x] = self.data[y, x, c]
                    imgB[y, x] = other.data[y, x, c]
            aSimil = ssim(
                imgA,
                imgB
            )
            similarityMeasures += aSimil

        return similarityMeasures / float(channels)

    # -------------------------------------------------------------------------
    def gaussianBlur(self, sd):
        self.data = numpy.copy(self.data)
        height, width, channels = self.data.shape

        for c in range(channels):
            tempArray = numpy.zeros((height, width), dtype=numpy.float32)
            for y in range(height):
                for x in range(width):
                    tempArray[y, x] = self.data[y, x, c]
            
            blurred = scipy.ndimage.gaussian_filter(tempArray, sigma=sd)

            for y in range(height):
                for x in range(width):
                    self.data[y, x, c] = blurred[y, x]

    # -------------------------------------------------------------------------
    def vflip(self):
        self.data = numpy.flip(self.data, 0)

    # -------------------------------------------------------------------------
    def hflip(self):
        self.data = numpy.flip(self.data, 1)

    # -------------------------------------------------------------------------
    def rotate(self, times):
        self.data = numpy.rot90(self.data, times)


# =============================================================================
# Utilities

def read_line(f):
    buff = b""
    while True:
        c = f.read(1)
        if not c:
            raise Exception("Unexpected end of file")
        elif c == b'\n':
            return buff.decode("UTF-8")
        else:
            buff += c

# <return> a numpy 1D array
def read_float_array(num, f):
    buff = f.read(num * 4)
    return numpy.frombuffer(buff, dtype=numpy.float32)

def write_float_32(f, v):
    data = struct.pack('f', v)
    f.write(data)

# =============================================================================
# Load

def load(file_path):

    # Use a large 10KB buffer
    f = open(file_path, "rb", 10000)

    # Read the identifier line
    identifier_line = read_line(f)
    if identifier_line == "PF":
        channels = 3
    elif identifier_line == "Pf":
        channels = 1
    else:
        raise Exception("Unrecognized identifier line {}".format(identifier_line))
    
    # Read the dimensions line
    dimensions_line = read_line(f)
    dimensions_line_split = dimensions_line.split(" ")
    if len(dimensions_line_split) != 2:
        raise Exception("Could not recognize PFM dimensions line in [{}]".format(dimensions_line))
    width = int(dimensions_line_split[0])
    height = int(dimensions_line_split[1])

    # Read scale factor and endianness
    read_line(f)
    # Ignore the value

    # Read pixel values
    # The array has 3 dimensions: Height, Width, Channels
    data = read_float_array(height * width * channels, f)
    data = data.reshape((height, width, channels))

    f.close()

    # Create final object
    return PfmImage(data, file_path)

# =============================================================================
# Load from flattened numpy array

def load_from_flat_numpy(narray, width=32, height=32, channels=3):
    shape = (height, width, channels)
    narray = narray.reshape(shape)
    return PfmImage(narray, "NPARRAY")

# =============================================================================
# Load from ConvOutNpArray

def loadFromConvOutNpArray(vals):
    channels, height, width = vals.shape
    res = numpy.zeros((height, width, channels), dtype=numpy.float32)
    for y in range(height):
        for x in range(width):
            for c in range(channels):
                res[y, x, c] = vals[c, y, x]
    return PfmImage(res, "CONVOUTNPARRAY")

# =============================================================================
# Quick test

def test_main():
    files = [
        "/home/gj/git/pbrt-v3-IISPT-dataset-indirect/bathroom-0/p_448_168.pfm",
        "/home/gj/git/pbrt-v3-IISPT-dataset-indirect/bathroom-0/z_64_72.pfm",
        "/home/gj/git/pbrt-v3-IISPT-dataset-indirect/bathroom-0/n_64_288.pfm",
        "/home/gj/git/pbrt-v3-IISPT-dataset-indirect/bathroom-0/d_544_408.pfm"
    ]

    pPfm = load("/home/gj/git/pbrt-v3-IISPT-dataset-indirect/bathroom-0/p_448_168.pfm")

    nameCount = 0

    for f in files:
        print()
        nameCount += 1
        print(f)
        p = load(f)
        autoExposure = p.computeAutoexposure()
        print("Autoexposure computed {}".format(autoExposure))
        p.save_png("/tmp/testmain{}.png".format(nameCount), autoExposure, 1.8)
        l1loss = p.computeL1Loss(pPfm)
        print("Loss compared to P is {}".format(l1loss))
        crossCorr = p.computeCrossCorrelation(pPfm)
        print("CrossCorrelation is {}".format(crossCorr))
        similarity = p.computeStructuralSimilarity(pPfm)
        print("Structural similarity is {}".format(similarity))

        aCopy = p.makeCopy()
        aCopy.gaussianBlur(1.0)
        aCopy.save_png("/tmp/testblur{}.png".format(nameCount), autoExposure, 1.8)

def test_main2():
    fp = "/home/gj/git/pbrt-v3-IISPT-dataset-indirect/custom-fireplace1/d_426_160.pfm"
    imgOld = load(fp)
    imgNew = load(fp)

    imgOld.normalize_distance_downstream_full()
    imgNew.normalize_distance_downstream_full_new()

    allClose = numpy.allclose(imgOld.data, imgNew.data, rtol=0.0001, atol=0.0001)
    print("All close {}".format(allClose))

    print("OLD SYSTEM")
    print(imgOld.data)

    print("NEW SYSTEM")
    print(imgNew.data)

# test_main()
# test_main2()