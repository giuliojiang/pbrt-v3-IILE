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
            # If input is 7 layers, 32x32
            nn.Conv2d(7, 16, 3, stride=1, padding=1),
            nn.ReLU(True),
            nn.MaxPool2d(2), # 16 layers, 16x16
            nn.Conv2d(16, 8, 3, stride=1, padding=1),
            nn.ReLU(True),
            nn.MaxPool2d(2) # 8 layers, 8x8
        )

        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(8, 16, 3, stride=1, padding=1), # 16 8x8
            nn.ELU(),
            nn.Upsample(scale_factor=2), # 16 16x16
            nn.ConvTranspose2d(16, 8, 3, stride=1, padding=1), # 8 16x16
            nn.ELU(),
            nn.Upsample(scale_factor=2), # 8 32x32
            nn.ConvTranspose2d(8, 3, 3, stride=1, padding=1), # 3 32x32
            nn.ELU()
            

            # nn.ConvTranspose2d(8, 16, 3),
            # nn.ReLU(True),
            # nn.ConvTranspose2d(16, 8, 3),
            # nn.ReLU(True),
            # nn.ConvTranspose2d(8, 3, 3),
            # nn.Tanh()
        )

    def forward(self, x):
        x = self.encoder(x)
        x = self.decoder(x)
        return x
