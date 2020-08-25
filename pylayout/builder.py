from pylayout.core import Parameter, ParameterContainer, _pylayout_warning, _pylayout_exception
from pylayout.utils import ccw, colin, direction_angle
from pylayout.math import pi, radians, degrees, Vec, AABB
from pylayout.process import ProcessLayer
from pylayout.routing import Port
from pylayout.shapes import SimplePolygon, Path, Text

import copy


class Builder(ParameterContainer):
    def __init__(self, **kwargs):
        super(Builder, self).__init__(**kwargs)
        self.rebuild()

    def build(self):...
    
    def clear(self):...

    def rebuild(self):
        self.on_clear()
        self.clear()
        self.before_build()
        self.build()
        self.after_build()

    #
    # Lifecycle hooks
    #
    def on_clear(self):
        pass

    def before_build(self):
        pass

    def after_build(self):
        pass


class BuildParameter(Parameter):
    """ defines a construction parameter used by blueprints """
    def _set(self, parent, value):
        super()._set(parent, value)
        
        # rebuild the parent to reflect the change!
        parent.rebuild()


class TraceTemplate(Builder):
    """ defines a multilayer mask template used to define 
        cross-section profiles available by the process (ex. metal traces or waveguides)
    """
    def __repr__(self):
        return self.__class__.__name__
    
    def clear(self):
        self.spec = dict()

    def add(self, layer: ProcessLayer, width, offset=0):
        if type(width) is list:
            for i, w in enumerate(width):
                if type(offset) is list:
                    assert len(offset) == len(width)
                    self.add(layer, w, offset[i])
                else:
                    self.add(layer, w, offset)
        else:
            if not layer in self.spec:
                self.spec[layer.name] = set()
            self.spec[layer.name].add((layer, width, offset))


class ComponentBuilder(Builder):
    """ defines a blueprint for creating layout components """        

    def __repr__(self):
        return self.unique_name()

    def clear(self):
        self.shapes = list()
        self.ports = dict()

    def get_bounds(self):
        xy = []
        for layer, shape in self.shapes:
            xy.extend(shape.get_points())
        for port in self.ports.values():
            xy.append(port.position)
        return AABB().fit(xy)

    def unique_name(self):
        return self.__class__.__name__

    def insert(self, layer: ProcessLayer, shape,  scale=1.0, rotation=0.0, translation=(0,0)):
        """ insert shape into component process layer
        
        input:
            layer - ProcessLayer
            shape - SimplePolygon, Path, Text or a list of points Nx2 to construct a polygon shape
        """

        self.before_insert()

        if isinstance(shape, list):
            shape = SimplePolygon(shape)

        if not isinstance(shape, (SimplePolygon, Path, Text)):
            raise ValueError('Invalid shape type supplied to insert()')
        
        # always keep a copy, not a ref
        item = shape.copy()
        item.transform(
            scale, 
            rotation, 
            translation)

        self.shapes.append((layer, item))

        self.after_insert()

    def port(self, name, position, direction='e', width=1.0):
        """ define a new port by name at position with given direction and width """
        self.before_port_define()

        self.ports[name] = Port(name, position, direction, width)
        
        self.after_port_define()

    #
    # Lifecycle hooks
    #

    def before_insert(self):
        pass

    def after_insert(self):
        pass

    def before_port_define(self):
        pass

    def after_port_define(self):
        pass


class DeviceBuilder(Builder):
    """ Builder/generator pattern at the device layout level allows creating standardized device layouts made of components, routes and ports """
    pass


class Waveguide(ComponentBuilder):
    """ Defines a parametric waveguide builder that smoothly interpolates a path to generate multilayer traces
    
    input:
        template     - (require) TraceTemplate, Waveguide layer template used when interpolating path
        points       - (require) list, Points defining the waveguide path to interpolate
        core_width   - (require) number, Waveguide core width
        radius       - (require) number, Radius used when creating bends of any kind
        bezier       - number, Method for cunstructing bends along the waveguide
        tolerance    - number, Tolerance for bend interpolation defines the mesh precision
        precision    - number, Unit precisision to snap points to
        augmented    - boolean, Automatically taper segments to wide sections when long enough
        aug_width    - number, Width of wide sections when tapers option is true
        aug_template - TraceTemplate, If a layer template is provided, use it instead of fixed width
        taper_length - number, Length of tapers when tapers option is true
    """

    template        = BuildParameter(type=TraceTemplate, required=True, description='Waveguide layer template used when interpolating path.')
    points          = BuildParameter(type=list, required=True, description='Points defining the waveguide path to interpolate.')
    core_width      = BuildParameter(0.5, required=True, description='Waveguide core width.')
    radius          = BuildParameter(10.0, required=True, description='Radius used when creating bends of any kind.')
    bezier          = BuildParameter(0.45, description='Method for cunstructing bends along the waveguide.')
    tolerance       = BuildParameter(0.01, description='Tolerance for bend interpolation defines the mesh precision.')
    precision       = BuildParameter(1e-9, description='Unit precisision to snap points to.')
    augmented       = BuildParameter(False, description='Automatically taper segments to wide sections when long enough.')
    aug_width       = BuildParameter(3, description='Width of wide sections when tapers option is true.')
    aug_template    = BuildParameter(False, description='If a layer template is provided, use it instead of fixed width.')
    taper_length    = BuildParameter(10, description='Length of tapers when tapers option is true.')

    # def unique_name(self):
    #     return ''.join(['Waveguide('
    #         "template=%s, "       % self.template,
    #         "core_width=%s, "     % self.core_width,
    #         "radius=%s, "         % self.radius,
    #         "bezier=%s, "         % self.bezier,
    #         "augmented=%s, "      % self.augmented,
    #         "start=(%.1f,%.1f), " % tuple(self.points[0]) ,
    #         "end=(%.1f,%.1f)"     % tuple(self.points[-1]),
    #         ')'])

    def build(self):
        for i in range(1, len(self.points)-1):
            (x1, y1), (x2, y2), (x3, y3) = self.points[i-1], self.points[i], self.points[i+1]
            if ((x1 - x2)*(x3 - x2) + (y1 - y2)*(y3 - y2)) > 0:
                _pylayout_warning("the angle at the corner {} is less than 90 degrees!".format(self.points[i]))

        tpl_layer_names = set(self.template.spec.keys())
        tpr_layer_names = set()
        
        if self.aug_template:
            tpr_layer_names = set(self.aug_template.spec.keys())
            if not tpl_layer_names <= tpr_layer_names:
                raise ValueError("Taper template must contain the same layers as the waveguide template!")

        for layer_name, triplet in self.template.spec.items():
            for layer, width, offset in triplet:
                
                if self.radius < 2 * width:
                    # TODO: if the trace is offset, should check with that radius??
                    _pylayout_warning("the waveguide trace width %s on layer %s is too large for the requested bend radius!" % (width, layer.name))

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
                        _pylayout_warning("the waveguide trace width %s on layer %s is too large for the requested bend radius!" % (width, layer.name))

                    path = self._trace_path(
                        self.points,
                        self.core_width,
                        offset,
                        aug_width,
                        self.radius,
                        self.bezier)

                    self.insert(layer, path)
        
        self.port('opt1', path.end(), path.end_direction(), self.core_width)
        self.port('opt2', path.start(), path.start_direction(), self.core_width)

    def _trace_path(self, points, width, offset, taper_width, radius, bezier):

        if len(points) < 3:
            return Path(points, width, offset)

        # this method mutates the points array!
        points = copy.deepcopy(points)

        _taper = False
        _corner = False

        def _make_wide(path, n, segment_length, taper_length, taper_width):
            segment_length -= 2 * taper_length
            path.by(n * taper_length, taper_width)
            path.by(n * segment_length, taper_width)
            # don't add the last taper, it well be generated automatically

        def _make_bend(path, p1, p2, p3, width, radius, bezier):
            v1.normalize()
            v2.normalize()

            path.to(
                p2 + v1 * radius, width)
            path.interp(
                p2 + v1 * radius * bezier,
                p2 + v2 * radius * bezier,
                p2 + v2 * radius
            , width, relative=False)
        

        path = Path(
            points[0],
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
                    if v1.length() - 2*radius < 0:
                        _pylayout_exception("Distance between consecutive corners is too short to accomodate bend radius at {}".format(p2))
                
                if v1.length() - radius <= 0:
                    _pylayout_exception("Segment length is too short to accomodate bend radius at corner {}".format(p2))

                # NOTE: assuming the upcoming point p3 is NOT a corner (it will be checked anyway in the next iteration)
                if v2.length() - radius <= 0:
                    _pylayout_exception("Segment length is too short to accomodate bend radius at corner {}".format(p2))

                _make_bend(path, p1, p2, p3, width, radius, bezier)

                # if ccw(p1, p2, p3) > 1:
                #     path.bend(radius, -90.0, method='circular', b=bezier, width=width)
                # else:
                #     path.bend(radius, 90.0, method='circular', b=bezier, width=width)

                _taper = False  # reset _taper to false as we never instert tapers in the p2-p3 segment when doing corners!
                _corner = True
                
            i += 1

        path.to(points[-1], width)
        
        return path