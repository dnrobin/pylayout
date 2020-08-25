from ..core import Transforms

class Shape(Transforms):
    """Geometric shape encapsulating masked areas

    Arguments
    _________
    """
    def __init__(self, xy=[]):
        super().__init__()

        self.xy = xy
    
    def to_gds(self, layer, dtype, unit=1e-6, precision=1e-9):
        """ Convert this shape to gdspy primitive """
        from gdspy import Polygon

        return Polygon(self.transform(self.xy, unit, precision), layer, dtype)
