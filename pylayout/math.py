from types import LambdaType

import math

__all__ = (
    'wrap_angle',
    'pol_eval',
    'linspace',
    'circle_from_two_points',
    'circle_from_three_points',
    'Vec'
)

def wrap_angle(angle):
    """ wrap angle within 0 and 2*pi """
    _, i = math.modf(angle / (2*math.pi))
    a = angle - i*(2*math.pi)
    if a < 0:
        a += (2*math.pi)
    return a

def pol_eval(p, x) -> float:
    """ evaluate polynomial from coefficients p : p[0] + p[1]*x + p[2]*x**2 + ... """
    if not isinstance(p,(list,tuple)):
        p = [p]
    
    y = p[-1]
    for i in range(len(p)-2,-1,-1):
        y = p[i] + y*x
    return y

def linspace(a, b, n=100):
    """ return array of floats form a to b in n elements """
    dx = (b - a) / (n - 1)
    return [a + dx * i for i in range(int(n))]

def adaptlinspace(a, b, f: LambdaType, step=0.01):
    """ creates an adaptive linspace taking into account the local curvature of the function f """

    D = abs((f(b) - f(a)) / (b - a))

    X = []
    x = a
    h = (b - a) / 2
    while x + h < b:
        X.append(x)

        K = (f(x) - 2*f(x + h) + f(x + 2*h)) / h**2
        
        # TODO: include rounding tolerance to avoid duplicate y values?
        h = step**2 * D / abs(K)
        h = max(h, step)
        x = min(b, x + h)

    X.append(b)
    
    return X, [f(x) for x in X]

def cubic_bezier(p0, p1, p2, p3, t):
    """ evaluate cubic bezier curve from p0 to p3 at fraction t for control points p1 and p2 """
    return p0 * (1 - t)**3 + 3 * p1 * t*(1 - t)**2 + 3 * p2 * t**2*(1 - t) + p3 * t**3

def circle_from_two_points(p1, p2, r) -> tuple:
    """ find the center position of a circle of radius r going through the points in *ccw* direction """

    if r == 0:
        raise ValueError('radius must be differenct than zero')

    x1, y1 = p1
    x2, y2 = p2
    dx = x2 - x1
    dy = y2 - y1
    h = math.sqrt(dx**2 + dy**2)
    if h > 2*r:
        raise ValueError('both points are more distant than any circle of diameter given!')
    
    x3, y3 = (x1 + x2)/2, (y1 + y2)/2
    d = math.sqrt(r**2 - (h/2)**2)

    return (x3 - d*dy/h, y3 + d*dx/h)

def circle_from_three_points(p1, p2, p3):
    """ find the center position and radius of the circle going through all three points """

    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3

    a = x2 - x1
    c = x3 - x1
    d = y2 - y1
    e = y3 - y1
    f = x1**2 - x2**2
    g = x1**2 - x3**2
    h = y1**2 - y2**2
    i = y1**2 - y3**2

    y = -1/2*(g + i + f*c/a + h*c/a)/(e - c*d/a)
    x = 1/2*f/a + 1/2*h/a - d/a*y
    r = math.sqrt((x1 - x)**2 + (y1 - y)**2)

    return (x, y), r


class Vec:
    """ 2-Dimensional double-precision float vector to simplify arithmetic """
    EPSILON = 1e-9
    __slots__ = ('__xy')
    def __init__(self, x=0, y=0):
        self.__xy = [0,0]
        if isinstance(x, (list, tuple, Vec)):
            self.__xy[0] = x[0]
            self.__xy[1] = x[1]
        else:
            self.__xy[0] = x
            self.__xy[1] = y

    @property
    def x(self):
        return self.__xy[0]

    @x.setter
    def x(self, value):
        self.__xy[0] = value

    @property
    def y(self):
        return self.__xy[1]

    @y.setter
    def y(self, value):
        self.__xy[1] = value

    def set(self, x, y):
        self.__xy[0] = x
        self.__xy[1] = y
    
    def __getitem__(self, key):
        assert key in [0, 1]
        return self.__xy[key]

    def __setitem__(self, key, value):
        assert key in [0, 1]
        self.__xy[key] = value

    def __len__(self):
        return 2

    def __iter__(self):
        yield self.__xy[0]
        yield self.__xy[1]

    def __add__(self, v):
        return Vec(self.__xy[0] + v[0], self.__xy[1] + v[1])

    def __sub__(self, v):
        return Vec(self.__xy[0] - v[0], self.__xy[1] - v[1])

    def __mul__(self, h):
        return Vec(self.__xy[0] * h, self.__xy[1] * h)
    
    def __truediv__(self, h):
        return Vec(self.__xy[0] / h, self.__xy[1] / h)

    def __radd__(self, v):
        return Vec(self.__xy[0] + v[0], self.__xy[1] + v[1])

    def __rsub__(self, v):
        return Vec(self.__xy[0] - v[0], self.__xy[1] - v[1])

    def __rmul__(self, h):
        return Vec(self.__xy[0] * h, self.__xy[1] * h)
    
    def __iadd__(self, v):
        self.__xy[0] += v[0]
        self.__xy[1] += v[1]
        return self

    def __isub__(self, v):
        self.__xy[0] -= v[0]
        self.__xy[1] -= v[1]
        return self

    def __imul__(self, h):
        self.__xy[0] *= h
        self.__xy[1] *= h
        return self
    
    def __itruediv__(self, h):
        self.__xy[0] /= h
        self.__xy[1] /= h
        return self

    def __neg__(self):
        return Vec(-self.__xy[0], -self.__xy[1])
    
    def __pos__(self):
        return Vec(self.__xy[0], self.__xy[1])

    def length2(self):
        return self.__xy[0]**2 + self.__xy[1]**2

    def length(self):
        return math.sqrt(self.length2())
    
    def normalize(self):
        h = max(self.EPSILON, self.length())
        self.__xy[0] /= h
        self.__xy[1] /= h
        return self
    
    def dot(self, v):
        return self.__xy[0] * v[0] + self.__xy[1] * v[1]
    
    def angle(self, asdegrees=False):
        angle = math.atan2(self.__xy[1], self.__xy[0])
        return angle if not asdegrees else math.degrees(angle)

    def colinear(self, v):
        return abs(v.dot(self)) > self.EPSILON

    def rotate(self, angle):
        x = self.__xy[0] * math.cos(angle) - self.__xy[1] * math.sin(angle)
        y = self.__xy[0] * math.sin(angle) + self.__xy[1] * math.cos(angle)
        self.set(x, y)
        return self