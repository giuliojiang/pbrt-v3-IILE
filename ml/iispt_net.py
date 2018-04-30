import torch
from torch import nn, optim
from torch.autograd.variable import Variable
from torchvision import transforms, datasets

class IISPTNet(torch.nn.Module):

    def __init__(self):
        super(IISPTNet, self).__init__()

        self.hidden0 = nn.Sequential(
            nn.Linear(7168, 4300),
            nn.LeakyReLU(0.2)
        )

        self.hidden1 = nn.Sequential(
            nn.Linear(4300, 3584),
            nn.LeakyReLU(0.2)
        )

        self.hidden2 = nn.Sequential(
            nn.Linear(3584, 2000),
            nn.LeakyReLU(0.2)
        )

        self.hidden3 = nn.Sequential(
            nn.Linear(2000, 1792),
            nn.LeakyReLU(0.2)
        )

        self.hidden4 = nn.Sequential(
            nn.Linear(1792, 896),
            nn.LeakyReLU(0.2)
        )

        self.hidden5 = nn.Sequential(
            nn.Linear(896, 614),
            nn.LeakyReLU(0.2)
        )

        self.out0 = nn.Sequential(
            nn.Linear(614, 1228),
            nn.LeakyReLU(0.2)
        )

        self.out1 = nn.Sequential(
            nn.Linear(1228, 3072),
            nn.LeakyReLU(0.2)
        )

    def forward(self, x):
        x = self.hidden0(x)
        x = self.hidden1(x)
        x = self.hidden2(x)
        x = self.hidden3(x)
        x = self.hidden4(x)
        x = self.hidden5(x)
        x = self.out0(x)
        x = self.out1(x)

        return x