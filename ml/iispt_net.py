import torch
from torch import nn, optim
from torch.autograd.variable import Variable
from torchvision import transforms, datasets

class IISPTNet(torch.nn.Module):

    def __init__(self):
        super(IISPTNet, self).__init__()

        self.hidden0 = nn.Sequential(
            nn.Linear(7168, 6450),
            nn.LeakyReLU(0.2)
        )

        self.hidden1 = nn.Sequential(
            nn.Linear(6450, 5800),
            nn.LeakyReLU(0.2)
        )

        self.hidden2 = nn.Sequential(
            nn.Linear(5800, 5225),
            nn.Tanh()
        )

        self.hidden3 = nn.Sequential(
            nn.Linear(5225, 4700),
            nn.Tanh()
        )

        self.hidden4 = nn.Sequential(
            nn.Linear(4700, 3300),
            nn.Tanh()
        )

        self.hidden5 = nn.Sequential(
            nn.Linear(3300, 2200),
            nn.Tanh()
        )

        self.hidden6 = nn.Sequential(
            nn.Linear(2200, 1800),
            nn.Tanh()
        )

        self.hidden7 = nn.Sequential(
            nn.Linear(1800, 1024),
            nn.Tanh()
        )

        self.out0 = nn.Sequential(
            nn.Linear(1024, 1800),
            nn.Tanh()
        )

        self.out1 = nn.Sequential(
            nn.Linear(1800, 2500),
            nn.Tanh()
        )

        self.out2 = nn.Sequential(
            nn.Linear(2500, 3072),
            nn.Tanh()
        )
    
    def forward(self, x):
        x = self.hidden0(x)
        x = self.hidden1(x)
        x = self.hidden2(x)
        x = self.hidden3(x)
        x = self.hidden4(x)
        x = self.hidden5(x)
        x = self.hidden6(x)
        x = self.hidden7(x)
        x = self.out0(x)
        x = self.out1(x)
        x = self.out2(x)
        return x