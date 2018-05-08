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

        # In 32x32
        self.encoder0 = nn.Sequential(
            # Input 32x32
            nn.Conv2d(7, 16, 3, stride=1, padding=1),
            nn.ELU(),
            nn.Dropout2d(0.1),
            nn.Conv2d(16, 24, 3, stride=1, padding=1),
            nn.ELU()
        )
        # Out 32x32

        # In 32x32
        self.encoder1 = nn.Sequential(
            nn.MaxPool2d(2),
            nn.Conv2d(24, 38, 3, stride=1, padding=1),
            nn.ELU(),
            nn.Conv2d(38, 42, 3, stride=1, padding=1),
            nn.ELU()
        )
        # Out 16x16

        # In 16x16
        self.encoder2 = nn.Sequential(
            nn.MaxPool2d(2), # 8x8
            nn.Conv2d(42, 64, 3, stride=1, padding=1),
            nn.ELU()
        )
        # Out 8x8

        # In 8x8
        self.decoder0 = nn.Sequential(
            nn.ConvTranspose2d(64, 42, 3, stride=1, padding=1), # 8x8
            nn.ELU(),
            nn.Upsample(scale_factor=2, mode="bilinear") # 16x16
        )
        # Out 16x16

        # In 16x16
        self.decoder1 = nn.Sequential(
            nn.ConvTranspose2d(84, 42, 3, stride=1, padding=1),
            nn.ELU(),
            nn.ConvTranspose2d(42, 24, 3, stride=1, padding=1),
            nn.ELU(),
            nn.Upsample(scale_factor=2, mode="bilinear") # 32x32
        )
        # Out 32x32

        # In 32x32
        self.decoder2 = nn.Sequential(
            nn.ConvTranspose2d(48, 24, 3, stride=1, padding=1),
            nn.ELU(),
            nn.ConvTranspose2d(24, 3, 3, stride=1, padding=1),
            nn.ELU()
        )
        # Out 32x32

    def forward(self, x):
        x0 = self.encoder0(x)
        x1 = self.encoder1(x0)
        x2 = self.encoder2(x1)

        x3 = self.decoder0(x2)
        x4 = self.decoder1(torch.cat((x3, x1), 1))
        x5 = self.decoder2(torch.cat((x4, x0), 1))
        return x5
