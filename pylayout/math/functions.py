from math import (trunc,
                  log10,
                  pi,
                  sqrt,
                  sin,
                  cos,
                  tan,
                  asin,
                  acos,
                  atan2)

#===================================================================================================

NORTH       = 1
NORTHEAST   = 2
EAST        = 3
SOUTHEAST   = 4
SOUTH       = 5
SOUTHWEST   = 6
WEST        = 7
NORTHWEST   = 8

def wrapangle(x,degrees=False):
    """ wrap angle value between [0, 2pi] (or [0, 180]) """
    if degrees:
        return (y + 180.0) % (2 * 180.0) - 180.0
    
    return (y + pi) % (2 * pi) - pi

def radians(x):
    """ convert from degrees to radians and wrap the result """
    y = x / 180.0 * pi
    return wrapangle(y)

def degrees(x):
    """ convert from radians to degrees and wrap the result """
    y = x / pi * 180.0
    return wrapangle(y,True)

def cardinal2angle(x):
    """ convert a cardinal direction to an angle in **degrees** """
    dirs = {
        NORTH       : 90.0,
        NORTHEAST   : 45.0,
        EAST        : 0.0,
        SOUTHEAST   : 315.0,
        SOUTH       : 270.0,
        SOUTHWEST   : 225.0,
        WEST        : 180.0,
        NORTHWEST   : 135.0
    }
    return dirs.get(x,lambda: error("invalid direction"))

def snap(x, grid):
    """ snap number to the nearest unit """
    return round(float(x) / grid) * grid

def clamp(x, a, b):
    """ clamp number to range [a,b] """
    return min(max(x, a), b)

# TODO: add interpolation functions (lerp, spline, nurb, bezier)