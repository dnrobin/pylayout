from pylayout.math import radians, cos, sin, Vec, QuickPath
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


class Router:
    def __init__(self, port1: Port, port2: Port, unit=1, precision=1e-3):
        assert port1.width == port2.width
        self.port1 = port1
        self.port2 = port2
        self.width = port1.width

        self._unit = unit
        self._precision = precision

        self._rules = DesignRules(unit, precision)

    def route(self, bend_radius=None, rules=None):
        """ Generate a path linking port1 and port2 with manhattan segments respecting bend spacing, design rules and port orientations 
        
        input:
            bend_radius - number or None, the radius of curvature of bends for waveguides or None for metal traces
            rules - DesignRules, provide specific design rules for this route
        """

        if rules is None:
            rules = self._rules

        spacing = rules['MIN_WIDTH'].value + rules['MIN_SPACE'].value

        if not bend_radius is None:
            if bend_radius < 2 * self.width:
                raise ValueError("A radius of %s is too small to accomodate the path of width %s!" % (bend_radius, self.width))

            if bend_radius < spacing:
                raise ValueError("The bend radius %s is smaller than the minimum spacing or %s!" % (bend_radius, spacing))

        min_spacing = max(bend_radius * 1.1, spacing)

        p1 = self.port1.position
        p2 = self.port2.position

        dx, dy = p2[0] - p1[0], p2[1] - p1[1]

        if (dx ** 2 + dy ** 2) < 4 * min_spacing ** 2:
            raise ValueError("The points %s, %s are too close to be routed with the given spacing!" % (p1, p2))

        d1 = direction_angle(self.port1.direction)
        d2 = direction_angle(self.port2.direction) + 180.0    # make d2 point along path from p1 to p2

        path = QuickPath(p1, d1, self._unit, self._precision)
        path.forward(min_spacing)

        _p = QuickPath(p2, d2-180.0, self._unit, self._precision)
        _p.forward(min_spacing)

        d1 = radians(round(d1 / 90.0) * 90.0)
        d2 = radians(round(d2 / 90.0) * 90.0)

        v2 = Vec(cos(d2), sin(d2))

        n = Vec(cos(d1), sin(d1))
        t = Vec(n[1], -n[0])
        v = _p.end() - path.end()
        dn, dt = Vec(n.dot(v), t.dot(v))
        # print(dn, dt)
        v.normalize()

        def _kind(v1, v2, v):
            d = v1.dot(v2)
            e = v.cross(v2)
            if abs(d) > 0:
                if d <= 0:
                    if v.dot(v1) > 0:
                        return 1    # facing
                    else:
                        return 1    # facing away
            else:
                if v.cross(v1) > 0:
                    if e <= 0:
                        return 1    # CW turn
                else:
                    if e > 0:
                        return 1    # CCW turn
            return 0

        k = _kind(n, v2, v)

        if dn < 0:  # do dt first
            if not dt:
                dt = sgn(-v2.dot(t)) * 2 * min_spacing

            if not k:
                if abs(dt/2) < 2 * min_spacing:
                    raise ValueError("Path segment length at {} is too short to satisfy spacing limits!".format(path.end()))
                path.move_by(t*dt/2)
                path.move_by(n*dn)
            else:
                path.move_by(t*dt)
                path.move_by(n*dn)

        else:       # do dn first
            if not dn:
                dn = sgn(-v2.dot(n)) * 2 * min_spacing
            
            if not k:
                if abs(dn/2) < 2 * min_spacing:
                    raise ValueError("Path segment length at {} is too short to satisfy spacing limits!".format(path.end()))
                path.move_by(n*dn/2)
                path.move_by(t*dt)
            else:
                path.move_by(n*dn)
                path.move_by(t*dt)

        path.extend(_p.reverse())

        return path