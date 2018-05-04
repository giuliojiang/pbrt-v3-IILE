import torch
from torch import nn, optim
from torch.autograd.variable import Variable
from torchvision import transforms, datasets

class IISPTNet(torch.nn.Module):

    def __init__(self):
        super(IISPTNet, self).__init__()

        # Input depth:
        # Intensity RGB
        # Normals XYZ
        # Distance Z
        # 7 channels

        # Output depth:
        # Intensity RGB
        # 3 channels

        self.encoder = nn.Sequential(
            # Input 32x32
            nn.Conv2d(7, 16, 5, stride=1, padding=2),
            nn.ELU(),
            nn.Dropout2d(0.1),

            nn.Conv2d(16, 32, 5, stride=1, padding=2),
            nn.ELU(),

            nn.MaxPool2d(2), # 16x16

            nn.Conv2d(32, 22, 5, stride=1, padding=2),
            nn.ELU(),

            nn.Conv2d(22, 20, 5, stride=1, padding=2),
            nn.ELU(),

            nn.MaxPool2d(2), # 8x8

            nn.Conv2d(20, 19, 5, stride=1, padding=2),
            nn.ELU()
        )

        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(19, 20, 5, stride=1, padding=2), # 8x8
            nn.ELU(),

            nn.Upsample(scale_factor=2), # 16x16

            nn.ConvTranspose2d(20, 22, 5, stride=1, padding=2),
            nn.ELU(),

            nn.ConvTranspose2d(22, 32, 5, stride=1, padding=2),
            nn.ELU(),

            nn.Upsample(scale_factor=2), # 32x32

            nn.ConvTranspose2d(32, 16, 5, stride=1, padding=2),
            nn.ELU(),

            nn.ConvTranspose2d(16, 3, 5, stride=1, padding=2),
            nn.ELU(),
        )

    def forward(self, x):
        x = self.encoder(x)
        x = self.decoder(x)
        return x
