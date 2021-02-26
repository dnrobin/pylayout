from types import LambdaType

import math, numbers

__all__ = (
    'isnumber',
    'wrapangle',
    'pol_eval',
    'linspace',
    'adaptlinspace',
    'circle_from_two_points',
    'circle_from_three_points',
    'cubic_bezier',
    'Vec',
    'Transform'
    'Range',
    'BoundingBox'
)

def isnumber(type):
    return isinstance(type, numbers.Number)

def wrapangle(angle):
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
    """ Vector 2-D for convenient vector arithmetic oprtations
    
    Supports vector arithmetic and transformations used to represent points in 2D
    space like coordinates or polygon vertices, but also directional vectors.

    input:
        x - float value for x-coordinate or list/tuple/Vec for initialisation
        y - float value for y-coordinate or None
    """
    EPSILON = 1e-9
    __slots__ = ('__xy')
    def __init__(self, x=0, y=0):
        self.__xy = [0,0]
        if isinstance(x, (list, tuple, Vec)):
            self.__xy[0] = x[0]
            self.__xy[1] = x[1]
        else:
            self.__xy[0] = x
            if y is None:
                self.__xy[1] = x
            else:
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


class Range:
    """
        Value range construct for set theoretic operations
    """
    __slots__ = ('a', 'b')
    def __init__(self, a=math.nan, b=math.nan):
        self.a = a
        self.b = b

    @property
    def min(self):
        """ get minimum value of range [a,b] """
        return self.a

    @property
    def max(self):
        """ get maximum value of range [a,b] """
        return self.b

    @property
    def center(self):
        """ get center value (mean) of range [a,b] """
        return (self.a + self.b) / 2

    @property
    def extent(self):
        """ get extent (length) of range [a,b] """
        return self.b - self.a

    def __str__(self):
        return f"Range({self.a},{self.b})"
    
    def __gt__(self, x):
        if type(x) is Range:
            return self.a > self.b
        return self.a > x

    def __lt__(self, x):
        if type(x) is Range:
            return self.b < self.a
        return self.b < x

    def __ge__(self, x):
        if type(x) is Range:
            return self.a >= self.b
        return self.a >= x

    def __le__(self, x):
        if type(x) is Range:
            return self.b <= self.a
        return self.b <= x

    def __iter__(self):
        yield self.a
        yield self.b

    def includes(self, value):
        """ returns true if other is included in range [a,b] """
        # TODO: compare within tolerance radius
        if isinstance(value, Range):
            return value.a >= self.a and value.b <= self.b

        assert isnumber(value)
        return value >= self.a and value <= self.b

    def excludes(self, value):
        """ returns true if other is strictly outside range [a,b] """
        return not self.include(value)

    def distance(self, value):
        """ compute the absolute distance between value and range [a,b] """
        if value < self.a:
            if isinstance(value, Range):
                return self.a - max(value)
            return self.a - value

        elif value > self.b:
            if isinstance(value, Range):
                return min(value) - self.b
            return value - self.b

        return 0

    def include(self, value):
        """ stretch range (if necessary) to include value """
        if math.isnan(self.a):
            if isinstance(value, Range):
                self.a = value.a
            else:
                assert isnumber(value)
                self.a = value

        if math.isnan(self.b):
            if isinstance(value, Range):
                self.b = value.b
            else:
                assert isnumber(value)
                self.b = value

        if isinstance(value, Range):
            if value.a < self.a: self.a = value.a
            if value.b > self.b: self.b = value.b

        else:
            assert isnumber(value)
            if value < self.a: self.a = value
            if value > self.b: self.b = value

        return self

    def bound(self, values):
        """ adjust range to bound set of values """
        self.a = math.nan
        self.b = math.nan
        
        for value in values:
            self.include(value)
        
        return self


class BoundingBox:
    """ Axis aligned bounding box construct for set theoretic operations on points """
    __slots__ = ('__xrange', '__yrange')
    def __init__(self, xmin=math.nan, xmax=math.nan, ymin=math.nan, ymax=math.nan):
        self.__xrange = Range(xmin, xmax)
        self.__yrange = Range(ymin, ymax)

    def __str__(self):
        return f"BoundingBox(ll:({self.__xrange.min},{self.__yrange.min}), ur:({self.__xrange.max},{self.__yrange.max}))"

    @property
    def xmin(self):
        """ get minimum x value """
        return self.__xrange.min

    @property
    def xmax(self):
        """ get maximum x value """
        return self.__xrange.max

    @property
    def ymin(self):
        """ get minimum y value """
        return self.__yrange.min

    @property
    def ymax(self):
        """ get maximum y value """
        return self.__yrange.max

    @property
    def xrange(self):
        """ extract x range as Range() """
        return self.__xrange

    @property
    def yrange(self):
        """ extract y range as Range() """
        return self.__yrange
    
    @property
    def center(self):
        """ get the center point """
        return Vec(self.__xrange.center, self.__yrange.center)
    
    @property
    def left(self):
        """ get the left center point """
        return Vec(self.__xrange.min, self.__yrange.center)
    
    @property
    def right(self):
        """ get the right center point """
        return Vec(self.__xrange.max, self.__yrange.center)
    
    @property
    def top(self):
        """ get the top center point """
        return Vec(self.__xrange.center, self.__yrange.max)
    
    @property
    def bottom(self):
        """ get the bottom center point """
        return Vec(self.__xrange.center, self.__yrange.min)
    
    @property
    def ll(self):
        """ get the lower left corner point """
        return Vec(self.__xrange.min, self.__yrange.min)
    
    @property
    def lr(self):
        """ get the lower right corner point """
        return Vec(self.__xrange.max, self.__yrange.min)
    
    @property
    def ul(self):
        """ get the upper left corner point """
        return Vec(self.__xrange.min, self.__yrange.max)

    @property
    def ur(self):
        """ get the upper right corner point """
        return Vec(self.__xrange.max, self.__yrange.max)

    @property
    def width(self):
        """ get the box width """
        return self.__xrange.extent
    
    @property
    def height(self):
        """ get the box height """
        return self.__yrange.extent

    @property
    def size(self):
        """ return the x and y dimension tuple """
        return (self.width, self.height)
    
    @property
    def area(self):
        """ obtain the box area """
        return self.width * self.height

    def include(self, point):
        """ resize box (if necessary) to include point """
        if isinstance(point, BoundingBox):
            self.__xrange.include(point.xrange)
            self.__yrange.include(point.yrange)
        
        else:
            self.__xrange.include(point[0])
            self.__yrange.include(point[1])

        return self

    def bound(self, points):
        """ adjust box to bound a set of points """
        self.__xrange = Range()
        self.__yrange = Range()
        for point in points:
            self.include(point)

        return self
    
    def includes(self, other):
        # TODO: true if completely inside
        pass

    def overlaps(self, other):
        # TODO: true if partly inside or completely inside
        pass

    def excludes(self, other):
        # TODO: true if completely outside
        pass

    def distance(self, other):
        # TODO: distance is zero if inside, greater than zero if outside comparing nearest edge distance
        pass    
            

class Transform:
    """ Represents a 2D transformation

    The transform is a local-to-parent representation used to transform sets of vertices to
    new coordinates. The components of the transform, ie. scale, rotation and translation, 
    are stored and can be altered with the respective functions or by matrix multiplication 
    via '*' operator. Left multiplying a Vec with a Transform returns a Vec with the applied
    transformation.

    input:
        translation - vector-like, translation (dx, dy)
        rotation - number, angle in *radians*
        scale - number or vector-like combining (scale_x, scale_y)
    """
    def __init__(self, translation=(0,0), rotation=0.0, scale=1.0):
        
        if not isinstance(translation, (list, tuple, Vec)):
            raise ValueError("Translation must be a vector type (dx,dy)!")

        self.__translation = Vec(scale)
        self.__rotation = wrapangle(rotation)
        self.__scale = Vec(scale)

    def __mul__(self, other):
        if type(other) is Vec:
            return self.apply(other)
        
        elif type(other) is Transform:
            t = Transform()
            t.assign(self)
            t.transform(other.translation, other.rotation, other.scale)
            return t

        else:
            raise ValueError("invalid operant type for '*' with Transform")

    def __str__(self):
        return "translation: ({:2}, {:2}), rotation: {:2}, scale: ({:2}, {:2})".format(
            self.__translation.x, self.__translation.y, self.__rotation, self.__scale.x, self.__scale.y)

    @property
    def x(self):
        """ get translation x coordinate """
        return self.__translation.x

    @property
    def y(self):
        """ get translation y coordinate """
        return self.__translation.y

    @property
    def translation(self):
        """ get translation vector """
        return self.__translation

    @property
    def rotation(self):
        """ get rotation value in *radians* """
        return self.__rotation

    @property
    def scale(self):
        """ get scale vector (scale x and y) """
        return self.__scale

    def assign(self, other):
        """ set transform to equal other transform """
        assert isinstance(other, Transform)
        self.__translation.set(other.__translation.x, other.__translation.y)
        self.__rotation = other.__rotation
        self.__scale.set(other.__scale.x, other.__scale.y)
        
    def transform(self, translation=None, rotation=None, scale=None):
        """ apply transformation to transform """
        if isinstance(translation, Transform):
            self.resize(translation.scale)
            self.rotate(translation.rotation)
            self.translate(translation.translation)
        else:
            if not translation is None:
                self.translate(translation)
            if rotation:
                self.rotate(rotation)
            if scale:
                self.resize(scale)
        
        return self
    
    def flipH(self):
        """ reflect transform about the y axis """
        self.__scale.x *= -1

    def flipV(self):
        """ reflect transform about the x axis """
        self.__scale.y *= -1

    def flip(self):
        """ reflect transform about the 45 degree axis """
        self.__scale *= -1

    def translate(self, dx, dy=None):
        """ apply translation vector """
        if isinstance(dx, (list, tuple, Vec)):
            self.__translation.x = dx[0]
            self.__translation.y = dx[1]
        
        else:
            assert isnumber(dx)
            self.__translation.x = dx
            self.__translation.y = dy

    def rotate(self, angle):
        """ apply rotation in *radians* """
        self.__rotation = wrapangle(angle)

    def resize(self, scale):
        """ apply scale factor (both x and y or seperately if tuple)"""
        self.__scale = Vec(scale)

    def reset(self):
        """ reset transform to the identity """
        self.__translation = Vec()
        self.__rotation = 0.0
        self.__scale = Vec(1.0)
