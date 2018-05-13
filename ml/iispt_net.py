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
            nn.Conv2d(7, 24, 3, stride=1, padding=1),
            nn.ELU(),
            nn.Dropout2d(0.2),
            nn.Conv2d(24, 64, 3, stride=1, padding=1),
            nn.ELU(),
            nn.Dropout2d(0.2)
        )
        # Out 32x32

        # In 32x32
        self.encoder1 = nn.Sequential(
            nn.MaxPool2d(2),
            nn.Conv2d(64, 72, 3, stride=1, padding=1),
            nn.ELU(),
            nn.Dropout2d(0.2),
            nn.Conv2d(72, 84, 3, stride=1, padding=1),
            nn.ELU(),
            nn.Dropout2d(0.2)
        )
        # Out 16x16

        # In 16x16
        self.encoder2 = nn.Sequential(
            nn.MaxPool2d(2), # 8x8
            nn.Conv2d(84, 112, 3, stride=1, padding=1),
            nn.ELU(),
            nn.Dropout2d(0.2)
        )
        # Out 8x8

        # In 8x8
        self.encoder3 = nn.Sequential(
            nn.MaxPool2d(2),
            nn.Conv2d(112, 256, 3, stride=1, padding=1),
            nn.ELU(),
            nn.Dropout2d(0.2)
        )
        # Out 4x4

        # In 4x4
        self.decoder0 = nn.Sequential(
            nn.Conv2d(256, 112, 3, stride=1, padding=1),
            nn.ELU(),
            nn.Upsample(scale_factor=2, mode="bilinear")
        )
        # Out 8x8

        # In 8x8
        self.decoder1 = nn.Sequential(
            nn.Conv2d(224, 84, 3, stride=1, padding=1), # 8x8
            nn.ELU(),
            nn.Upsample(scale_factor=2, mode="bilinear") # 16x16
        )
        # Out 16x16

        # In 16x16
        self.decoder2 = nn.Sequential(
            nn.Conv2d(168, 72, 3, stride=1, padding=1),
            nn.ELU(),
            nn.Dropout2d(0.2),
            nn.Conv2d(72, 64, 3, stride=1, padding=1),
            nn.ELU(),
            nn.Upsample(scale_factor=2, mode="bilinear") # 32x32
        )
        # Out 32x32

        # In 32x32
        self.decoder3 = nn.Sequential(
            nn.Conv2d(128, 36, 3, stride=1, padding=1),
            nn.ELU(),
            nn.Dropout2d(0.2),
            nn.Conv2d(36, 16, 3, stride=1, padding=1),
            nn.ELU(),
            nn.Conv2d(16, 3, 3, stride=1, padding=1),
            nn.ELU()
        )
        # Out 32x32

    def forward(self, x):
        x0 = self.encoder0(x)
        x1 = self.encoder1(x0)
        x2 = self.encoder2(x1)
        x3 = self.encoder3(x2)

        x4 = self.decoder0(x3)
        x5 = self.decoder1(torch.cat((x4, x2), 1))
        x6 = self.decoder2(torch.cat((x5, x1), 1))
        x7 = self.decoder3(torch.cat((x6, x0), 1))

        return x7
