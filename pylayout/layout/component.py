from ..core import *

class Component:
    """Fundamental building block for device layout

    Compoments are the building blocks of circuit layouts and are composed
    of shape primitives like simple polygons, paths and text labels attached 
    to process layers. They should always define at least one I/O port for 
    routing if they are to be used in circuits.

    Arguments
    ---------
    name : string, a unique name used to reference this component
    """

    def __init__(self, name):
        self.name = name
        self.ports = {}
        self.layers = {}

    def insert(self, layer, dtype, shape):
        """ insert shape into device layer """
        from copy import deepcopy

        key = (layer,dtype)
        if not key in self.layers:
            self.layers[key] = []
        
        self.layers[key].append(deepcopy(shape))

    def to_gds(self, unit=1e-6, precision=1e-9):
        """ convert this component to gdspy Cell object """
        from gdspy import Cell, FlexPath, Text, Polygon

        cell = Cell(self.name, exclude_from_current=True)
        for (layer,dtype), shapes in self.layers.items():
            for shape in shapes:
                cell.add(shape.to_gds(layer, dtype, unit, precision))

        return cell