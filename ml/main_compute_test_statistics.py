import sys
import os
import subprocess
import time

import torch
from torch import nn
from torch.autograd.variable import Variable
import numpy
import scipy.stats

import plotly
import plotly.plotly as py
import plotly.graph_objs as go

import config
import iispt_dataset
import pfm
import iispt_net

pydir = os.path.dirname(os.path.abspath(__file__)) # root/ml
rootdir = os.path.dirname(pydir)
os.chdir(rootdir)

def plot(low, gauss, result, title):
    traceLow = go.Box(x=low, name="1spp")
    traceGauss = go.Box(x=gauss, name="blur")
    traceResult = go.Box(x=result, name="predicted")

    data = [traceLow, traceGauss, traceResult]

    plotly.offline.plot(
        {
            "data": data,
            "layout": go.Layout(title=title)
        }
    )

    time.sleep(10.0)

def main():

    # Load dataset
    trainset, testset = iispt_dataset.load_dataset(config.testset, 0.0)

    selected_set = testset
    selected_set_len = testset.__len__()

    # Load model
    net = iispt_net.IISPTNet()
    net.load_state_dict(torch.load(config.model_path))
    # Put in eval mode
    net.eval()
    print("Model loaded")

    # Statistics accumulators
    statLowL1 = []
    statLowSs = []
    statGaussianL1 = []
    statGaussianSs = []
    statResultL1 = []
    statResultSs = []

    # Loop for each test example
    print("Processing {} items".format(selected_set_len))
    for i in range(selected_set_len):

        print("Processing index {}".format(i))

        item = selected_set.__getitem__(i)
        item_input = item["t"]
        item_input = item_input.unsqueeze(0)

        # Run the network on the data
        input_variable = Variable(item_input)
        result = net(input_variable)

        resultImg = pfm.loadFromConvOutNpArray(result.data.numpy()[0])
        resultImg.normalize_intensity_upstream(item["mean"])

        expectedImg = pfm.load(item["p_name"])

        normalsImg = pfm.load(item["n_name"])

        distanceImg = pfm.load(item["z_name"])

        lowImg = pfm.load(item["d_name"])

        # Normalize the maps according to their mean for better statistics
        resultImg.divideMean()
        expectedImg.divideMean()
        lowImg.divideMean()

        gaussianImg = lowImg.makeCopy()
        gaussianImg.gaussianBlur(1.0)

        # Compute metrics on 1SPP
        lowL1 = lowImg.computeL1Loss(expectedImg)
        lowSs = lowImg.computeStructuralSimilarity(expectedImg)

        # Compute metrics on blurred
        gaussianL1 = gaussianImg.computeL1Loss(expectedImg)
        gaussianSs = gaussianImg.computeStructuralSimilarity(expectedImg)

        # Compute metrics on NN predicted
        resultL1 = resultImg.computeL1Loss(expectedImg)
        resultSs = resultImg.computeStructuralSimilarity(expectedImg)

        # Record statistics
        statLowL1.append(lowL1)
        statLowSs.append(lowSs)
        statGaussianL1.append(gaussianL1)
        statGaussianSs.append(gaussianSs)
        statResultL1.append(resultL1)
        statResultSs.append(resultSs)

    print("Statistics collection completed")

    # To numpy
    statLowL1 = numpy.array(statLowL1)
    statLowSs = numpy.array(statLowSs)
    statGaussianL1 = numpy.array(statGaussianL1)
    statGaussianSs = numpy.array(statGaussianSs)
    statResultL1 = numpy.array(statResultL1)
    statResultSs = numpy.array(statResultSs)

    plot(statLowL1, statGaussianL1, statResultL1, "L1")
    plot(statLowSs, statGaussianSs, statResultSs, "Structural Similarity")

    # Compute P values for L1
    data = {
        'a': statGaussianL1,
        'b': statResultL1
    }
    t, p =  scipy.stats.f_oneway(*data.values())
    print("P value L1 gaussian-predicted {}".format(p))
    
    # Compute P values for Ss
    data = {
        'a': statGaussianSs,
        'b': statResultSs
    }
    t, p =  scipy.stats.f_oneway(*data.values())
    print("P value Ss gaussian-predicted {}".format(p))

    # Compute P values for L1
    data = {
        'a': statLowL1,
        'b': statResultL1
    }
    t, p =  scipy.stats.f_oneway(*data.values())
    print("P value L1 low-predicted {}".format(p))
    
    # Compute P values for Ss
    data = {
        'a': statLowSs,
        'b': statResultSs
    }
    t, p =  scipy.stats.f_oneway(*data.values())
    print("P value Ss low-predicted {}".format(p))

# main()