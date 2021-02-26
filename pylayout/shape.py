from .math import *
from .math import math as math

__all__ = (
    'Circle',
    'Circle2P',
    'Circle3P',
    'Cross',
    'Ellipse',
    'Ngon',
    'Rect',
    'RectC',
    'RectWH',
    'Sector',
    'SectorT',
    'Shape',
    'Square',
    'Taper',
    'TaperQ',
    'Torus',
    'Path',
    'Text'
)

class Shape:
    """ Base class for geometric shapes which translate to simple polygons """
    __slots__ = ('xy')
    def __init__(self, xy=[]):
        self.xy = xy
    
    def copy(self):
        import copy
        return copy.deepcopy(self)

    def transform(self, translation=(0,0), rotation=0.0, scale=1.0, flipH=False):
        dx, dy = translation
        angle = math.radians(rotation)
        
        if isinstance(scale, (list, tuple)):
            sx, sy = scale
        else:
            sx, sy = scale, scale

        if flipH:
            sx = -sx
        
        for i, xy in enumerate(self.xy):
            x, y = xy

            # apply rotation
            x1 = x*math.cos(angle) - y*math.sin(angle)
            y1 = x*math.sin(angle) + y*math.cos(angle)

            self.xy[i] = (x1 * sx + dx, y1 * sy + dy)
        
        return self

    def translate(self, dx, dy):
        return self.transform(translation=(dx, dy))

    def rotate(self, angle):
        return self.transform(rotation=angle)

    def scale(self, scale):
        return self.transform(scale=scale)
    
    def flipH(self):
        return self.transform(flipH=True)


class Rect(Shape):
    """ Rectangle shape from lower-left (ll) and upper-right (ur) points """
    def __init__(self, ll=(-.5,-.5), ur=(.5,.5)):
        xl, yl = ll
        xr, yu = ur
        super().__init__([
            (xl, yl),
            (xr, yl),
            (xr, yu),
            (xl, yu)
        ])


class RectC(Rect):
    """ Rectangle shape from center cooridnate and size """
    def __init__(self, center=(0,0), size=(1,1)):
        x, y = center
        if isinstance(size, (tuple, list)):
            w, h = size
        else:
            w, h = size, size

        super().__init__((x - w/2, y - h/2), (x + w/2, y + h/2))


class RectWH(Rect):
    """ Rectangle shape from lower-left (ll) and width and height """
    def __init__(self, ll=(0,0), w=1, h=1):
        x, y = ll
        super().__init__((x, y), (x + w, y + h))


class Square(RectC):
    """ Square shape from center and size """
    def __init__(self, size=1, center=(0,0)):
        super().__init__(center, size)


class Ngon(Shape):
    """ N-sided polygon shape with radius r """
    def __init__(self, sides=6, r=0.5, center=(0,0)):
        x, y = center
        d = 2*math.pi/sides

        super().__init__([
            (x + r*math.sin(d*i), y + r*math.cos(d*i)) for i in range(0,sides)
        ])


class Sector(Shape):
    """ Circle sector of radius r form start angle to end angle in **degrees** """
    def __init__(self, r=1, start=0, end=90, points=16, center=(0,0)):
        x, y = center
        a1 = math.radians(start)
        a2 = math.radians(end)
        a = [a1 + (a2 - a1)/(points - 1)*i for i in range(points)]

        xy = [(0,0)]
        xy.extend(map(lambda t: (x + r*math.cos(t), y + r*math.sin(t)), a))

        super().__init__(xy)


class Ellipse(Shape):
    """ Ellipsoid shape with vertical (b) and horizontal (a) axes """
    def __init__(self, a=0.5, b=0.25, center=(0,0), points=64):
        x, y = center
        d = 2*math.pi/points

        super().__init__([
            (x + a*math.cos(d*i), y + b*math.sin(d*i)) for i in range(0,points)
        ])


class Circle(Ellipse):
    """ Circle shape with radius r """
    def __init__(self, r=0.5, center=(0,0), points=64):
        super().__init__(r, r, center, points)


class Circle2P(Circle):
    """ Circle shape from two points and radius r """
    def __init__(self, p1, p2, r=1):
        c = circle_from_two_points(p1, p2, r)
        super().__init__(r, c)


class Circle3P(Circle):
    """ Circle shape from three points """
    def __init__(self, p1, p2, p3):
        c, r = circle_from_three_points(p1, p2, p3)
        super().__init__(r, c)


class Torus(Shape):
    """ Torus shape with inner radius r1 and outer radius r2 """
    def __init__(self, r1=0.5, r2=1, points=64, center=(0,0)):
        x, y = center
        d = 2*math.pi/(points - 1)

        xy = [(x + r1*math.cos(d*i), y + r1*math.sin(d*i)) for i in range(0,points)]
        xy.extend([(x + r2*math.cos(d*i), y + r2*math.sin(d*i)) for i in range(points-1,-1,-1)])

        super().__init__(xy)


class SectorT(Shape):
    """ Torus sector with inner radius r1 and outer radius r2 form start angle a1 to end angle a2 in **degrees** """
    def __init__(self, r1=0.5, r2=1, a1=0, a2=90, points=64, center=(0,0)):
        a1 = wrap_angle(math.radians(a1))
        a = wrap_angle(math.radians(a2)) - a1
        x, y = center
        d = a/(points - 1)

        xy = [(x + r1*math.cos(a1 + d*i), y + r1*math.sin(a1 + d*i)) for i in range(0,points)]
        xy.extend([(x + r2*math.cos(a1 + d*i), y + r2*math.sin(a1 + d*i)) for i in range(points-1,-1,-1)])

        super().__init__(xy)


class Cross(Shape):
    """ Cross shape with arm length and inner and outer arm thicknesses """
    def __init__(self, length=.5, inner=.2, outer=.1, center=(0,0)):
        x, y = center
        l, w, t = length, inner/2, outer/2
        super().__init__([
            (x - w, y - w),
            (x - l, y - t),
            (x - l, y + t),
            (x - w, y + w),
            (x - t, y + l),
            (x + t, y + l),
            (x + w, y + w),
            (x + l, y + t),
            (x + l, y - t),
            (x + w, y - w),
            (x + t, y - l),
            (x - t, y - l)
        ])


class Taper(Shape):
    """ Produce tapered rectangle from width w1 to width w2 """
    def __init__(self, w1=0.5, w2=1.0, length=10, origin=(0,0)):
        x, y = origin
        super().__init__([
            (x,        y - w1/2),
            (x+length, y - w2/2),
            (x+length, y + w2/2),
            (x,        y + w1/2)
        ])


class TaperQ(Shape):
    """ Quadratic taper implementation based off of DOI: 10.1364/OPEX.13.007748 """
    def __init__(self, w1=2.0, w2=0.5, alpha=0.5, length=10, tol=.01):
        x, y = math.adaptlinspace(0, length, lambda x: w1/2 + (w1 - w2)/2*(pow(1 - x/length, alpha) - 1), tol)
        
        xy = [(c, y[i]) for i, c in enumerate(x)]
        xy.extend(reversed([(c, -y[i]) for i, c in enumerate(x)]))

        super().__init__(xy)


class Path:
    pass


class Text:
    pass