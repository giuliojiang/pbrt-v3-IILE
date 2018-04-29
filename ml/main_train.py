import time
import os
from datetime import datetime

import torch
from torch import nn, optim
from torch.autograd.variable import Variable
from torchvision import transforms, datasets
import torch.optim as optim
from tensorboardX import SummaryWriter

import iispt_dataset
import iispt_net
import config

TRAINING_TIME_MINUTES = 120.0
BATCH_SIZE = 100
NO_WORKERS = 2
LEARNING_RATE = 0.0001
DATASET_DIR = "/home/gj/git/pbrt-v3-IISPT-dataset-indirect"

log_dir = os.path.join('/tmp/runs', datetime.now().strftime('%b%d_%H-%M-%S'))
writer = SummaryWriter(log_dir=log_dir)

start_time = time.time()

def minutes_elapsed():
    current_seconds = time.time()
    elapsed_seconds = current_seconds - start_time
    elapsed_minutes = elapsed_seconds / 60.0
    return elapsed_minutes

def train():

    trainset, testset = iispt_dataset.load_dataset(DATASET_DIR, 0.1)

    trainloader = torch.utils.data.DataLoader(trainset, batch_size=BATCH_SIZE, shuffle=True, num_workers=NO_WORKERS)
    testloader = torch.utils.data.DataLoader(testset, batch_size=BATCH_SIZE, shuffle=False, num_workers=NO_WORKERS)

    net = iispt_net.IISPTNet().cuda()

    criterion = nn.L1Loss()
    # optimizer = optim.Adam(net.parameters(), lr=LEARNING_RATE)
    optimizer = optim.Rprop(net.parameters(), lr=LEARNING_RATE)

    epoch_loss = []
    running_loss = 0.0

    epoch = 0
    n_iter = 0

    print("Dataset loaded from {}".format(DATASET_DIR))
    print("About to start training... for Tensorboard, use tensorboard --logdir /tmp/runs")

    while True:

        elapsed_minutes = minutes_elapsed()
        print("Training: elapsed {} minutes".format(elapsed_minutes))
        if elapsed_minutes > TRAINING_TIME_MINUTES:
            break

        # each i is a batch
        for i, data in enumerate(trainloader, 0):

            # Get the inputs
            input_x = data["t"]
            expected_x = data["p"]

            # Wrap in variables
            input_v = Variable(input_x.cuda())
            expected_v = Variable(expected_x.cuda())

            # Zero the parameter gradients
            optimizer.zero_grad()

            # Forward, backward, optimize
            outputs = net(input_v)
            loss = criterion(outputs, expected_v)
            loss.backward()
            optimizer.step()

            # Print statistics
            running_loss = loss.data[0]
            print("Epoch [{}] example [{}] Running loss [{}]".format(epoch, i * BATCH_SIZE, running_loss))

            # Log train/loss to TensorBoard at every iteration
            writer.add_scalar('train/loss', loss.data[0], n_iter)
            n_iter += 1
        
        epoch_loss.append(running_loss)

        # Log model parameters to TensorBoard at every epoch
        for name, param in net.named_parameters():
            layer, attr = os.path.splitext(name)
            attr = attr[1:]
            writer.add_histogram('{}/{}'.format(layer, attr), param.clone().cpu().data.numpy(), n_iter)

    print("Finished training")

    for i in range(len(epoch_loss)):
        print("Epoch {} Loss {}".format(i, epoch_loss[i]))

    net = net.cpu()
    torch.save(net, config.model_path)
    print("Model saved: {}".format(config.model_path))

train()
writer.close()