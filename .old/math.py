from pylayout.utils import isnumber, isvec, direction_angle, clamp
from math import (
    isclose,
    trunc,
    log10,
    pi,
    sqrt,
    sin,
    cos,
    tan,
    asin,
    acos,
    atan2,
    degrees as _degrees,
    radians as _radians)

import numpy

def sgn(x):
    return -1.0 if x < 0 else 1.0

def radians(x: float) -> float:
    """ convert angle from *degrees to radians* and return result within domain [0, 2pi[ """
    return float(numpy.angle(numpy.exp(1j*_radians(x))))

def degrees(x: float) -> float:
    """ convert angle from *radians to degrees* and return result within domain [0, 360[ """
    return float(_degrees(numpy.angle(numpy.exp(1j*x))))

def wrap(x, deg=False):
    """ wrap angle in domain [0, 2pi[ or [0, 360[ if deg is True """
    if deg is True: x = _radians(x)
    x = float(numpy.angle(numpy.exp(1j*x)))
    if deg is True: x = _degrees(x)
    return x

def snap(x, unit):
    """ return number rounded to the nearest unit """
    return round(float(x) / unit) * unit


class Vec:
    """ Vec - an extremely convenient vector 2D class

    Supports vector arithmetic and transformations used to represent points in 2D
    space like coordinates or polygon vertices, but also directional vectors.
    """
    def __init__(self, x=None, y=None, unit=1, precision=1e-9):
        # damn you numpy!@!@
        if isinstance(x, numpy.float64):
            x = float(x)
        if isinstance(y, numpy.float64):
            y = float(y)
        
        self.__unit = unit
        self.__precision = precision
        self.__digits = abs(trunc(-log10(precision/unit)))
        if x is None and y is None:
            self._x = 0.0
            self._y = 0.0
        elif isvec(x):
            assert len(x) == 2 and isnumber(x[0])
            self.x = round(x[0], self.__digits)
            self.y = round(x[1], self.__digits)
        else:
            assert isnumber(x)
            self._x = round(x, self.__digits)
            if y is None:
                self._y = self._x
            else:
                self._y = round(y, self.__digits)

    @classmethod
    def directional(cls, angle, deg=False, unit=1, precision=1e-9):
        if deg: angle = radians(angle)
        return Vec(cos(angle), sin(angle), unit, precision)

    def assign(self, v):
        """ assign the components from another vector """
        self.__unit = v.__unit
        self.__precision = v.__precision
        self.__digits = v.__digits
        self._x = v._x
        self._y = v._y

    @property
    def x(self): return self._x
    @x.setter
    def x(self, value):
        self._x = round(value, self.__digits)

    @property
    def y(self): return self._y
    @y.setter
    def y(self, value):
        self._y = round(value, self.__digits)

    def __getitem__(self, key):
        if key < 0 or key > 1 : raise IndexError()

        if key == 0: return self._x
        if key == 1: return self._y

    def __setitem__(self, key, value):
        if key < 0 or key > 1 : raise IndexError()

        if key == 0: self._x = round(value, self.__digits)
        if key == 1: self._y = round(value, self.__digits)

    def __len__(self):
        return 2

    def __iter__(self):
        yield self._x
        yield self._y
    
    def __repr__(self):
        return "({:.4f}, {:.4f})".format(self._x, self._y)
    
    def __add__(self, other):
        if not isvec(other):
            raise ValueError("invalid operand for '+' with Vec. must be a vector compatible type.")
        return Vec(self._x + other[0], self._y + other[1], self.__unit, self.__precision)

    def __sub__(self, other):
        if not isvec(other):
            raise ValueError("invalid operand for '-' with Vec. must be a vector compatible type.")
        return Vec(self._x - other[0], self._y - other[1], self.__unit, self.__precision)

    def __mul__(self, other):
        if not isnumber(other):
            raise ValueError("invalid operand for '*' with Vec. must be a numeric scalar type.")
        return Vec(self._x * other, self._y * other, self.__unit, self.__precision)

    def __truediv__(self, other):
        if not isnumber(other):
            raise ValueError("invalid operand for '/' with Vec. must be a numeric scalar type.")
        return Vec(self._x / other, self._y / other, self.__unit, self.__precision)

    def __radd__(self, other):
        if not isvec(other):
            raise ValueError("invalid operand for '+' with Vec. must be a vector compatible type.")
        return Vec(other[0] + self._x, other[1] + self._y, self.__unit, self.__precision)

    def __rsub__(self, other):
        if not isvec(other):
            raise ValueError("invalid operand for '-' with Vec. must be a vector compatible type.")
        return Vec(other[0] - self._x, other[1] - self._y, self.__unit, self.__precision)

    def __rmul__(self, other):
        if not isnumber(other):
            raise ValueError("invalid operand for '*' with Vec. must be a numeric scalar type.")
        return Vec(self._x * other, self._y * other, self.__unit, self.__precision)

    def __neg__(self):
        return Vec(-self._x, -self._y, self.__unit, self.__precision)

    def __pos__(self):
        return Vec(+self._x, +self._y, self.__unit, self.__precision)

    def __abs__(self):
        return Vec(abs(self._x), abs(self._y), self.__unit, self.__precision)

    def __pow__(self, p):
        return Vec(pow(self._x, p), pow(self._y, p), self.__unit, self.__precision)

    def __iadd__(self, other):
        if not isvec(other):
            raise ValueError("invalid operand for '+' with Vec. must be a vector compatible type.")
        self.x += other[0]
        self.y += other[1]
        return self

    def __isub__(self, other):
        if not isvec(other):
            raise ValueError("invalid operand for '-' with Vec. must be a vector compatible type.")
        self.x -= other[0]
        self.y -= other[1]
        return self

    def __imul__(self, other):
        if not isnumber(other):
            raise ValueError("invalid operand for '*' with Vec. must be a numeric scalar type.")
        self.x *= other
        self.y *= other
        return self

    def __itruediv__(self, other):
        if not isnumber(other):
            raise ValueError("invalid operand for '/' with Vec. must be a numeric scalar type.")
        self.x /= other
        self.y /= other
        return self

    def __eq__(self, other):
        if not isvec(other):
            raise ValueError('invalid comparison operand type with Vec')
        if not isclose(self._x, other[0], rel_tol=1e-6, abs_tol=1e-3): return False
        if not isclose(self._y, other[1], rel_tol=1e-6, abs_tol=1e-3): return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if not isvec(other):
            raise ValueError('invalid comparison operand type with Vec. must be a vector compatible type.')
        return (self._x < other[0]) and (self._y < other[1])

    def __gt__(self, other):
        if not isvec(other):
            raise ValueError('invalid comparison operand type with Vec. must be a vector compatible type.')
        return (self._x > other[0]) and (self._y > other[1])

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)

    def __ge__(self, other):
        return self.__gt__(other) or self.__eq__(other)
    
    def length2(self):
        """ compute the length squared of the vector """
        return self._x**2 + self._y**2
    
    def length(self):
        """ compute the length of the vector  """
        return sqrt(self._x**2 + self._y**2)

    def angle(self, deg=False):
        """ compute the angle of the vector in radians or degrees """
        a = atan2(self._y, self._x)
        return degrees(a) if deg else a

    def normalize(self):
        h = max(self.length(), 1e-6)
        self.x = self._x / h
        self.y = self._y / h
        return self

    def near(self, v, tolerance=1e-3):
        """ check if near other point (within length tolerance) """
        assert isvec(v)
        return isclose(self._x, v[0], abs_tol=tolerance) and isclose(self._y, v[1], abs_tol=tolerance)

    def snap(self, x, y=None):
        """ round coordinates to nearest grid coordinate """
        if y is None:
            if isvec(x):
                x = x[0]
                y = x[1]
            else:
                y = x
        
        self._x = snap(self._x, x)
        self._y = snap(self._y, y)
        return self

    def flipH(self):
        """ flip horizontal """
        self._x = -self._x
        return self

    def flipV(self):
        """ flip vertical """
        self._y = -self._y
        return self

    def dot(self, v):
        """ compute the dot product of other vector with this one """
        assert isvec(v)
        return self._x*v[0] + self._y*v[1]

    def cross(self, v):
        """ compute the 2D cross product of other vector with this one """
        assert isvec(v)
        return self._x*v[1] - self._y*v[0]
    
    def lerp(self, a, b, t):
        """ linearly interpolate this vector from a to b using parameter t[0,1] """
        assert isvec(a) and isvec(b) and isnumber(t)
        t = clamp(float(t), 0.0, 1.0)
        self.x = (1 - t)*a.x + t*b.x
        self.y = (1 - t)*a.y + t*b.y
        return self

    def trim(self, d):
        """ set vector length to d preserving direction """
        assert isnumber(d)
        v = self.normalize() * d
        self.x = v[0]
        self.y = v[1]
        return self

    def point_to(self, p):
        """ change the direction of the vector to point to p preserving the length """
        assert isvec(p)
        h = self.length()
        self.x = p[0]
        self.y = p[1]
        return self.trim(h)
    
    def scale(self, factor):
        """ scale the vector by the factor """
        if isvec(factor):
            self.x *= factor[0]
            self.y *= factor[1]
        else:
            assert isnumber(factor)
            self.x *= factor
            self.y *= factor
        return self
    
    def translate(self, d, dy=None):
        """ translate the vector by d=(dx, dy) or (d, dy) """
        if isvec(d):
            self.x += d[0]
            self.y += d[1]
        else:
            assert isnumber(d)
            if dy is None:  # translate in the vector direction
                self.x += sqrt(d)
                self.y += sqrt(d)
            else:
                self.x += d
                self.y += dy
            return self

    def rotate(self, angle):    # ccw rotation
        """ apply ccw rotation to the vector by angle in *radians* """
        assert isnumber(angle)
        c = cos(angle)
        s = sin(angle)
        x = self._x
        y = self._y
        self.x = x*c - y*s
        self.y = x*s + y*c
        return self

    def array(self):
        """ return the vector as a tuple """
        return (self._x, self._y)


class DPoint(Vec):
    """ Double precision point rouding x, y to 1e-9 precision """
    def __init__(self, x=None, y=None):
        super(DPoint, self).__init__(x, y, 1, 1e-9)


class Point(Vec):
    """ Double precision point rouding x, y to 1e-3 precision """
    def __init__(self, x=None, y=None):
        super(Point, self).__init__(x, y, 1, 1e-3)


class Transform:
    """ Represents a 2D transformation

    The transform is a local-to-parent representation used to transform sets of vertices to
    new coordinates. The components of the transform, ie. scale, rotation and translation, 
    are stored and can be altered with the respective functions or by matrix multiplication 
    via '*' operator. Left multiplying a Vec with a Transform returns a Vec with the applied
    transformation.

    input:
        scale - number or vector-like combining (scale_x, scale_y)
        rotation - number, angle in *radians*
        translation - vector-like, translation (dx, dy)
    """
    def __init__(self, scale=1.0, rotation=0.0, translation=(0,0), unit=1, precision=1e-9):
        """
        input:
            scale - number or vector-like, scale factor for x and y
            rotation - number, angle in *degrees*
            origin - vector-like, translation (dx, dy)
        """

        if not isvec(translation):
            raise ValueError("Translation must be a vector type (dx,dy)!")

        self.__unit = unit
        self.__precision = precision
        self.__digits = abs(trunc(-log10(precision/unit)))

        self.__scale = Vec(scale, unit=unit, precision=precision)
        self.__rotation = wrap(rotation)
        self.__translation = Vec(translation, unit=unit, precision=precision)

    def __mul__(self, other):
        if isvec(other):
            return self.apply(other)
        elif isinstance(other, Transform):
            t = Transform()
            t.assign(self)
            t.transform(other.get_scale(), other.get_rotation(), other.get_translation())

            # c = cos(self.__rotation)
            # s = sin(self.__rotation)
            # m11 = self.__scale.x*c
            # m12 = -self.__scale.y*s
            # m21 = self.__scale.x*s
            # m22 = self.__scale.y*c

            # return numpy.array([
            #     [m11, m12, self.__translation.x],
            #     [m21, m22, self.__translation.y],
            #     [0, 0, 1]
            # ])

            return t

        else:
            raise ValueError("invalid operant type for '*' with Transform")

    def __repr__(self):
        return "scale: ({:2}, {:2}), translation: ({:2}, {:2}), rotation: {:2}".format(
            self.__scale.x, self.__scale.y, self.__translation.x, self.__translation.y, self.__rotation)

    def __str__(self):
        return self.__repr__()

    @property
    def x(self): return self.__translation.x
    @property
    def y(self): return self.__translation.y

    def assign(self, transform):
        assert isinstance(transform, Transform)
        self.__unit = transform.__unit
        self.__precision = transform.__precision
        self.__digits = transform.__digits
        self.__scale.assign(transform.__scale)
        self.__rotation = transform.__rotation
        self.__translation.assign(transform.__translation)
        
    def transform(self, scale=None, rotation=None, translation=None):
        """ apply transformation to this transform
        
        input:
            scale - number, vector or Transform instance
            rotation - number, angle of rotation in *radians*
            translation - vector, translation distance (dx, dy)
        """
        if isinstance(scale, Transform):
            self.scale(scale.get_scale())
            self.rotate(rotation.rotation)
            self.translate(translation.translation)
        else:
            if not scale is None:
                self.scale(scale)
            if rotation:
                self.rotate(rotation)
            if translation:
                self.translate(translation)
        return self

    def apply(self, point, unit=None, precision=None):
        """ apply transformation to point or list of points and return the result """

        d = self.__digits
        if unit or precision:
            u, p = (1, 1)
            if unit: u = unit
            if precision: p = precision
            d = abs(trunc(-log10(p/u)))

        if not isnumber(point[0]):
            xy = []
            for p in point:
                xy.append(self.apply(p, unit, precision))
            return xy

        _x = round(point[0] * self.__scale.x, d)
        _y = round(point[1] * self.__scale.y, d)

        c = cos(self.__rotation); s = sin(self.__rotation)
        x = round((_x*c - _y*s) + self.__translation.x, d)
        y = round((_x*s + _y*c) + self.__translation.y, d)

        # always return a tuple
        return (x, y)

    def get_scale(self, index=None):
        if index is None:
            return self.__scale.array()
        
        return self.__scale[index]

    def set_scale(self, scale):
        self.__scale = Vec(scale, self.__unit, self.__precision)

    scale = property(get_scale, set_scale)

    def get_rotation(self):
        """ gets the rotation angle in *radians* """
        return self.__rotation

    def set_rotation(self, angle):
        """ sets the rotation angle in *radians* """
        assert isnumber(angle)
        self.__rotation = wrap(angle)

    rotation = property(get_rotation, set_rotation)

    def get_translation(self):
        return self.__translation.array()
    
    def set_translation(self, dx, dy=None):
        if dy is None:
            assert isvec(dx)
            self.__translation = Vec(dx, None, self.__unit, self.__precision)
        else:
            assert isnumber(dx)
            self.__translation.x = dx
            self.__translation.y = dy

    translation = property(get_translation, set_translation)

    def get_origin(self):
        return (-self.__translation).array()
    
    def set_origin(self, x, y=None):
        if y is None:
            assert isvec(x)
            self.__translation = -Vec(x, None, self.__unit, self.__precision)
        else:
            assert isnumber(x)
            self.__translation.x = -x
            self.__translation.y = -y

    origin = property(get_origin, set_origin)
    
    def scale(self, scale):
        """ scales by scale factor (mutates the transform) """
        s = Vec(scale, self.__unit, self.__precision)
        self.__scale.x *= s.x
        self.__scale.y *= s.y
        return self
    
    def translate(self, d, dy=None):
        """ translates by vector d, or by (dx,dy) (mutates the transform) """
        if dy is None:
            assert isvec(d)
            self.__translation += Vec(d, None, self.__unit, self.__precision)
        else:
            self.__translation.x += d
            self.__translation.y += dy
        return self

    def rotate(self, angle):
        """ rotates by angle in *radians* (mutates the transform) """
        self.__rotation = wrap(self.__rotation + angle)
        return self

    def flipV(self):
        """ reflect y-coordinate (mutates the transform) """
        self.__scale.y *= -1

    def flipH(self):
        """ reflect x-coordinate (mutates the transform) """
        self.__scale.x *= -1

    def reflect(self):
        """ reflect off the diagonal (mutates the transform) """
        self.__scale *= -1

    def reset(self):
        """ reset transformation to identity """
        self.__scale = Vec(1.0, 1.0, self.__unit, self.__precision)
        self.__rotation = 0.0
        self.__translation = Vec(0.0, 0.0, self.__unit, self.__precision)


class AABB:
    """ AABB - Axis Aligned Bounding Box

    Can be constructed to fit the bounds of a list of points. Features intersection routines.
    """
    def __init__(self, xmin=None, ymin=None, xmax=None, ymax=None):
        if type(xmin) is numpy.ndarray:
            self.xmin = float(xmin[0][0])
            self.ymin = float(xmin[0][1])
            self.xmax = float(xmin[1][0])
            self.ymax = float(xmin[1][1])
        
        else:
            if not xmin is None:
                self.xmin = xmin
                self.ymin = ymin
                self.xmax = xmax
                self.ymax = ymax
            else:
                self.reset()

    def __repr__(self):
        return "min: ({:.2f}, {:.2f}) max: ({:.2f}, {:.2f})".format(self.xmin, self.ymin, self.xmax, self.ymax)

    def __str__(sefl):
        return self.__repr__()

    def reset(self):
        from sys import maxsize
        self.xmin = maxsize; 
        self.xmax = -(maxsize-1)
        self.ymin = maxsize; 
        self.ymax = -(maxsize-1)

    @classmethod
    def fit(cls, points):
        b = cls()
        b.grow(points)
        return b

    def grow(self, point):
        if not isnumber(point[0]):
            for p in point:
                self.grow(p)
        else:
            if point[0] < self.xmin: self.xmin = point[0]
            if point[0] > self.xmax: self.xmax = point[0]
            if point[1] < self.ymin: self.ymin = point[1]
            if point[1] > self.ymax: self.ymax = point[1]

    def get_width(self):
        return self.xmax - self.xmin

    def get_height(self):
        return self.ymax - self.ymin

    width = property(get_width)
    height = property(get_height)

    def xrange(self):
        return (self.xmin, self.xmax)

    def yrange(self):
        return (self.ymin, self.ymax)

    def area(self):
        return self.width * self.height

    def size(self):
        return (self.width, self.height)

    def points(self):
        return [
            self.bottom_left,
            self.bottom_right,
            self.top_right,
            self.top_left
        ]

    @property
    def center(self):
        return ((self.xmin + self.xmax)/2, (self.ymin + self.ymax)/2)
    @property
    def left(self):
        return (self.xmin, (self.ymin + self.ymax)/2)
    @property
    def right(self):
        return (self.xmax, (self.ymin + self.ymax)/2)
    @property
    def top(self):
        return ((self.xmin + self.xmax)/2, self.ymax)
    @property
    def bottom(self):
        return ((self.xmin + self.xmax)/2, self.ymin)
    @property
    def bottom_left(self):
        return (self.xmin, self.ymin)
    @property
    def bottom_right(self):
        return (self.xmax, self.ymin)
    @property
    def top_left(self):
        return (self.xmin, self.ymax)
    @property
    def top_right(self):
        return (self.xmax, self.ymax)
    
    def is_point_inside(self, x, y):
        return x > self.xmin and x < self.xmax and y > self.ymin and y < self.ymax

    def is_overlapping(self, aabb):
        assert isinstance(aabb, AABB)
        if aabb.xmin > self.xmax or aabb.xmax < self.xmin or aabb.ymin > self.ymax or aabb.ymax < self.ymin:
            return False


class QuickPath:
    """ QuickPath - progressive path algorithm wrapping a simple points list
    
    input:
        initial_point, vector-like point (x,y)
        initial_direction, number or string, either angle in *degrees* or a compas direction string
    """
    def __init__(self, initial_point=(0,0), initial_direction='e', unit=1, precision=1e-9):
        self.__unit = unit
        self.__precision = precision
        self.xy = []

        if not isnumber(initial_point[0]):
            self.extend(initial_point)
        else:
            self.append(initial_point)
        
        self.__initial_dir = radians(direction_angle(initial_direction))

    def __repr__(self):
        return repr(self.xy)

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            return [self.xy[i] for i in range(idx.start, idx.stop, idx.step)]
        if idx < -len(self.xy) or idx >= len(self.xy): 
            raise IndexError("Index %s out of range in path!" % idx)
        return self.xy[idx]

    def __setitem__(self, idx, value):
        if idx < -len(self.xy) or idx >= len(self.xy): 
            raise IndexError("Index %s out of range in path!" % idx)
        if not isvec(value):
            raise ValueError("Invalid type set append path! Must be a vector addressable type.")
        self.xy[idx] = Vec(value, None, self.__unit, self.__precision)

    def __delitem__(self, idx):
        if idx < -len(self.xy) or idx >= len(self.xy): 
            raise IndexError("Index %s out of range in path!" % idx)
        del self.xy[idx]
    
    def __len__(self):
        return len(self.xy)

    def __add__(self, other):
        if not isinstance(other, QuickPath):
            raise ValueError("Invalid operand type for '-', expecting QuickPath!")
        qp = QuickPath(self)
        qp.extend(other)
        return qp

    @property
    def x(self):
        p = self.end()
        if p is None:
            raise AttributeError('x is not defined for null path!')
        return p.x

    @property
    def y(self):
        p = self.end()
        if p is None:
            raise AttributeError('x is not defined for null path!')
        return p.y

    def remove(self, index):
        """ remove a single point at index """
        if index < 0:
            index += len(self.xy)
        if index >= len(self.xy) : raise IndexError('Index out of range')
        del self.xy[index]

    def reverse(self):
        """ reverse the path direction starting at the end and ending at the begining """
        self.xy.reverse()
        return self

    def clean(self, tolerance=None):
        """ remove any overlapping points within the tolerance radius """
        if tolerance is None:
            tolerance = self.__precision / self.__unit
        
        for i, p in enumerate(self.xy):
            if self.xy[i].near(self.xy[i-1], tolerance):
                del self.xy[i-1]

        return self

    def trim(self, length):
        """ progressively remove points form both ends until path is the required length """
        pass

    def size(self):
        """ get the number of points in the path array """
        return len(self.xy)
    
    def length(self):
        """ compute the length traveled along the path (adds segment lengths) """
        l = 0
        for i in range(1, len(self.xy)):
            l += (self.xy[i] - self.xy[i-1]).length()
        return l

    def distance(self):
        """ compute the absolute distance from the starting position to ending position """
        if len(self.xy) < 2:
            return 0.0
        return (self.xy[-1]-self.xy[0]).length()

    def start_direction(self):
        """ compute the first direction along the path (angle in *degrees*) """
        if len(self.xy) < 2:
            return degrees(self.__initial_dir)
        return (self.xy[1] - self.xy[0]).angle(deg=True)
    
    def end_direction(self):
        """ compute the last direction along the path (angle in *degrees*) """
        if len(self.xy) < 2:
            return degrees(self.__initial_dir)
        return (self.xy[-1] - self.xy[-2]).angle(deg=True)
    
    def start(self):
        """ get the start position of the path """
        if len(self.xy) > 0:
            return self.xy[0]
        return None

    def end(self):
        """ get the end position of the path """
        if len(self.xy) > 0:
            return self.xy[-1]
        return None

    def points(self):
        xy = []
        for p in self.xy:
            xy.append(p.array())
        return xy

    def append(self, point):
        """ append a single point to the end of the path """
        self.xy.append(Vec(point, None, self.__unit, self.__precision))

    def extend(self, points):
        """ extend path points by appending elements from path """
        if isinstance(points, QuickPath):
            self.extend(points.points())
        else:
            for p in points:
                self.append(p)

    def to(self, point):
        """ move to absolute position """
        self.append(point)
        return self

    def by(self, point):
        """ append a single point relative to the last position """
        if len(self.xy) > 0:
            self.xy.append(self.xy[-1] + Vec(point, None, self.__unit, self.__precision))
        else:
            self.xy.append(point)
        return self

    def north(self, d):
        """ move north relative to last position """
        self.by(Vec(0,d,self.__unit,self.__precision))
        return self

    def east(self, d):
        """ move east relative to last position """
        self.by(Vec(d,0,self.__unit,self.__precision))
        return self

    def south(self, d):
        """ move south relative to last position """
        self.by(Vec(0,-d,self.__unit,self.__precision))
        return self

    def west(self, d):
        """ move west relative to last position """
        self.by(Vec(-d,0,self.__unit,self.__precision))
        return self
    
    def to_angle(self, d, a):
        """ move relative to last position in the direction given by angle in *degrees* """
        a = radians(a)
        self.by(Vec(d*cos(a),d*sin(a),self.__unit,self.__precision))
        return self
    
    def forward(self, d):
        """ move relative to last position in the forward going direction """
        if len(self.xy) > 1:
            n = (self.xy[-1] - self.xy[-2]).normalize()
            self.by(n * d)
        else:
            self.to_angle(d, self.end_direction())
        return self

    def left(self, d):
        """ move relative to last position in the left going direction """
        # self.to_angle(d, self.end_direction() + 90.0)
        if len(self.xy) > 1:
            n = (self.xy[-1] - self.xy[-2]).normalize()
            self.by(Vec(-n[1], n[0], self.__unit, self.__precision) * d)
        else:
            self.to_angle(d, degrees(self.__initial_dir) + 90)
        return self

    def right(self, d):
        """ move relative to last position in the right going direction """
        # self.to_angle(d, self.end_direction() - 90.0)
        if len(self.xy) > 1:
            n = (self.xy[-1] - self.xy[-2]).normalize()
            self.by(Vec(n[1], -n[0], self.__unit, self.__precision) * d)
        else:
            self.to_angle(d, degrees(self.__initial_dir) - 90)
        return self


class Transformed:
    """ Transformed - provides a local-to-parent transform for layout objects
    
    Children inherit the property _local which is a transform instance 
    and also inherit a set of useful methods for local transformations.
    """

    def __new__(cls, *args, **kwargs):

        kv = {}
        for key in Transform.__init__.__code__.co_varnames:
            if key in kwargs:
                kv[key] = kwargs[key]
                del kwargs[key]

        instance = object.__new__(cls)
        instance._local = Transform(**kv)

        return instance

    @property
    def x(self): return self._local.x
    @property
    def y(self): return self._local.y

    def scale(self, scale):
        """ scales by scale factor (mutates the transform) """
        self._local.scale(scale)
        return self

    def translate(self, d, dy=None):
        """ translates by vector d, or by (dx,dy) (mutates the transform) """
        self._local.translate(d, dy)
        return self

    def rotate(self, angle):
        """ rotates by angle in *radians* (mutates the transform) """
        self._local.rotate(angle)
        return self

    def flipV(self):
        """ reflect y-coordinate (mutates the transform) """
        self._local.flipV()
        return self

    def flipH(self):
        """ reflect x-coordinate (mutates the transform) """
        self._local.flipH
        return self

    def reflect(self):
        """ reflect off the diagonal (mutates the transform) """
        self._local.reflect()
        return self

    def transform(self, scale=1.0, rotation=0.0, translation=(0,0)):
        """ transform all at once in this order: scale, rotate, translate """
        self._local.transform(scale, rotation, translation)
        return self

    def set_origin(self, x, y=None):
        """ change local coordinate system origin """
        self._local.set_origin(x, y)

    def set_translation(self, x, y=None):
        self._local.set_translation(x, y)

    def set_rotation(self, angle):
        self._local.set_rotation(angle)

    def set_scale(self, scale):
        self._local.set_scale(scale)

    def get_origin(self):
        return self._local.get_origin()

    def get_translation(self):
        return self._local.get_translation()

    def get_rotation(self):
        return self._local.get_rotation()

    def get_scale(self, index=None):
        return self._local.get_scale(index)

    def reset_transformation(self):
        """ reset transformation to identity """
        self._local.reset()