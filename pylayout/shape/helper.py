from .shape import Shape

class Circle(Shape):
    def __init__(self, center=(0,0), r=1.0, tol=.01, **kwargs):
        """ create a circle shape of radius r at center point """
        super().__init__([], **kwargs)

        from math import pi, cos, sin

        angles = [(t*tol) * 2*pi for t in range(0,int(1//tol) + 1)]
        for a in angles:
            self.xy.append([
                r * cos(a) + center[0],
                r * sin(a) + center[1]
            ])


class Rect(Shape):
    def __init__(self, p1, p2, **kwargs):
        """ create a rectangle shape from lower-left (p1) point to upper right point (p2) """
        super().__init__([], **kwargs)

        self.xy = [
            (p1[0], p1[1]),
            (p1[0], p2[1]),
            (p2[0], p2[1]),
            (p2[0], p1[1])
        ]