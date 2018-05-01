import sys
import os
import subprocess

import torch
from torch.autograd.variable import Variable
import numpy

import config
import iispt_dataset
import pfm

pydir = os.path.dirname(os.path.abspath(__file__)) # root/ml
rootdir = os.path.dirname(pydir)
os.chdir(rootdir)

def print_force(s):
    print(s)
    sys.stdout.flush()

def convert_image(pfm_path, output_path, png_path):
    subprocess.call(["pfm", pfm_path, "--out=" + output_path])
    subprocess.call(["convert", output_path, png_path])

def main():

    # Load dataset
    trainset, testset = iispt_dataset.load_dataset(config.dataset, 0.1)

    selected_set = testset
    selected_set_len = testset.__len__()

    # Load model
    net = torch.load(config.model_path)
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
        item_expected = item["p"]

        # Run the network on the data
        input_variable = Variable(item_input)
        print_force("Input variable.data is {}".format(input_variable.data))
        result = net(input_variable)
        print_force("Result.data is {}".format(result.data))
        print_force("Expected is {}".format(item_expected))

        # TODO inverse log transform

        # Save the created result
        result_image = pfm.load_from_flat_numpy(result.data.numpy())
        # Upstream processing
        result_image.normalize_intensity_upstream(item["mean"])
        result_image.save_pfm("created.pfm")

        # Save the expected result
        expected_image = pfm.load(item["p_name"])
        # expected_image = pfm.load_from_flat_numpy(item_expected.numpy())
        expected_image.save_pfm("expected.pfm")

        # Convert images to PNG
        convert_image("created.pfm", "created.ppm", "created.png")
        convert_image("expected.pfm", "expected.ppm", "expected.png")

        print_force("#EVALUATECOMPLETE")


main()