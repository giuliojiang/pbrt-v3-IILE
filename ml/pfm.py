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
        t = iispt_transforms.NormalizeTransform(min_val, max_val)
        self.map(t)
    
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
        self.map(iispt_transforms.IntensityDownstreamFullSequence(mean))
        return mean

    # -------------------------------------------------------------------------
    # Normalize with mean at 0.0
    # Log
    # Log
    def normalize_intensity_downstream_half(self):
        mean = numpy.mean(self.data)
        self.map(iispt_transforms.IntensityDownstreamHalfSequence(mean))
    
    # -------------------------------------------------------------------------
    # Inv Log
    # Inv Log
    # Multiply by original mean
    def normalize_intensity_upstream(self, omean):
        self.map(iispt_transforms.IntensityUpstreamSequence(omean))

    # -------------------------------------------------------------------------
    def normalize_distance_downstream_full(self):
        mean = numpy.mean(self.data)
        self.map(iispt_transforms.DistanceDownstreamSequence(mean))
    
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
    def save_png(self, out_path, exposure, gamma):
        exposure = float(exposure)
        gamma = float(gamma)
        # Create bytebuffer
        height, width, channels = self.data.shape
        buff = bytearray()
        for y in range(height):
            for x in range(width):
                arr_pix = []
                if channels == 1:
                    v = self.data[y, x, 0]
                    rgb = [v, v, v]
                elif channels == 3:
                    rgb = [
                        self.data[y, x, 0],
                        self.data[y, x, 1],
                        self.data[y, x, 2]
                    ]
                else:
                    raise Exception("Number of channels is neither 1 nor 3 but it's {}".format(channels))

                for v in rgb:
                    # Adjust exposure
                    v *= 2.0**exposure
                    # Clamp
                    if v < 0.0:
                        v = 0.0
                    if v > 1.0:
                        v = 1.0
                    # Gamma
                    v = v**(1.0 / gamma)
                    buff.append(int(255.0 * v))

        im = PIL.Image.frombytes(
            "RGB",
            (width, height),
            bytes(buff)
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
            totalCount = float(width * height)
            for y in range(height):
                for x in range(width):
                    pixelSum = 0.0
                    pixelCount = float(channels)
                    for c in range(channels):
                        pixelSum += self.data[y, x, c]
                    pixelAvg = pixelSum / pixelCount
                    # Compute exposed value
                    exposedPixel = pixelAvg * (2.0**currentExposure)
                    if exposedPixel > 1.0:
                        clippedCount += 1.0
            clippedRatio = clippedCount / totalCount
            if clippedRatio < 0.10:
                return currentExposure
            else:
                currentExposure -= 1.0


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

def read_float_32(f):
    return struct.unpack('f', f.read(4))[0]

def write_float_32(f, v):
    data = struct.pack('f', v)
    f.write(data)

def load_pixel(f, y, x, channels, data):
    for p in range(channels):
        val = read_float_32(f)
        data[y, x, p] = val

def load_row(f, y, width, channels, data):
    # 2 dimensions: width, channels
    for x in range(width):
        load_pixel(f, y, x, channels, data)
    
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
    data = numpy.zeros(shape=(height, width, channels), dtype=numpy.float32)
    for y in range(height):
        load_row(f, y, width, channels, data)
    
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

    nameCount = 0

    for f in files:
        nameCount += 1
        print(f)
        p = load(f)
        autoExposure = p.computeAutoexposure()
        print("Autoexposure computed {}".format(autoExposure))
        p.save_png("/tmp/testmain{}.png".format(nameCount), autoExposure, 1.8)

test_main()