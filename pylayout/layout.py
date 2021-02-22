from typing import Any


class Array:
    """ Rectangular array of points """
    def __init__(self, item: Any, rows, cols, pitch=(1,1)):
        pass


class PolarArray:
    """ Array layed out in arcs """
    def __init__(self, item: Any, a1=0, a2=90, r1=1, r2=2, Na=10, Nr=10):
        pass


class Lattice:
    """ Arbitrary lattice of points """
    def __init__(self, item: Any, rows=10, cols=10, e1=1, e2=1, angle=90):
        pass