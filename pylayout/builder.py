from pylayout.core import Parameter, ParameterContainer
from pylayout.math import radians
from pylayout.utils import colin, direction_angle
from pylayout.process import ProcessLayer, TraceTemplate
from pylayout.routing import Port
from pylayout.shapes import *

import copy

class ComponentParameter(Parameter):
    """ defines a construction parameter used by blueprints """
    def _set(self, parent, value):
        super()._set(parent, value)
        
        # rebuild the parent to reflect the change!
        parent.rebuild()


class ComponentBuilder(ParameterContainer):
    """ defines a blueprint for creating layout components """
    def __init__(self, **kwargs):
        super(ComponentBuilder, self).__init__(**kwargs)
        
        self.shapes = list()
        self.ports = dict()

        # call user build script
        self.rebuild()
        
    def __repr__(self):
        return self.__class__.__name__ + super().__repr__()

    def build(self): ...

    def on_clear(sefl):
        pass

    def before_build(self):
        pass

    def after_build(self):
        pass

    def before_insert(self):
        pass

    def after_insert(self):
        pass

    def before_port_define(self):
        pass

    def after_port_define(self):
        pass

    def rebuild(self):
        self.clear()
        self.before_build()
        self.build()
        self.after_build()

    def clear(self):
        self.on_clear()
        self.shapes.clear()
        self.ports.clear()

    def insert(self, layer: ProcessLayer, shape,  scale=1.0, rotation=0.0, translation=(0,0)):
        """ insert shape into component process layer
        
        input:
            layer - ProcessLayer
            shape - SimplePolygon, Path, FlexPath, RobustPath, Text or a list of points [N,2] to construct a polygon shape
        """

        self.before_insert()

        if isinstance(shape, list):
            shape = SimplePolygon(shape)

        if not isinstance(shape, (SimplePolygon, Path, Text, FlexPath, RobustPath)):
            raise ValueError('Invalid shape type supplied to insert()')
        
        # always keep a copy, not a ref
        item = shape.copy()
        item.transform(
            scale, 
            rotation, 
            translation)

        self.shapes.append((layer, item))

        self.after_insert()

    def port(self, name, position, width=1.0, direction='e'):
        """ define a new port by name at position with given direction and width """
        self.before_port_define()

        self.ports[name] = Port(position, width, direction)
        
        self.after_port_define()


class Waveguide(ComponentBuilder):
    """ Waveguide Blueprint - defines a parametric waveguide and interpolates over route path """

    template    = ComponentParameter(type=TraceTemplate, required=True, description='Waveguide layer template used when interpolating path.')
    points      = ComponentParameter(type=list, required=True, description='Points defining the waveguide path to interpolate.')
    width       = ComponentParameter(0.5, required=True, description='Waveguide core width.')
    radius      = ComponentParameter(10.0, required=True, description='Radius used when creating bends of any kind.')
    bezier      = ComponentParameter(0.45, description='Method for cunstructing bends along the waveguide.')
    tolerance   = ComponentParameter(0.01, description='Tolerance for bend interpolation defines the mesh precision.')
    precision   = ComponentParameter(1e-9, description='Unit precisision to snap points to.')
    augmented   = ComponentParameter(False, description='Automatically taper segments to wide sections when long enough.')
    aug_width   = ComponentParameter(3, description='Width of wide sections when tapers option is true.')
    aug_template = ComponentParameter(False, description='If a layer template is provided, use it instead of fixed width.')
    taper_length = ComponentParameter(10, description='Length of tapers when tapers option is true.')

    def build(self):
        for i in range(1, len(self.points)-1):
            (x1, y1), (x2, y2), (x3, y3) = self.points[i-1], self.points[i], self.points[i+1]
            if ((x1 - x2)*(x3 - x2) + (y1 - y2)*(y3 - y2)) > 0:
                print('Warning: the angle at the corner {} is less than 90 degrees!'.format(self.points[i]))

        tpl_layer_names = set(self.template.spec.keys())
        tpr_layer_names = set(self.aug_template.spec.keys())

        if self.aug_template:
            if not tpl_layer_names <= tpr_layer_names:
                raise ValueError("Taper template must contain the same layers as the waveguide template!")

        for layer_name, triplet in self.template.spec.items():
            for layer, width, offset in triplet:
                
                if self.radius < 2 * width:
                    # TODO: if the trace is offset, should check with that radius??
                    print('Warning: the waveguide trace width %s on layer %s is too large for the requested bend radius!' % (width, layer.name))

                aug_width = self.aug_width
                if self.aug_template:
                    _, aug_width, _ = list(self.aug_template.spec[layer_name])[0]

                path = self._trace_path(
                    self.points,
                    width,
                    offset,
                    aug_width,
                    self.radius,
                    self.bezier)

                self.insert(layer, path)

        if self.augmented:
            for layer_name in (tpr_layer_names - tpl_layer_names):
                for layer, aug_width, aug_offset in self.aug_template.spec[layer_name]:

                    if self.radius < 2 * aug_width:
                        # TODO: if the trace is offset, should check with that radius??
                        print('Warning: the waveguide trace width %s on layer %s is too large for the requested bend radius!' % (width, layer.name))

                    path = self._trace_path(
                        self.points,
                        self.width,
                        offset,
                        aug_width,
                        self.radius,
                        self.bezier)

                    self.insert(layer, path)

    def _trace_path(self, points, width, offset, taper_width, radius, bezier):

        if len(points) < 3:
            return FlexPath(points, width, offset)

        # this method mutates the points array!
        points = copy.deepcopy(points)

        _taper = False
        _corner = False

        def _make_wide(path, n, segment_length, taper_length, taper_width):
            segment_length -= 2 * taper_length
            path.segment(n * taper_length, taper_width, relative=True)
            path.segment(n * segment_length, taper_width, relative=True)
            # don't add the last taper, it well be generated automatically

        def _make_bend(path, p1, p2, p3, width, radius, bezier):
            v1.normalize()
            v2.normalize()

            path.segment(
                p2 + v1 * radius
            , width, relative=False)
            path.bezier([
                p2 + v1 * radius * bezier,
                p2 + v2 * radius * bezier,
                p2 + v2 * radius
            ], width, relative=False)
        

        path = FlexPath(
            [points[0]],
            width,
            offset,
            max_points=199,    # otherwise path algorithm messes up for some reason :(
            tolerance=self.tolerance,
            precision=self.precision,
            gdsii_path=False)

        i = 1
        while i < len(points) - 1:

            p1 = Vec(points[i-1])
            p2 = Vec(points[i])
            p3 = Vec(points[i+1])

            if colin(p1, p2, p3):
                _taper = False

                length = (p3 - p1).length()
                if _corner:
                    length -= radius

                if i+2 < len(points):
                    if not colin(p2, p3, points[i+2]):
                        length -= radius
                
                if length > 3 * self.taper_length and self.augmented:
                    _make_wide(path, (p3 - p1).normalize(), length, self.taper_length, taper_width)
                    _taper = True

                # NOTE: Possible source of bugs, this is Python 3.7 implementation
                # dependent on how list indices are managed. Consider an alternative.
                del points[i]
                i -= 1
                
            else:
                if not _taper:
                    length = (p2 - p1).length()
                    length -= radius
                    if _corner:
                        length -= radius
                
                    if length > 3 * self.taper_length and self.augmented:
                        _make_wide(path, (p2 - p1).normalize(), length, self.taper_length, taper_width)
                        _taper = True

                v1 = p1 - p2
                v2 = p3 - p2

                if _corner:
                    if v1.length() - 2*radius <= 0:
                        raise Exception("Distance between consecutive corners is too short to accomodate bend radius at {}".format(p2))
                
                if v1.length() - radius <= 0:
                    raise Exception("Segment length is too short to accomodate bend radius at corner {}".format(p2))

                # NOTE: assuming the upcoming point p3 is not a corner (it will be checked anyway in the next iteration)
                if v2.length() - radius <= 0:
                    raise Exception("Segment length is too short to accomodate bend radius at corner {}".format(p2))

                _make_bend(path, p1, p2, p3, width, radius, bezier)

                # reset _taper to false as we never instert tapers in the p3-p2 segment!
                _taper = False
                _corner = True
                
            i += 1

        path.segment(points[-1])
        
        return path