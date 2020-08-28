from .math import __isnumbertype
from .math import *

__all__ = ["Vector"]

def __isvectortype(x):
    if isinstance(x, (list, tuple)):
        return len(x) == 2
    else:
        return isinstance(x, Vector)

class Vector:
    """ Essential vector 2D implementation

    Supports vector arithmetic and transformations used to represent points in 2D
    space like coordinates or polygon vertices, but also directional vectors.
    """

    def __init__(self, *args):
        """
        Arguments
        ---------
        """
        self.__x = 0
        self.__y = 0

        if len(args) > 1:
            self.__x = args[0]
            self.__y = args[1]
        elif len(args) > 0:
            if isinstance(args[0], Vector):
                self.__x = args[0].x
                self.__y = args[0].y
            elif isinstance(args[0], (list, tuple)):
                self.__x = args[0][0]
                self.__y = args[0][1]
            else:
                if not __isnumbertype(args[0]):
                    raise TypeError("Invalid type supplied to Vector() intialization")

                self.__x = args[0]
                self.__y = args[0]

    @classmethod
    def directional(cls, angle):
        return Vector(cos(radians(angle)), sin(radians(angle)))
    
    def assign(self, v):
        """ assign the components from another vector """
        self.__x = v.__x
        self.__y = v.__y
    
    @property
    def x(self): return self.__x
    
    @property
    def y(self): return self.__y

    @x.setter
    def x(self, value):
        if not __isnumbertype(value):
            raise TypeError("Cannot assign non-numeric type to Vector component!")
        self.__x = x

    @y.setter
    def y(self, value):
        if not __isnumbertype(value):
            raise TypeError("Cannot assign non-numeric type to Vector component!")
        self.__y = y
    
    def __getitem__(self, key):
        if not key in [0, 1] : raise IndexError("Vector component index out of range")

        if key == 0:
            return self.__x
        else:
            return self.__y

    def __setitem__(self, key, value):
        if not key in [0, 1] : raise IndexError("Vector component index out of range")

        if key == 0:
            self.__x = value
        else:
            self.__y = value

    def __len__(self):
        return 2

    def __iter__(self):
        yield self.__x
        yield self.__y
    
    def __add__(self, v):
        if not _isvectortype(v):
            raise ValueError("Invalid operand for '+' with Vector, must be a vector compatible type.")
        return Vector(self.__x + v[0], self.__y + v[1])

    def __sub__(self, v):
        if not _isvectortype(v):
            raise ValueError("Invalid operand for '-' with Vector, must be a vector compatible type.")
        return Vector(self.__x - v[0], self.__y - v[1])

    def __mul__(self, v):
        if not __isnumbertype(v):
            raise ValueError("Invalid operand for '*' with Vector, must be a numeric scalar type.")
        return Vector(self.__x * v, self.__y * v)

    def __truediv__(self, v):
        if not __isnumbertype(v):
            raise ValueError("Invalid operand for '/' with Vector, must be a numeric scalar type.")
        return Vector(self.__x / v, self.__y / v)

    def __radd__(self, v):
        if not _isvectortype(v):
            raise ValueError("Invalid operand for '+' with Vector, must be a vector compatible type.")
        return Vector(v[0] + self.__x, v[1] + self.__y)

    def __rsub__(self, v):
        if not _isvectortype(v):
            raise ValueError("Invalid operand for '-' with Vector, must be a vector compatible type.")
        return Vector(v[0] - self.__x, v[1] - self.__y)

    def __rmul__(self, v):
        if not __isnumbertype(v):
            raise ValueError("Invalid operand for '*' with Vector, must be a numeric scalar type.")
        return Vector(self.__x * v, self.__y * v)

    def __neg__(self):
        return Vector(-self.__x, -self.__y)

    def __pos__(self):
        return Vector(+self.__x, +self.__y)

    def __abs__(self):
        return Vector(abs(self.__x), abs(self.__y))

    def __pow__(self, p):
        return Vector(pow(self.__x, p), pow(self.__y, p))

    def __iadd__(self, v):
        if not _isvectortype(v):
            raise ValueError("Invalid operand for '+' with Vector, must be a vector compatible type.")
        self.__x += v[0]
        self.__y += v[1]
        return self

    def __isub__(self, v):
        if not _isvectortype(v):
            raise ValueError("Invalid operand for '-' with Vector, must be a vector compatible type.")
        self.__x -= v[0]
        self.__y -= v[1]
        return self

    def __imul__(self, v):
        if not __isnumbertype(v):
            raise ValueError("Invalid operand for '*' with Vector, must be a numeric scalar type.")
        self.__x *= v
        self.__y *= v
        return self

    def __itruediv__(self, v):
        if not __isnumbertype(v):
            raise ValueError("Invalid operand for '/' with Vector, must be a numeric scalar type.")
        self.__x /= v
        self.__y /= v
        return self

    def __eq__(self, v):
        if not _isvectortype(v):
            raise ValueError('Invalid comparison operand type with Vector')
        if not isclose(self.__x, v[0], rel_tol=1e-6, abs_tol=1e-3): return False
        if not isclose(self.__y, v[1], rel_tol=1e-6, abs_tol=1e-3): return False

    def __ne__(self, v):
        return not self.__eq__(v)

    def __lt__(self, v):
        if not _isvectortype(v):
            raise ValueError('Invalid comparison operand type with Vector, must be a vector compatible type.')
        return (self.__x < v[0]) and (self.__y < v[1])

    def __gt__(self, v):
        if not _isvectortype(v):
            raise ValueError('Invalid comparison operand type with Vector, must be a vector compatible type.')
        return (self.__x > v[0]) and (self.__y > v[1])

    def __le__(self, v):
        return self.__lt__(v) or self.__eq__(v)

    def __ge__(self, v):
        return self.__gt__(v) or self.__eq__(v)

    @property
    def length2(self):
        """ compute the length squared of the vector """
        return self.__x**2 + self.__y**2
    
    @property
    def length(self):
        """ compute the length of the vector  """
        return sqrt(self.__x**2 + self.__y**2)

    def direction(self):
        """ compute the direction angle in degrees """
        a = atan2(self.__y, self.__x)
        return degrees(a)

    def normalize(self):
        h = max(self.length, 1e-6)
        self.__x = self.__x / h
        self.__y = self.__y / h
        return self

    def isclose(self, v, tol=1e-3):
        """ check if near other point (within length tolerance) """
        assert _isvectortype(v)
        return isclose(self.__x, v[0], abs_tol=tol) and isclose(self.__y, v[1], abs_tol=tol)

    def snap(self, x, y=None):
        """ round coordinates to nearest grid coordinate """
        if y is None:
            if _isvectortype(x):
                x = x[0]
                y = x[1]
            else:
                y = x
        
        self.__x = snap(self.__x, x)
        self.__y = snap(self.__y, y)
        return self

    def flipH(self):
        """ flip horizontal """
        self.__x = -self.__x
        return self

    def flipV(self):
        """ flip vertical """
        self.__y = -self.__y
        return self

    def dot(self, v):
        """ compute the dot product of other vector with this one """
        assert _isvectortype(v)
        return self.__x*v[0] + self.__y*v[1]

    def cross(self, v):
        """ compute the 2D cross product of other vector with this one """
        assert _isvectortype(v)
        return self.__x*v[1] - self.__y*v[0]
    
    def lerp(self, a, b, t):
        """ linearly interpolate this vector from a to b using parameter t[0,1] """
        assert _isvectortype(a) and _isvectortype(b) and __isnumbertype(t)

        t = clamp(float(t), 0.0, 1.0)
        self.__x = (1 - t)*a.x + t*b.x
        self.__y = (1 - t)*a.y + t*b.y
        return self

    def trim(self, d):
        """ set vector length to d preserving direction """
        assert __isnumbertype(d)
        v = self.normalize() * d
        self.__x = v[0]
        self.__y = v[1]
        return self

    def point_to(self, p):
        """ change the direction of the vector to point to p preserving the length """
        assert _isvectortype(p)
        h = self.length()
        self.__x = p[0]
        self.__y = p[1]
        return self.trim(h)
    
    def scale(self, factor):
        """ scale the vector by the factor """
        if _isvectortype(factor):
            self.__x *= factor[0]
            self.__y *= factor[1]
        else:
            assert __isnumbertype(factor)
            self.__x *= factor
            self.__y *= factor
        
        return self
    
    def translate(self, d, dy=None):
        """ translate the vector by d=(dx, dy) or (d, dy) """
        if _isvectortype(d):
            self.__x += d[0]
            self.__y += d[1]
        else:
            assert __isnumbertype(d)
            if dy is None:  # translate in the vector direction
                self.__x += sqrt(d)
                self.__y += sqrt(d)
            else:
                self.__x += d
                self.__y += dy

        return self

    def rotate(self, angle):
        """ apply ccw rotation by angle in *degrees* """
        assert __isnumbertype(angle)
        a = radians(angle)
        c = cos(a)
        s = sin(a)
        x = self.__x
        y = self.__y

        self.__x = x*c - y*s
        self.__y = x*s + y*c
        return self
    
    def __repr__(self):
        return "(%.4f, %.4f)" % (self.__x, self.__y)