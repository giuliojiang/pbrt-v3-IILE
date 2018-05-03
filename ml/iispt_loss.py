import torch
from torch import nn
from torch import functional as F

class IisptLoss(torch.nn.Module):
    def __init__(self, size_average=True):
        super(IisptLoss, self).__init__()
        self.size_average = size_average

def pointwiseLoss(lambd, input, target, size_average=True, reduce=True):
    d = lambd(input, target)
    if not reduce:
        return d
    return torch.mean(d) if size_average else torch.sum(d)

def relMSELoss(input, target, eps, size_average=True, reduce=True):
    return pointwiseLoss(
        lambda a, b: ((a - b)**2.0 / (a**2.0 + eps)),
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