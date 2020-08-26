from pylayout.utils import isnumber
from pylayout.math import (
    pi,
    wrap,
    radians,
    degrees,
    sin,
    cos,
    atan2,
    sqrt,
    sgn,
    direction_angle,
    Vec,
    Transformed)

from copy import deepcopy
import gdspy


class Shape(Transformed):
    def __init__(self, *args, **kwargs):
        self.xy = []

    def copy(self):
        return deepcopy(self)

    def get_points(self, unit=None, precision=None):
        return self._local.apply(self.xy, unit, precision)
    

class SimplePolygon(Shape):
    """ defines a set of points to construct a closed polygonal shape """
    def __init__(self, xy = [], **kwargs):
        super().__init__(**kwargs)
        self.xy = xy


class Rect(SimplePolygon):
    def __init__(self, size=(1,1), origin=(0,0), **kwargs):
        x, y = origin
        w, h = size
        super().__init__([
            (-x - w/2, -y - h/2),
            (-x + w/2, -y - h/2),
            (-x + w/2, -y + h/2),
            (-x - w/2, -y + h/2)
            ], **kwargs)


class Ellipse(SimplePolygon):
    def __init__(self, origin=(0,0), a=1.0, b=None, tolerance=1e-2, **kwargs):
        x, y = origin

        if b is None:
            b = a

        xy = []
        n = round(1/tolerance)
        da = 2*pi / (n - 1)
        for i in range(n):
            xy.append((x + a*cos(i*da), y + b*sin(i*da)))
        
        super().__init__(xy, **kwargs)


class Text(Shape):
    def __init__(self, text, position=(0,0), size=0.2, anchor='o', polygonal=False, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.__position = position
        self.__size = size
        self.anchor = anchor
        self.polygonal = polygonal

    def get_position(self):
        t = self._local.get_translation()
        p = (t[0] + self.__position[0],
             t[1] + self.__position[1])
        return p

    def set_position(self, value):
        self.__position = value

    """ x, y position of the text """
    position = property(get_position, set_position)

    def get_size(self):
        return self._local.get_scale(0) * self.__size
    
    def set_size(self, value):
        self.__size = value

    """ size of the text """
    size = property(get_size, set_size)

    def get_rotation(self):
        return self._local.rotation

    def set_rotation(self, value):
        self._local.set_rotation(value)

    """ rotation angle in *radians* """
    rotation = property(get_rotation, set_rotation)

    def get_points(self, unit=1, precision=1e-9):
        v = Vec(self.position, None, unit, precision)
        return [(v[0], v[1])]


class Path(Shape):
    """ Path - parametric path shape with a similar API to pylayout.QuickPath """
    def __init__(self, initial_point, width=1.0, offset=0.0, initial_direction='e', tolerance=0.01, gds_path=False, unit=1, precision=1e-9, **kwargs):
        super().__init__(**kwargs)

        self.__unit = unit
        self.__precision = precision

        if isnumber(initial_point[0]):
            initial_point = [initial_point]
        
        self._path = gdspy.FlexPath(initial_point, width, offset, tolerance=tolerance, precision=precision/unit, gdsii_path=gds_path)
        self._update_dir(radians(direction_angle(initial_direction)))
    
    def __repr__(self):
        return repr(self._path.points)

    def __len__(self):
        return len(self._path.points)

    def _update_dir(self, angle=None):
        if angle is None:
            n = Vec(Vec(self._path.points[-1]) - Vec(self._path.points[-2])).normalize()
        else:
            n = Vec(cos(angle), sin(angle))
        
        self._n = n
        self._t = Vec(-n[1], n[0])   # right hand

    @property
    def x(self):
        return self.end()[0]

    @property
    def y(self):
        return self.end()[1]
    
    def length(self):
        """ total path length obtained by summing each segments """
        l = 0.0
        x1, y1 = self._path.points[0]
        for i in range(1, len(self._path.points)):
            x2, y2 = self._path.points[i]
            l += sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            x1 = x2
            y1 = y2
        return l

    def distance(self):
        """ compute the absolute distance from the starting position to ending position """
        if len(self._path.points) < 2:
            return 0.0
        
        x1, y1 = self._path.points[0]
        x2, y2 = self._path.points[-1]
        return sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def start_direction(self):
        """ compute the first direction along the path (angle in *degrees*) """
        if len(self._path.points) < 2:
            return self._n.angle(deg=True)

        x1, y1 = self._path.points[0]
        x2, y2 = self._path.points[1]
        angle = atan2(y2 - y1, x2 - x1)

        return degrees(wrap(self._local.rotation + angle))
    
    def end_direction(self):
        """ compute the last direction along the path (angle in *degrees*) """
        angle = self._n.angle()
        return degrees(self._local.rotation + angle)
    
    def start(self):
        """ get the start position of the path """
        return self._local.apply(self._path.points[0], self.__unit, self.__precision)

    def end(self):
        """ get the end position of the path """
        return self._local.apply(self._path.points[-1], self.__unit, self.__precision)

    def get_points(self, unit=None, precision=None):
        if not unit:
            unit = self.__unit
        if not precision:
            precision = self.__precision
        
        xy = []
        for p in self._path.points:
            xy.append(self._local.apply(p, unit, precision))
        return xy

    def append(self, point, width=None, offset=None):
        """ append a single point to the end of the path """
        self._path.segment(point, width, offset)
        self._update_dir()

    def extend(self, points, width=None, offset=None):
        """ extend path points by appending elements from path """
        for p in points:
            self.append(p, width, offset)

    def to(self, point, width=None, offset=None):
        """ move to absolute position """
        self.append(point, width, offset)
        return self

    def interp(self, p3, p4, p5, width=None, offset=None, relative=True):
        """ interpolate the previous point with the following 4 points using a cubic bezier spline """
        self._path.bezier([p3, p4, p5], width=width, offset=offset, relative=relative)

    def bend(self, radius, angle, method='circular', b=0.2, width=None, offset=None):
        """ produce a smooth bend turning by angle

        inputs:
            radius - bend radius
            angle - ccw angle increment relative to curent direction in *degrees*
            method - 'circular' or 'bezier' in which case the 'b' parameter is used
        """

        if abs(angle) > 180:
            raise_PylayoutException("Cannot bend more than 180 degrees!")

        a = radians(angle)

        if method == 'bezier':

            if abs(angle) > 90:
                print("Warning: bezier bends of grater than 90 degrees will produce strange results at {}".format(self.end()))

            p1 = Vec(self.end(), self.__unit, self.__precision)
            c0 = p1 + sgn(angle)*self._t*radius
            v = (p1 - c0).normalize()
            h = radius * (1.0 / max(1e-1, cos(a/2)))
            p0 = c0 + v.rotate(a/2) * h
            p3 = c0 + v.rotate(a/2) * radius

            v1 = (p1 - p0).normalize()
            v2 = (p3 - p0).normalize()
            l = (p1 - p0).length()

            self._path.bezier([
                p0 + v1*l*b,
                p0 + v2*l*b,
                p3
            ], width, offset, relative=False)

        elif method == 'circular':
            self._path.turn(radius, a, width, offset)

        else:
            raise ValueError("Unrecognized method '%s' for bend!" % method)
        
        self._update_dir(radians(self.end_direction() + angle))
        
        return self

    def smooth(self, points, angles=None, curl_start=1, curl_end=1, t_in=1, t_out=1, width=None, offset=None, relative=True):
        """ add a smooth interpolating curve through the given points.
        
        Uses the Hobby algorithm [1]_ to calculate a smooth interpolating curve made of cubic Bezier segments between each pair of points.
        """
        self._path.smooth(points, angles, curl_start, curl_end, t_in, t_out, False, width, offset, relative)
        self._update_dir()

    def by(self, point, width=None, offset=None):
        """ append a single point relative to the last position """
        self._path.segment(point, width, offset, relative=True)
        self._update_dir()
        return self

    def north(self, d, width=None, offset=None):
        """ move north relative to last position """
        self.by((0,d), width, offset)
        return self

    def east(self, d, width=None, offset=None):
        """ move east relative to last position """
        self.by((d,0), width, offset)
        return self

    def south(self, d, width=None, offset=None):
        """ move south relative to last position """
        self.by((0,-d), width, offset)
        return self

    def west(self, d, width=None, offset=None):
        """ move west relative to last position """
        self.by((-d,0), width, offset)
        return self

    def northeast(self, d, width=None, offset=None):
        """ move north relative to last position """
        _d = sqrt(d)
        self.by((d,d), width, offset)
        return self

    def northwest(self, d, width=None, offset=None):
        """ move north relative to last position """
        _d = sqrt(d)
        self.by((-d,d), width, offset)
        return self

    def southeast(self, d, width=None, offset=None):
        """ move north relative to last position """
        _d = sqrt(d)
        self.by((d,-d), width, offset)
        return self

    def southwest(self, d, width=None, offset=None):
        """ move north relative to last position """
        _d = sqrt(d)
        self.by((-d,-d), width, offset)
        return self
    
    def to_angle(self, d, a, width=None, offset=None):
        """ move relative to last position in the direction given by angle in *degrees* """
        a = radians(a)
        self.by((d*cos(a),d*sin(a)), width, offset)
        return self
    
    def forward(self, d, width=None, offset=None):
        """ move relative to last position in the forward going direction """
        self.by(self._n * d, width, offset)
        return self

    def left(self, d, width=None, offset=None):
        """ move relative to last position in the left going direction """
        self.by(-self._t * d, width, offset)
        return self

    def right(self, d, width=None, offset=None):
        """ move relative to last position in the right going direction """
        self.by(self._t * d, width, offset)
        return self
