from math import (isclose,
                  trunc,
                  log10,
                  pi,
                  sqrt,
                  sin,
                  cos,
                  tan,
                  asin,
                  acos,
                  atan2)

DIRECTIONS  = ['e','ne','n','nw','w','sw','s','se']
EAST        = 0
NORTHEAST   = 1
NORTH       = 2
NORTHWEST   = 3
WEST        = 4
SOUTHWEST   = 5
SOUTH       = 6
SOUTHEAST   = 7

def __isnumbertype(x):
    import numbers
    return isinstance(x, numbers.Number)

#===================================================================================================
# General purpose
#===================================================================================================

def sgn(x):
    """ returns the sign of a number """
    if x < 0: return -1
    if x > 0: return +1
    return 0

def snap(x, unit):
    """ snap number to the nearest grid unit """
    return round(float(x) / unit) * unit

def clamp(x, a, b):
    """ clamp number to range [a,b] """
    return min(max(x, a), b)

#===================================================================================================
# Angles and directions
#===================================================================================================

def wrapangle(x,degrees=False):
    """ wrap angle value between [0, 2pi] (or [0, 180]) """
    if degrees:
        return (x + 180.0) % (2 * 180.0) - 180.0
    
    return (x + pi) % (2 * pi) - pi

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

    if isinstance(x, str):
        dirs = {DIRECTIONS[i] : 45.0 * i for i in range(len(DIRECTIONS))}
    else:
        dirs = {i : 45.0 * i for i in range(len(DIRECTIONS))}

    return dirs.get(x,lambda: error("invalid direction"))

#===================================================================================================
# Distances and intersections
#===================================================================================================

def distance_to_point(p0, p):
    """ returns the distance from p0 to point p """
    x1, y1 = p0
    x2, y2 = p

    return sqrt((x1 - x2)**2 + (y1 - y2)**2)

def distance_to_line(p0, p1, p2):
    """ returns the distance from p0 to point the line defined by points p1 and p2 """
    d = distance_to_point(p1, p2)
    if d == 0:
        raise ValueError("points on line must be distinct!")

    x1, y1 = p1
    x2, y2 = p2

    a = y1 - y2
    b = x2 - x1
    c = x1*y2 - x2*y1

    return abs(a*p0[0] + b*p0[1] + c) / d

def distance_to_circle(p0, c0, r):
    """ return the distance from p0 to the edge of the circle of radius r centered at c0
    
    Note: a negative distance implies the point is inside the circle
    """
    return distance_to_point(p0, c0) - r

def distance_to_set(p0, points: list):
    """ returns the distance from p0 to the nearest point in the set """
    return min([distance_to_point(p0, p) for p in points])

def line_distance_to_circle(p1, p2, c0, r):
    pass

def line_distance_to_set(p1, p2, points: list):
    pass

def point_on_line(p0, p1, p2, tol=1e-3) -> bool:
    pass

def point_on_circle(p0, c0, r, tol=1e-3) -> bool:
    pass

def line_intersects_line(p1, p2, c0, r, tol=1e-3) -> bool:
    """ returns 1 if the line defined by points p1 and p2 intersects the circle or radius r centered at c0 """
    pass

def line_intersects_circle(p1, p2, c0, r, tol=1e-3) -> bool:
    """ returns 1 if the line defined by points p1 and p2 intersects the circle or radius r centered at c0 """
    pass

def circle_intersects_circle(p1, p2, c0, r, tol=1e-3) -> bool:
    """ returns 1 if the line defined by points p1 and p2 intersects the circle or radius r centered at c0 """
    pass

# TODO: add testing for point, line, circle and arbitrary shape with *Bounds*

def colinear(p1, p2, p3, tol=1e-3) -> bool:
    """ check if three points are colinear """
    return isclose(0, p1[0] * (p2[1] - p3[1]) + p2[0] * (p3[1] - p1[1]) + p3[0] * (p1[1] - p2[1]), abs_tol=tol)

def spin(p1, p2, p3) -> int:
    """ check if sequence of three points are going in a cw or ccw direction 
    
    Return:
        -1 - counterclockwise
         0 - colinear
        +1 - clockwise
    """
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3

    return sgn(float(y2 - y1) * (x3 - x2) 
             - float(y3 - y2) * (x2 - x1))

def circle_from_two_points(p1, p2, r):
    """ compute the two possible circle centers from two points on the circle """
    if r <= 0:
        raise ValueError('radius must be greater than zero')
    
    h = distance_to_point(p1, p2)
    if h > 2*r:
        raise ValueError('points must be closer that the desired circle diameter')

    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = (x1 + x2)/2, (y1 + y2)/2

    dx = x2 - x1
    dy = y2 - y1
    d = sqrt(r**2 - (h/2)**2)

    return [(x3 - d*dy/h, y3 + d*dx/h), (x3 + d*dy/h, y3 - d*dx/h)]

#===================================================================================================
# Interpolation
#===================================================================================================

def lerp(a, b, p: float):
    """ linear interpolation between a and b by parameter p in [0, 1] """
    assert isinstance(p, (int, float))
    p = clamp(p, 0.0, 1.0)
    return (1 - p) * a + p * b

def bezier(p0, p1, p2, r, b, tol=1e-2):
    """ generate bezier curve with radius r and parameter b interpolating three points """
    from .vector import Vector

    p1 = Vector(p1)
    v1 = (Vector(p0) - p1).normalize()
    v2 = (Vector(p2) - p1).normalize()

    a = p1 + v1 * r
    b = p1 + v1 * r*b
    c = p1 + v2 * r*b
    d = p1 + v2 * r

    n = round(1/tol)
    dt = 1 / (n - 1)
    xy = []
    for i in range(n):
        t = i * dt
        p = a*(1-t)**3 + b*3*(1-t)**2*t + c*3*(1-t)*t**2 + d*t**3
        xy.append(p)

    return xy