from pylayout.core import _pylayout_notice, _pylayout_warning, _pylayout_exception
from pylayout.math import pi, radians, cos, sin, sgn, Vec, QuickPath
from pylayout.utils import direction_angle
from pylayout.process import DesignRules


class Port:
    """ Defines a component input/output port used for routing 
    
    A port must always define a position, a width and an outward direction. Every component 
    should define at least one port in its ports dictionary and attach shapes to it.
    """
    def __init__(self, name, position, direction='e', width=1.0):
        """
        input:
            position - port center position (x, y)
            width - port width: float
            direction - outward direction, one of: {'e', 'ne', 'n', 'nw', 'w', 'sw', 's', 'se'} or angle in *degrees*
        """
        self.name = name
        self.width = width
        self.position = position
        self.direction = direction_angle(direction)

    def __repr__(self):
        return "Port '%s': at %s width: %s, direction: %s" % (self.name, self.position, self.width, self.direction)


class Connection:
    class RouteTarget:
        def __init__(self, position, direction):
            self.position = position
            self.direction = direction_angle(direction)
    

    def __init__(self, port1: Port, port2: Port, unit=1, precision=1e-3):
        if not (port1.width == port2.width):
            _pylayout_exception("Incompatible ports with different widths while creating connection!")

        self.port1 = port1
        self.port2 = port2
        self.width = port1.width

        self._unit = unit
        self._precision = precision
        self._rules = DesignRules(unit, precision)

    def _route(self, p1, p2, d1, d2, spacing, in_clearence=0.0, out_clearence=0.0):
        is_orth_d1 = (round(d1) % 90.0 == 0)
        is_orth_d2 = (round(d2) % 90.0 == 0)

        _s = QuickPath(p1, d1, self._unit, self._precision)         # start path
        _e = QuickPath(p2, d2-180.0, self._unit, self._precision)   # end path

        _s.forward(spacing + in_clearence)
        _e.forward(spacing + out_clearence)
        
        d1 = radians(round(d1 / 90.0) * 90.0)
        d2 = radians(round(d2 / 90.0) * 90.0)

        v2 = Vec(cos(d2), sin(d2))

        n = Vec(cos(d1), sin(d1))
        t = Vec(n[1], -n[0])
        v = _e.end() - _s.end()
        dn, dt = n.dot(v), t.dot(v)
        v.normalize()

        def _kind(v1, v2, v):
            d = v1.dot(v2)
            e = v.cross(v2)
            if abs(d) > 0:
                if d > 0:
                    return 0        # same direction
                else:
                    if v.dot(v1) > 0:
                        return 1    # facing eachother
                    else:
                        return 2    # facing away (back to back)
            else:
                if v.cross(v1) > 0:
                    if e <= 0:
                        return 3    # CW turn
                else:
                    if e > 0:
                        return 4    # CCW turn

            return -1               # pathological case

        k = _kind(n, v2, v)

        if k < 0:
            _pylayout_notice("the routing is not optimal for the port orientations. Consider adding constraints or targets.")

        if k == 2 and abs(dt) < spacing:
            _pylayout_warning("lateral spacing is too small to insert s-bend with the given radius!")

        # print('before: k', k, 'dn', dn, 'dt', dt, 'space', spacing)

        if dn < 0:                  ## move along t first

            if abs(dt) < spacing:
                dt = sgn(dt) * (spacing + abs(dt))

            if k < 1:
                dt = dt / 2
                if abs(dt) < spacing:
                    _pylayout_warning("space between ports is too narrow to fit bend!")

            if k != 0 and abs(dn) < spacing:
                _s.by(n * (spacing - abs(dn)))
                dn = sgn(dn) * spacing

            _s.by(t*dt)
            _s.by(n*dn)

        else:                       ## move along n first

            # try to remove needless start/end spacing
            # if is_orth_d1:
            #     _s.remove(-1)
            # if k == 2 and is_orth_d2:
            #     _e.remove(-1)

            if abs(dn) < spacing:
                dn = sgn(dn) * (spacing + abs(dn))

            if k < 1:
                dn = dn / 2
                if abs(dn) < spacing:
                    _pylayout_warning("space between ports is too narrow to fit bend!")
            
            if k != 0 and abs(dt) < spacing:
                _e.by(t * (spacing - abs(dt)))
                dt = sgn(dt) * spacing
                # NOTE: this could break some cases...
                if k == 1:
                    dn = dn / 2

            _s.by(n*dn)
            _s.by(t*dt)

        # print('after: k', k, 'dn', dn, 'dt', dt, 'space', spacing)

        _s.extend(_e.reverse())

        return _s

    def route(self, bend_radius=None, in_clearence=0.0, out_clearence=0.0, targets=None, rules=None):
        """ Generate a path linking port1 and port2 with manhattan segments respecting bend spacing, design rules and port orientations 
        
        input:
            bend_radius - number or None, the radius of curvature of bends for waveguides or None for metal traces
            rules - DesignRules, provide specific design rules for this route
            targets - RouteTarget or list or targets, targets the route must pass through
        """
        
        if rules is None:
            rules = self._rules

        spacing = rules['MIN_WIDTH'].value + rules['MIN_SPACE'].value

        if not bend_radius is None:
            if bend_radius < 2 * self.width:
                _pylayout_exception("A radius of %s is too small to accomodate the path width of %s!" % (bend_radius, self.width))

            if bend_radius < spacing:
                _pylayout_exception("The bend radius %s is smaller than the minimum spacing or %s!" % (bend_radius, spacing))

        min_spacing = max(bend_radius * 2, spacing)

        p1 = self.port1.position
        p2 = self.port2.position

        dx, dy = p2[0] - p1[0], p2[1] - p1[1]

        if (dx ** 2 + dy ** 2) < 4 * min_spacing ** 2:
            _pylayout_exception("The points %s, %s are too close to be routed with the given spacing!" % (p1, p2))

        d1 = direction_angle(self.port1.direction)
        d2 = direction_angle(self.port2.direction) + 180.0    # make d2 point along path from p1 to p2

        # TODO: validate targets are possible?

        if isinstance(targets, list):
            path = self._route(p1, targets[0].position, d1, targets[0].direction, min_spacing, in_clearence, out_clearence)

            for i in range(1, len(targets)):
                path.extend(self._route(
                    targets[i-1].position, 
                    targets[i].position, 
                    targets[i-1].direction, 
                    targets[i].direction, 
                    min_spacing,
                    in_clearence, out_clearence))

            path.extend(self._route(targets[-1].position, p2, targets[-1].direction, d2, min_spacing, in_clearence, out_clearence))

        elif isinstance(targets, self.RouteTarget):
            path1 = self._route(p1, targets.position, d1, targets.direction, min_spacing, in_clearence, out_clearence)
            path2 = self._route(targets.position, p2, targets.direction, d2, min_spacing, in_clearence, out_clearence)
            path = path1 + path2

        else:
            path = self._route(p1, p2, d1, d2, min_spacing, in_clearence, out_clearence)
        
        return path.clean()