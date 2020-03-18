import os
import numpy
import math
import numbers

DIRECTIONS = ['e', 'ne', 'n', 'nw', 'w', 'sw', 's', 'se']

def isnumeric(obj):
    return isinstance(obj, numbers.Number)

def isvector(obj):
    return (not hasattr(obj, "strip") and
            hasattr(obj, "__getitem__") or
            hasattr(obj, "__iter__"))

def clamp(x, a, b):
    return min(max(x, a), b)

def compas_dir_from_angle(angle: float, tol=1e-2):
    angle = numpy.angle(numpy.exp(1j*angle))
    if abs(angle) < tol:
        return 'e'
    elif abs(abs(angle) - 1*math.pi/4) < tol:
        return 'ne' if angle > 0 else 'se'
    elif abs(abs(angle) - 2*math.pi/4) < tol:
        return 'n' if angle > 0 else 's'
    elif abs(abs(angle) - 3*math.pi/4) < tol:
        return 'nw' if angle > 0 else 'sw'
    elif abs(abs(angle) - 4*math.pi/4) < tol:
        return 'w'
    elif abs(abs(angle) - 5*math.pi/4) < tol:
        return 'sw' if angle > 0 else 'nw'
    elif abs(abs(angle) - 6*math.pi/4) < tol:
        return 's' if angle > 0 else 'n'
    elif abs(abs(angle) - 7*math.pi/4) < tol:
        return 'se' if angle > 0 else 'ne'
    return 'o'

def nearest_compas_dir(angle: float) -> str:
    """ round angle in *radians* to the nearest direction in ['e', 'ne', 'n', 'nw', 'w', 'sw', 's', 'se'] and return string """
    nearest = round(angle / (math.pi/4)) * math.pi/4
    return compas_dir_from_angle(nearest)

def compas_direction_to_radians(direction: str) -> float:
    """ convert one of ['e', 'ne', 'n', 'nw', 'w', 'sw', 's', 'se'] to an angle in *radians* """
    assert direction in DIRECTIONS
    angles = [0.0, 1*math.pi/4, 2*math.pi/4, 3*math.pi/4, 4*math.pi/4, 5*math.pi/4, 6*math.pi/4, 7*math.pi/4]
    return angles[DIRECTIONS.index(direction)]

def compas_direction_to_degrees(direction: str) -> float:
    """ convert one of ['e', 'ne', 'n', 'nw', 'w', 'sw', 's', 'se'] to an angle in *degrees* """
    return math.degrees(compas_direction_to_radians(direction))

def direction_angle(obj) -> float:
    """ get angle in *degrees* from direction string or vector components """
    if isvector(obj) and len(obj) == 2:
        return math.degrees(math.atan2(obj[1], obj[0]))
    if isinstance(obj, str):
        return compas_direction_to_degrees(obj)
    assert isnumeric(obj)
    return float(obj)

def get_lambda_expr(l):
    """ extract expression string from lambda function """
    import re, inspect
    s = inspect.getsource(l)
    i = s.find('lambda')
    j = re.search(':[^,)]*', s[i:]).span()
    return s[i+j[0]+1:i+j[1]].strip()

def colin(p1, p2, p3, tolerance=1e-3):
    """ check if three points are colinear based on the triangle they form """
    return math.isclose(0, p1[0] * (p2[1] - p3[1]) + p2[0] * (p3[1] - p1[1]) + p3[0] * (p1[1] - p2[1]), abs_tol=tolerance)

def circle_from_two_points(p1, p2, r):
    """ compute the two possible circle centers from two points on the circle """
    if r == 0:
        raise ValueError('radius must be differenct than zero')

    x1, y1 = p1
    x2, y2 = p2
    dx = x2 - x1
    dy = y2 - y1
    h = sqrt(dx**2 + dy**2)
    if h > 2*r:
        raise ValueError('both points are more distant than any circle of diameter given!')
    
    x3, y3 = (x1 + x2)/2, (y1 + y2)/2
    d = sqrt(r**2 - (h/2)**2)
    return [(x3 - d*dy/h, y3 + d*dx/h), (x3 + d*dy/h, y3 - d*dx/h)]

def bezier_corner(p0, p1, p2, radius, bezier, tolerance=1e-2):
    """ generate points interpolating a cubic bezier bend for corner point p0 and two other points along the path """

    p0 = Vec(p0)
    v1 = (Vec(p1) - p0).normalize()
    v2 = (Vec(p2) - p0).normalize()

    a = p0 + v1 * radius
    b = p0 + v1 * radius*bezier
    c = p0 + v2 * radius*bezier
    d = p0 + v2 * radius

    n = round(1/tolerance)
    dt = 1 / (n - 1)
    xy = []
    for i in range(n):
        t = i * dt
        p = a*(1-t)**3 + b*3*(1-t)**2*t + c*3*(1-t)*t**2 + d*t**3
        xy.append(p.array())

    return xy

def unique_name_for(name, dict):
    unique_name = name

    i = 0
    while unique_name in dict:
        i += 1
        unique_name = name + '_' + str(i)
    
    return unique_name