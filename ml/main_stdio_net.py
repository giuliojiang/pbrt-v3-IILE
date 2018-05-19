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

def write_char(c):
    sys.stdout.buffer.write(c.encode())

# <return> a numpy 1D array
def read_float_array(num):
    buff = sys.stdin.buffer.read(num * 4)
    return numpy.frombuffer(buff, dtype=numpy.float32)

# <return> a (7, height, width) shaped ndarray
def read_input():
    # Read intensity data
    intensityArray = read_float_array(IISPT_IMAGE_SIZE * IISPT_IMAGE_SIZE * 3)

    # Read normals data
    normalsArray = read_float_array(IISPT_IMAGE_SIZE * IISPT_IMAGE_SIZE * 3)

    # Read distance data
    distanceArray = read_float_array(IISPT_IMAGE_SIZE * IISPT_IMAGE_SIZE * 1)

    # Reshape read arrays into (height, width, channels)
    intensityArray = intensityArray.reshape((IISPT_IMAGE_SIZE, IISPT_IMAGE_SIZE, 3))
    normalsArray = normalsArray.reshape((IISPT_IMAGE_SIZE, IISPT_IMAGE_SIZE, 3))
    distanceArray = distanceArray.reshape((IISPT_IMAGE_SIZE, IISPT_IMAGE_SIZE, 1))

    # Transpose into (channels, height, width)
    intensityArray = intensityArray.transpose((2, 0, 1))
    normalsArray = normalsArray.transpose((2, 0, 1))
    distanceArray = distanceArray.transpose((2, 0, 1))

    # Concatenate into single multiarray
    return numpy.concatenate([intensityArray, normalsArray, distanceArray], axis=0)

# =============================================================================
# <nparray> a shape (channel, height, width) 3D ndarray
# Outputted as an image with dimensions order as (height, width, channel)
def output_to_stdout(nparray):
    # Reshape into (height, width, channel)
    data = numpy.transpose(nparray, (1, 2, 0))
    buff = data.tobytes()
    sys.stdout.buffer.write(buff)
    write_char("x")
    write_char("\n")
    sys.stdout.flush()

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