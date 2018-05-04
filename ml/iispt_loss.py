import torch
from torch import nn
from torch import functional as F
import math

class IisptLoss(torch.nn.Module):
    def __init__(self, size_average=True):
        super(IisptLoss, self).__init__()
        self.size_average = size_average

def pointwiseLoss(lambd, input, target, size_average=True, reduce=True):
    d = lambd(input, target)
    if not reduce:
        return d
    return torch.mean(d) if size_average else torch.sum(d)

# =============================================================================

def relMSELoss(input, target, eps, size_average=True, reduce=True):
    return pointwiseLoss(
        lambda a, b: (((a - b)**2.0) / ((a**2.0) + eps)),
        input,
        target,
        size_average,
        reduce
    )

class RelMSELoss(IisptLoss):

    def __init__(self, eps=0.0001, size_average=True, reduce=True):
        super(RelMSELoss, self).__init__(size_average)
        self.reduce = reduce
        self.eps = eps
    
    def forward(self, input, target):
        return relMSELoss(input, target, self.eps, size_average=self.size_average, reduce=self.reduce)

# =============================================================================

def l1Func(a, b):
    return torch.abs(a - b)

def l1Loss(input, target, size_average=True, reduce=True):
    return pointwiseLoss(
        l1Func,
        input,
        target,
        size_average,
        reduce
    )

class L1Loss(IisptLoss):

    def __init__(self, size_average=True, reduce=True):
        super(L1Loss, self).__init__(size_average)
        self.reduce = reduce
    
    def forward(self, input, target):
        return l1Loss(input, target, size_average=self.size_average, reduce=self.reduce)

# =============================================================================

def relL1Func(a, b):
    return (torch.abs(a - b)) / (a + 0.00001)

def relL1Loss(input, target, size_average=True, reduce=True):
    return pointwiseLoss(
        relL1Func,
        input,
        target,
        size_average,
        reduce
    )

class RelL1Loss(IisptLoss):

    def __init__(self, size_average=True, reduce=True):
        super(RelL1Loss, self).__init__(size_average)
        self.reduce = reduce
    
    def forward(self, input, target):
        return relL1Loss(input, target, size_average=self.size_average, reduce=self.reduce)