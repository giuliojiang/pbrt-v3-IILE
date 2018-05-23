import math
import numpy

# =============================================================================
# Efficient Numpy based transforms

def npDivide(data, amount):
    if amount > 0.0:
        return data / amount
    else:
        return data

def npLog(data):
    data = data + 1.0
    data = numpy.clip(data, 1.0, None)
    data = numpy.log(data)
    return data

def npSub(data, amount):
    return data - amount

def npNormalize(data, minV, maxV):
    mid = (maxV + minV) / 2.0
    r = maxV - mid
    data = data - mid
    if r > 0.0:
        data = data / r
    data = numpy.clip(data, -1.0, 1.0)
    return data

def npAdd(data, amount):
    return data + amount

# =============================================================================
# Augmentations
def augmentList(thePfms, aug):

    for aPfm in thePfms:

        # Perform data augmentation: flipping
        flipIndex = int(aug / 4)
        if flipIndex == 0:
            # No flip
            pass
        elif flipIndex == 1:
            # Vertical flip
            aPfm.vflip()
        elif flipIndex == 2:
            # Horizontal flip
            aPfm.hflip()
        elif flipIndex == 3:
            # Vertical and horizontal flip
            aPfm.vflip()
            aPfm.hflip()
        else:
            raise Exception("Unknown flip index {} from aug index {}".format(flipIndex, aug))

        # Perform data augmentation: rotation
        rotationIndex = int(aug % 4)
        if rotationIndex == 0:
            # No rotation
            pass
        elif rotationIndex == 1:
            # 90
            aPfm.rotate(1)
        elif rotationIndex == 2:
            # 180
            aPfm.rotate(2)
        elif rotationIndex == 3:
            # 270
            aPfm.rotate(3)
        else:
            raise Exception("Unknown rotation index {} from aug index {}".format(rotationIndex, aug))

# =============================================================================
# Math wrappers

def safelog(x):
    if x <= 1.0:
        return 0.0
    else:
        return math.log(x)

def safesqrt(x):
    if x <= 0.0:
        return 0.0
    else:
        return math.sqrt(x)

# =============================================================================
# Transform callables

# -----------------------------------------------------------------------------
# Normalization into [-1,+1] range
class NormalizeTransform:

    def __init__(self, min_val, max_val):
        self.min_val = min_val
        self.max_val = max_val
    
    def __call__(self, x):
        mid = (self.max_val + self.min_val) / 2.0
        r = self.max_val - mid
        x = x - mid
        x = x / r
        if x < -1.0:
            return -1.0
        elif x > 1.0:
            return 1.0
        else:
            return x

# -----------------------------------------------------------------------------
# Normalization into [0,+1] range

class NormalizePositiveTransform:

    def __init__(self, min_val, max_val):
        self.min_val = min_val
        self.max_val = max_val

    def __call__(self, x):
        d = self.max_val - self.min_val
        if d <= 0.0: # Degenerate range!
            return 0.0
        x = x - self.min_val
        x = x / d
        if x < 0.0:
            return 0.0
        elif x > 1.0:
            return 1.0
        else:
            return x

class NormalizeInvTransform:

    def __init__(self, max_val):
        self.max_val = max_val
    
    def __call__(self, x):
        return x * self.max_val

# -----------------------------------------------------------------------------

class LogTransform:

    def __init__(self):
        pass
    
    def __call__(self, x):
        return safelog(x + 1.0)

class LogInvTransform:

    def __init__(self):
        pass
    
    def __call__(self, y):
        if y < 0.0:
            y = 0.0
        return math.exp(y) - 1.0

# -----------------------------------------------------------------------------
class SqrtTransform:

    def __init__(self):
        pass
    
    def __call__(self, x):
        return safesqrt(x)

# -----------------------------------------------------------------------------
class GammaTransform:

    def __init__(self, gm):
        self.exponent = 1.0 / gm
    
    def __call__(self, x):
        if x < 0.0:
            x = 0.0
        return x ** self.exponent

# -----------------------------------------------------------------------------
class Divide:

    def __init__(self, amount):
        self.amount = amount
    
    def __call__(self, x):
        if self.amount == 0.0:
            return x
        else:
            return x / self.amount

# -----------------------------------------------------------------------------
class Multiply:

    def __init__(self, amount):
        self.amount = amount

    def __call__(self, x):
        return x * self.amount

# -----------------------------------------------------------------------------
class Add:

    def __init__(self, amount):
        self.amount = amount

    def __call__(self, x):
        return x + self.amount

# -----------------------------------------------------------------------------
class Subtract:

    def __init__(self, amount):
        self.amount = amount
    
    def __call__(self, x):
        return x - self.amount

# -----------------------------------------------------------------------------
class LinearLDR:

    def __init__(self, exposure, gamma):
        self.exposure = exposure
        self.gamma = gamma
    
    def __call__(self, x):
        x *= 2.0**self.exposure
        if x < 0.0:
            x = 0.0
        if x > 1.0:
            x = 1.0
        x = x**(1.0 / self.gamma)
        return int(255.0 * x)

# -----------------------------------------------------------------------------
class Sequence:

    def __init__(self, ts):
        self.ts = ts
    
    def __call__(self, x):
        for t in self.ts:
            x = t(x)
        return x

# -----------------------------------------------------------------------------
# log, normalize+, gamma

class IntensitySequence:

    def __init__(self, max_value, gamma):
        ts = []
        ts.append(LogTransform())
        ts.append(NormalizePositiveTransform(0.0, max_value))
        ts.append(GammaTransform(gamma))
        self.seq = Sequence(ts)
    
    def __call__(self, x):
        return self.seq(x)

class IntensityInvSequence:

    def __init__(self, max_value, gamma):
        ts = []
        ts.append(GammaTransform(1.0 / gamma))
        ts.append(NormalizeInvTransform(max_value))
        ts.append(LogInvTransform())
        self.seq = Sequence(ts)
    
    def __call__(self, x):
        return self.seq(x)

# -----------------------------------------------------------------------------
# sqrt, normalize+, gamma
class DistanceSequence:

    def __init__(self, max_value, gamma):
        ts = []
        ts.append(SqrtTransform())
        ts.append(NormalizePositiveTransform(0.0, max_value))
        ts.append(GammaTransform(gamma))
        self.seq = Sequence(ts)
    
    def __call__(self, x):
        return self.seq(x)

# -----------------------------------------------------------------------------
class IntensityDownstreamFullSequence:

    def __init__(self, mean):
        ts = []
        ts.append(Divide(10.0 * mean))
        ts.append(LogTransform())
        ts.append(Subtract(0.1))
        self.seq = Sequence(ts)
    
    def __call__(self, x):
        return self.seq(x)

# -----------------------------------------------------------------------------
class IntensityDownstreamHalfSequence:

    def __init__(self, mean):
        ts = []
        ts.append(Divide(10.0 * mean))
        ts.append(LogTransform())
        self.seq = Sequence(ts)
    
    def __call__(self, x):
        return self.seq(x)

# -----------------------------------------------------------------------------
class IntensityUpstreamSequence:

    def __init__(self, mean):
        ts = []
        ts.append(LogInvTransform())
        ts.append(Multiply(10.0 * mean))
        self.seq = Sequence(ts)
    
    def __call__(self, x):
        return self.seq(x)

# -----------------------------------------------------------------------------
class DistanceDownstreamSequence:

    def __init__(self, mean):
        ts = []
        ts.append(Add(1.0))
        ts.append(Divide(10.0 * (mean + 1.0)))
        ts.append(LogTransform())
        ts.append(Subtract(0.1))
        self.seq = Sequence(ts)
    
    def __call__(self, x):
        return self.seq(x)