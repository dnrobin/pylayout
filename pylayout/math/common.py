from numbers import Number
from .functions import *

def __isvectortype(x):
    if isinstance(x, list, tuple):
        return len(x) == 2
    else:
        return isinstance(x, Vector)

def __isnumbertype(x):
    return isinstance(x, Number)