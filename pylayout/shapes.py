from pylayout.math import Vec, Transformed, QuickPath

import gdspy
from copy import deepcopy


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
    """ Path - a simple constant width path with QuickPath implementation """
    def __init__(self, width=1.0, initial_point=(0,0), initial_direction='e', gds_path=False, unit=1, precision=1e-9, **kwargs):
        super().__init__(**kwargs)
        self.width = width
        self.gds_path = gds_path
        self._path = QuickPath(initial_point, initial_direction, unit, precision)
        self.xy = self._path.xy
    
    @property
    def x(self): self._path.x
    @property
    def y(self): self._path.y
    def remove(self, index): self._path.remove(index)
    def reverse(self): self._path.reverse()
    def clean(self, tolerance=1e-3): self._path.clean(tolerance)
    def trim(self, length): self._path.trim(length)
    def size(self): self._path.size()
    def length(self): self._path.length()
    def distance(self): self._path.distance()
    def start_direction(self): self._path.start_direction()
    def end_direction(self): self._path.end_direction()
    def start(self): self._path.start()
    def end(self): self._path.end()
    def points(self): self._path.points()
    def append(self, point): self._path.append(point)
    def extend(self, points): self._path.extend(points)
    def to(self, point): self._path.to(point)
    def move_by(self, point): self._path.move_by(point)
    def north(self, d): self._path.north(d)
    def east(self, d): self._path.east(d)
    def south(self, d): self._path.south(d)
    def west(self, d): self._path.west(d)
    def to_angle(self, d, a): self._path.to_angle(d, a)
    def forward(self, d): self._path.forward(d)
    def left(self, d): self._path.left(d)
    def right(self, d): self._path.right(d)


class FlexPath(Shape):
    def __init__(self, 
        points, 
        width, 
        offset=0, 
        corners="natural", 
        bend_radius=None, 
        tolerance=0.01, 
        precision=1e-3, 
        max_points=199, 
        gdsii_path=False, 
        width_transform=True, 
        **kwargs):

        super().__init__(**kwargs)

        self._object = gdspy.FlexPath(
            points,
            width, 
            offset,
            corners,
            "flush",
            bend_radius,
            tolerance,
            precision,
            max_points,
            gdsii_path,
            width_transform)

    def end(self):
        return self._object.points[-1]
    
    def arc(self, radius, initial_angle, final_angle, width=None, offset=None):
        self._object.arc(radius, initial_angle, final_angle, width, offset)

    def area(self):
        self._object.area()

    def bezier(self, points, width=None, offset=None, relative=True):
        self._object.bezier(points, width, offset, relative)

    def parametric(self, curve_function, width=None, offset=None, relative=True):
        self._object.parametric(curve_function, width, offset, relative)

    def segment(self, end_point, width=None, offset=None, relative=False):
        self._object.segment(end_point, width, offset, relative)

    def smooth(self, points, angles=None, curl_start=1, curl_end=1, t_in=1, t_out=1, cycle=False, width=None, offset=None, relative=True):
        self._object.smooth(points, angles, curl_start, curl_end, t_in, t_out, cycle, width, offset, relative)

    def turn(self, radius, angle, width=None, offset=None):
        self._object.turn(radius, angle, width, offset)

    def get_points(self, unit=None, precision=None):
        xy = []
        for points in self._object.get_polygons():
            xy.extend(points)

        return self._local.apply(xy, unit, precision)


class RobustPath(Shape):
    def __init__(self,
        initial_point,
        width,
        offset=0,
        tolerance=0.01,
        precision=1e-3,
        max_points=199,
        max_evals=1000,
        gdsii_path=False,
        width_transform=True,
        **kwargs):

        super().__init__(**kwargs)

        self._object = gdspy.RobustPath(
            initial_point,
            width,
            offset,
            "flush",
            tolerance,
            precision,
            max_points,
            max_evals,
            gdsii_path,
            width_transform)

    def arc(self, radius, initial_angle, final_angle, width=None, offset=None):
        self._object.arc(radius, initial_angle, final_angle, width, offset)

    def area(self):
        self._object.area()

    def bezier(self, points, width=None, offset=None, relative=True):
        self._object.bezier(points, width, offset, relative)

    def parametric(self, curve_function, width=None, offset=None, relative=True):
        self._object.parametric(curve_function, width, offset, relative)

    def segment(self, end_point, width=None, offset=None, relative=False):
        self._object.segment(end_point, width, offset, relative)

    def smooth(self, points, angles=None, curl_start=1, curl_end=1, t_in=1, t_out=1, cycle=False, width=None, offset=None, relative=True):
        self._object.smooth(points, angles, curl_start, curl_end, t_in, t_out, cycle, width, offset, relative)

    def turn(self, radius, angle, width=None, offset=None):
        self._object.turn(radius, angle, width, offset)

    def get_points(self, unit=None, precision=None):
        xy = []
        for points in self._object.get_polygons():
            xy.extend(points)

        return self._local.apply(xy, unit, precision)
        