from pylayout.math import pi, radians, cos, sin, sgn, Vec, QuickPath
from pylayout.utils import direction_angle
from pylayout.process import DesignRules


class Port:
    """ Defines a component input/output port used for routing 
    
    A port must always define a position, a width and an outward direction. Every component 
    should define at least one port in its ports dictionary and attach shapes to it.
    """
    def __init__(self, position, width=1.0, direction='e'):
        """
        input:
            position - port center position (x, y)
            width - port width: float
            direction - outward direction, one of: {'e', 'ne', 'n', 'nw', 'w', 'sw', 's', 'se'} or angle in *degrees*
        """
        self.width = width
        self.position = position
        self.direction = direction_angle(direction)

    def __repr__(self):
        return "Port %s width: %s, direction: %s" % (self.position, self.width, self.direction)


class Connection:
    class RouteTarget:
        def __init__(self, position, direction):
            self.position = position
            self.direction = direction_angle(direction)
    

    def __init__(self, port1: Port, port2: Port, unit=1, precision=1e-3):
        assert port1.width == port2.width

        self.port1 = port1
        self.port2 = port2
        self.width = port1.width

        self._unit = unit
        self._precision = precision
        self._rules = DesignRules(unit, precision)

    def _route(self, p1, p2, d1, d2, min_spacing):
        _s = QuickPath(p1, d1, self._unit, self._precision)         # start path
        _e = QuickPath(p2, d2-180.0, self._unit, self._precision)   # end path

        _s.forward(min_spacing)
        _e.forward(min_spacing)

        d1 = radians(round(d1 / 90.0) * 90.0)
        d2 = radians(round(d2 / 90.0) * 90.0)

        v2 = Vec(cos(d2), sin(d2))

        n = Vec(cos(d1), sin(d1))
        t = Vec(n[1], -n[0])
        v = _e.end() - _s.end()
        dn, dt = Vec(n.dot(v), t.dot(v))
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
            print("Notice: the routing is not optimal for the port orientations. Consider adding constraints or targets.")

        if k == 2 and abs(dt) < min_spacing:
            print("Route Warning: lateral spacing is too small to insert s-bend with the given radius!")

        # print('before: k', k, 'dn', dn, 'dt', dt, 'space', min_spacing)

        if dn < 0:  # move perpendiculare first

            if abs(dt) < min_spacing:
                dt = sgn(dt) * (min_spacing + abs(dt))

            if k < 1:
                dt = dt / 2
                if abs(dt) < min_spacing:
                    print("Route Warning: space between ports is too narrow to fit bend!")

            if k != 0 and abs(dn) < min_spacing:
                _s.move_by(n * (min_spacing - abs(dn)))
                dn = sgn(dn) * min_spacing

            _s.move_by(t*dt)
            _s.move_by(n*dn)

        else:       # move forward first

            if abs(dn) < min_spacing:
                dn = sgn(dn) * (min_spacing + abs(dn))

            if k < 1:
                dn = dn / 2
                if abs(dn) < min_spacing:
                    print("Route Warning: space between ports is too narrow to fit bend!")
            
            if k != 0 and abs(dt) < min_spacing:
                _e.move_by(t * (min_spacing - abs(dt)))
                dt = sgn(dt) * min_spacing
                # NOTE: this could break some case...
                if k == 1:
                    dn = dn / 2

            _s.move_by(n*dn)
            _s.move_by(t*dt)

        # print('after: k', k, 'dn', dn, 'dt', dt, 'space', min_spacing)

        _s.extend(_e.reverse())

        return _s

    def route(self, bend_radius=None, targets=None, rules=None):
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
                raise ValueError("A radius of %s is too small to accomodate the path width of %s!" % (bend_radius, self.width))

            if bend_radius < spacing:
                raise ValueError("The bend radius %s is smaller than the minimum spacing or %s!" % (bend_radius, spacing))

        min_spacing = max(bend_radius * 2, spacing)

        p1 = self.port1.position
        p2 = self.port2.position

        dx, dy = p2[0] - p1[0], p2[1] - p1[1]

        if (dx ** 2 + dy ** 2) < 4 * min_spacing ** 2:
            raise ValueError("The points %s, %s are too close to be routed with the given spacing!" % (p1, p2))

        d1 = direction_angle(self.port1.direction)
        d2 = direction_angle(self.port2.direction) + 180.0    # make d2 point along path from p1 to p2

        # TODO: validate targets are possible?

        if isinstance(targets, list):
            path = self._route(p1, targets[0].position, d1, targets[0].direction, min_spacing)
            for i in range(1, len(targets)):
                path.extend(self._route(
                    targets[i-1].position, 
                    targets[i].position, 
                    targets[i-1].direction, 
                    targets[i].direction, 
                    min_spacing))

            path.extend(self._route(targets[-1].position, p2, targets[-1].direction, d2, min_spacing))

        elif isinstance(targets, self.RouteTarget):
            path1 = self._route(p1, targets.position, d1, targets.direction, min_spacing)
            path2 = self._route(targets.position, p2, targets.direction, d2, min_spacing)
            path = path1 + path2

        else:
            path = self._route(p1, p2, d1, d2, min_spacing)
        
        return path.clean()