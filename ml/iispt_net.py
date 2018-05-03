import torch
from torch import nn, optim
from torch.autograd.variable import Variable
from torchvision import transforms, datasets

class IISPTNet(torch.nn.Module):

    def __init__(self):
        super(IISPTNet, self).__init__()

        self.hidden0 = nn.Sequential(
            nn.Linear(7168, 6000),
            nn.ELU(),
            nn.Dropout(0.2)
        )

        self.hidden1 = nn.Sequential(
            nn.Linear(6000, 5000),
            nn.ELU(),
            nn.Dropout(0.2)
        )

        self.hidden2 = nn.Sequential(
            nn.Linear(5000, 4500),
            nn.ELU(),
            nn.Dropout(0.2)
        )

        self.hidden3 = nn.Sequential(
            nn.Linear(4500, 4000),
            nn.ELU(),
            nn.Dropout(0.2)
        )

        self.hidden4 = nn.Sequential(
            nn.Linear(4000, 3500),
            nn.ELU(),
            nn.Dropout(0.2)
        )

        self.hidden5 = nn.Sequential(
            nn.Linear(3500, 3000),
            nn.ELU(),
            nn.Dropout(0.2)
        )

        self.hidden6 = nn.Sequential(
            nn.Linear(3000, 2500),
            nn.ELU(),
            nn.Dropout(0.2)
        )

        self.hidden7 = nn.Sequential(
            nn.Linear(2500, 2000),
            nn.ELU(),
            nn.Dropout(0.2)
        )

        self.hidden8 = nn.Sequential(
            nn.Linear(2000, 1950),
            nn.ELU(),
            nn.Dropout(0.2)
        )

        self.out0 = nn.Sequential(
            nn.Linear(1950, 2000),
            nn.ELU(),
            nn.Dropout(0.2)
        )

        self.out1 = nn.Sequential(
            nn.Linear(2000, 2500),
            nn.ELU(),
            nn.Dropout(0.2)
        )

        self.out2 = nn.Sequential(
            nn.Linear(2500, 3072),
            nn.ELU()
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
        x = self.hidden8(x)
        x = self.out0(x)
        x = self.out1(x)
        x = self.out2(x)
        return x