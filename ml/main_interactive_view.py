import sys
import os
import subprocess

import torch
from torch import nn
from torch.autograd.variable import Variable
import numpy

import config
import iispt_dataset
import pfm
import iispt_net

GAMMA = 1.8

pydir = os.path.dirname(os.path.abspath(__file__)) # root/ml
rootdir = os.path.dirname(pydir)
os.chdir(rootdir)

pfmExecutable = os.path.join(rootdir, "tools", "pfm.js")

def print_force(s):
    print(s)
    sys.stdout.flush()

def convert_image(pfm_path, output_path, png_path):
    subprocess.call([pfmExecutable, pfm_path, "--out=" + output_path])
    subprocess.call(["convert", output_path, png_path])

def main():

    # Load dataset
    trainset, testset = iispt_dataset.load_dataset(config.testset, 1.0)

    selected_set = testset
    selected_set_len = testset.__len__()

    # Load model
    net = iispt_net.IISPTNet()
    net.load_state_dict(torch.load(config.model_path))
    # Put in eval mode
    net.eval()
    print_force("#LOADCOMPLETE {}".format(selected_set_len))


    # Loop for console info
    for line in sys.stdin:
        if line.endswith("\n"):
            line = line[:-1]

        idx = int(line)
        print_force("Requesting index {}".format(idx))

        datum = selected_set.get_datum(idx)
        if datum is None:
            print_force("Out of range!")
            continue
        item = selected_set.__getitem__(idx)
        item_input = item["t"]
        item_input = item_input.unsqueeze(0)
        item_expected = item["p"]

        # Run the network on the data
        input_variable = Variable(item_input)
        result = net(input_variable)
        

        # Save the created result
        result_image = pfm.loadFromConvOutNpArray(result.data.numpy()[0])
        # Upstream processing
        result_image.normalize_intensity_upstream(item["mean"])

        # Save the expected result
        expected_image = pfm.load(item["p_name"])
        # expected_image = pfm.load_from_flat_numpy(item_expected.numpy())
        expectedExposure = expected_image.computeAutoexposure()
        expected_image.save_png("interactiveExpected.png", expectedExposure, GAMMA)

        # Save the created result
        result_image.save_png("interactiveResult.png", expectedExposure, GAMMA)

        # Save the normals map
        normalsImage = pfm.load(item["n_name"])
        normalsImage.save_png("interactiveNormals.png", normalsImage.computeAutoexposure(), GAMMA)

        # Save the distance map
        distanceImage = pfm.load(item["z_name"])
        distanceImage.save_png("interactiveDistance.png", distanceImage.computeAutoexposure(), GAMMA)

        # Save 1SPP path
        lowSamplesImage = pfm.load(item["d_name"])
        lowSamplesImage.save_png("interactiveLow.png", expectedExposure, GAMMA)

        # Make gaussian blur of 1SPP
        gaussianBlurred = lowSamplesImage.makeCopy()
        gaussianBlurred.gaussianBlur(1.0)
        gaussianBlurred.save_png("interactiveBlurred.png", expectedExposure, GAMMA)

        # Compute metrics on the 1SPP path
        lowSamplesL1 = lowSamplesImage.computeL1Loss(expected_image)
        lowSamplesSs = lowSamplesImage.computeStructuralSimilarity(expected_image)
        print_force("#LOWL1 {}".format(lowSamplesL1))
        print_force("#LOWSS {}".format(lowSamplesSs))

        # Compute metrics on blurred
        gaussianBlurredL1 = gaussianBlurred.computeL1Loss(expected_image)
        gaussianBlurredSs = gaussianBlurred.computeStructuralSimilarity(expected_image)
        print_force("#GAUSSL1 {}".format(gaussianBlurredL1))
        print_force("#GAUSSSS {}".format(gaussianBlurredSs))

        # Compute emtrics on NN predicted
        resultL1 = result_image.computeL1Loss(expected_image)
        resultSs = result_image.computeStructuralSimilarity(expected_image)
        print_force("#RESL1 {}".format(resultL1))
        print_force("#RESSS {}".format(resultSs))

        print_force("#EVALUATECOMPLETE")


main()