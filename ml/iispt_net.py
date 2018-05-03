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
            nn.Conv2d(7, 16, 3, stride=1, padding=1),
            nn.LeakyReLU(0.1),

            nn.Conv2d(16, 32, 3, stride=1, padding=1),
            nn.LeakyReLU(0.1),

            nn.AvgPool2d(2), # 16x16

            nn.Conv2d(32, 34, 3, stride=1, padding=1),
            nn.LeakyReLU(0.1),

            nn.Conv2d(34, 36, 3, stride=1, padding=1),
            nn.LeakyReLU(0.1),

            nn.AvgPool2d(2), # 8x8

            nn.Conv2d(36, 40, 3, stride=1, padding=1),
            nn.LeakyReLU(0.1),

            nn.Conv2d(40, 64, 3, stride=1, padding=1),
            nn.LeakyReLU(0.1)
        )

        self.decoder = nn.Sequential(

            nn.ConvTranspose2d(64, 40, 3, stride=1, padding=1), # 8x8
            nn.LeakyReLU(0.1),

            nn.ConvTranspose2d(40, 36, 3, stride=1, padding=1),
            nn.LeakyReLU(0.1),

            nn.Upsample(scale_factor=2), # 16x16

            nn.ConvTranspose2d(36, 34, 3, stride=1, padding=1),
            nn.LeakyReLU(0.1),

            nn.ConvTranspose2d(34, 32, 3, stride=1, padding=1),
            nn.LeakyReLU(0.1),

            nn.Upsample(scale_factor=2), # 32x32

            nn.ConvTranspose2d(32, 16, 3, stride=1, padding=1),
            nn.LeakyReLU(0.1),

            nn.ConvTranspose2d(16, 3, 3, stride=1, padding=1)
        )

    def forward(self, x):
        x = self.encoder(x)
        x = self.decoder(x)
        return x
