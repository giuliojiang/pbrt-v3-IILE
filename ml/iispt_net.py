import torch
from torch import nn, optim
from torch.autograd.variable import Variable
from torchvision import transforms, datasets

class IISPTNet(torch.nn.Module):

    def __init__(self):
        super(IISPTNet, self).__init__()

        self.hidden0 = nn.Sequential(
            nn.Linear(7168, 5600),
            nn.ELU()
        )

        self.hidden1 = nn.Sequential(
            nn.Linear(5600, 5000),
            nn.ELU(),
            nn.Dropout(0.4)
        )

        self.hidden2 = nn.Sequential(
            nn.Linear(5000, 4500),
            nn.ELU(),
            nn.Dropout(0.4)
        )

        self.hidden3 = nn.Sequential(
            nn.Linear(4500, 3200),
            nn.ELU(),
            nn.Dropout(0.4)
        )

        self.hidden4 = nn.Sequential(
            nn.Linear(3200, 2000),
            nn.ELU(),
            nn.Dropout(0.4)
        )

        self.hidden5 = nn.Sequential(
            nn.Linear(2000, 1000),
            nn.ELU(),
            nn.Dropout(0.4)
        )

        self.hidden6 = nn.Sequential(
            nn.Linear(1000, 800),
            nn.ELU(),
            nn.Dropout(0.4)
        )

        self.hidden7 = nn.Sequential(
            nn.Linear(800, 600),
            nn.ELU(),
            nn.Dropout(0.4)
        )

        self.hidden8 = nn.Sequential(
            nn.Linear(600, 500),
            nn.ELU()
        )

        self.out0 = nn.Sequential(
            nn.Linear(500, 1000),
            nn.ELU()
        )

        self.out1 = nn.Sequential(
            nn.Linear(1000, 2000),
            nn.ELU()
        )

        self.out2 = nn.Sequential(
            nn.Linear(2000, 3072),
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