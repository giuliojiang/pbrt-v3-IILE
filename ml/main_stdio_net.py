import sys
import os
import subprocess
import struct
import time

import torch
from torch.autograd.variable import Variable
import numpy

import config
import iispt_transforms
import iispt_dataset
import km
import iispt_net

# =============================================================================

# @prop
# Will be populated with keys "int_norm" and "dist_norm"

# -----------------------------------------------------------------------------
# Constants

IISPT_IMAGE_SIZE = 32

# -----------------------------------------------------------------------------
# Init

pydir = os.path.dirname(os.path.abspath(__file__)) # root/ml
rootdir = os.path.dirname(pydir)
os.chdir(rootdir)

# =============================================================================
# Utilities

def print_stderr(s):
    sys.stderr.write(s + "\n")

def read_float():
    return struct.unpack('f', sys.stdin.buffer.read(4))[0]

def write_float(x):
    sys.stdout.buffer.write(struct.pack("f", x))

def write_float_array(xs):
    data = struct.pack("{}f".format(len(xs)), *xs)
    sys.stdout.buffer.write(data)
    sys.stdout.flush()

def write_char(c):
    sys.stdout.buffer.write(c.encode())

# <return> a python array
def read_float_array(num):
    buff = sys.stdin.buffer.read(num * 4)
    return struct.unpack('{}f'.format(num), buff)

# <return> a (7, height, width) shaped ndarray
def read_input():
    # Read intensity data
    print_stderr("python: Reading intensity")
    intensityArray = read_float_array(IISPT_IMAGE_SIZE * IISPT_IMAGE_SIZE * 3)
    print_stderr("python: intensity read.")

    # Read normals data
    print_stderr("python: reading normals")
    normalsArray = read_float_array(IISPT_IMAGE_SIZE * IISPT_IMAGE_SIZE * 3)
    print_stderr("python: normals read")

    # Read distance data
    print_stderr("python: reading distance")
    distanceArray = read_float_array(IISPT_IMAGE_SIZE * IISPT_IMAGE_SIZE * 1)
    print_stderr("python: distance read.")

    # Create final numpy ndarray
    res = numpy.zeros(
        shape=(7, IISPT_IMAGE_SIZE, IISPT_IMAGE_SIZE),
        dtype=numpy.float32
    )

    # Populate data values
    height = IISPT_IMAGE_SIZE
    width = IISPT_IMAGE_SIZE
    for y in range(height):
        for x in range(width):
            # Compute flattened index
            idx = y * width + x
            idx3 = 3 * idx
            # Intensity
            res[0, y, x] = intensityArray[idx3 + 0]
            res[1, y, x] = intensityArray[idx3 + 1]
            res[2, y, x] = intensityArray[idx3 + 2]
            # Normals
            res[3, y, x] = normalsArray[idx3 + 0]
            res[4, y, x] = normalsArray[idx3 + 1]
            res[5, y, x] = normalsArray[idx3 + 2]
            # Distance
            res[6, y, x] = distanceArray[idx]

    return res

# =============================================================================
# <nparray> a shape (channel, height, width) 3D ndarray
# Outputted as an image with dimensions order as (height, width, channel)
def output_to_stdout(nparray):
    print_stderr("python: waiting 5 seconds before writing")
    time.sleep(5.0)
    channels, height, width = nparray.shape
    print_stderr("python: Writing to STDOUT. Shape is: {}".format(nparray.shape))
    writeCount = 0
    for y in range(height):
        for x in range(width):
            for c in range(channels):
                write_float(nparray[c, y, x])
                writeCount += 1

    print_stderr("python: Written {} floats".format(writeCount))

    write_char("x")
    write_char("\n")

# =============================================================================
# Processing function
def process_one(net):

    # Read input from stdin
    inputNdArray = read_input()
    torchData = torch.from_numpy(inputNdArray).float()
    torchData = torchData.unsqueeze(0)
    inputVariable = Variable(torchData)

    # Run the network
    outputVariable = net(inputVariable)

    outputNdArray = outputVariable.data.numpy()[0]
    output_to_stdout(outputNdArray)
    print_stderr("python: One completed.")

# =============================================================================
# Main

def main():
    print_stderr("main_stdio_net.py: Startup")
    # Load model
    net = iispt_net.IISPTNet()
    net.load_state_dict(torch.load(config.model_path))
    # Put in eval mode
    net.eval()
    print_stderr("Model loaded")

    while True:
        process_one(net)

main()