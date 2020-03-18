from PySide2.QtCore import *
from PySide2.QtGui import *

import gdspy

import math
import random

class ElementType(object):
    Boundary = 1
    Text     = 2


class Element(object):
    type: ElementType


class Boundary(Element):
    type = ElementType.Boundary

    def __init__(self, xy: list):
        self.xy = xy


class Layer(QObject):
    """
    Model containing layout elements of the same layer/dtype category
    """

    item_inserted = Signal(Element)
    item_removed = Signal(Element)

    _forw = True

    def __init__(self
        , layer: int            # layer number
        , dtype: int            # data type
        , name: str = ''       # optional name
        , base_color: QColor = None
        , pattern: Qt.BrushStyle = None
        ):
        
        super(Layer, self).__init__()

        self.layer = layer
        self.dtype = dtype
        self.name = name

        if base_color is None:
            r = random.randint(50, 220)
            g = random.randint(80, 200)
            b = random.randint(80, 200)
            base_color = QColor(r, g, b)

        self.base_color = base_color

        if pattern is None:
            Layer._forw = not Layer._forw
            if Layer._forw:
                pattern = Qt.FDiagPattern
            else:
                pattern = Qt.BDiagPattern
        
        self.pattern = pattern

        self.elements = list()

    def insert(self, item: Element):
        self.elements.append(item)
        self.item_inserted.emit(item)

    def remove(self, item: Element):
        self.elements.remove(item)
        self.item_removed.emit(item)


class Layout(QObject):
    """
    Model containing layout elements grouped in layer/dtype category
    """

    layer_added = Signal(int, int, Layer)
    layer_removed = Signal(int, int)

    def __init__(self 
        , physical_unit: float = 1e-9   # size of base unit in meters (ex. nm would be 1e-9)
        , logical_unit: float = 1e3     # size of display unit in base units (ex. um would be 1e3 if base was 1e-9)
        , name: str = ''
        ):

        super(Layout, self).__init__()

        self.physical_unit = physical_unit
        self.logical_unit = logical_unit
        self.name = name

        self.layers = dict()

    def addLayer(self, layer: int, dtype: int, name: str = '', base_color: QColor = None):
        if (layer, dtype) in self.layers:
            return
        
        self.layers[(layer, dtype)] = Layer(layer, dtype, name, base_color)
        self.layer_added.emit(layer, dtype, self.layers[(layer, dtype)])

    def removeLayer(self, layer: int, dtype: int):
        if (layer, dtype) in self.layers:
            self.layers.pop((layer, dtype))
            self.layer_removed.emit(layer, dtype)

    def getLayer(self, layer: int, dtype: int):
        return self.layers.get((layer, dtype))

    def insert(self, layer: int, dtype: int, item: Element):
        if (layer, dtype) not in self.layers:
            self.addLayer(layer, dtype)
        
        self.layers[(layer, dtype)].insert(item)

    def remove(self, layer: int, dtype: int, item: Element):
        if (layer, dtype) in self.layers:
            self.layers[(layer, dtype)].remove(item)

    def clear(self):
        self.layers.clear()

    def set(self, lib: gdspy.GdsLibrary):
        self.physical_unit = lib.precision
        self.logical_unit = lib.unit
        self.name = lib.name

        for cell in lib.top_level():
            self.loadCell(cell)

    def loadCell(self, cell: gdspy.Cell):
        scale = 1 #/ (self.logical_unit * self.physical_unit)

        print(cell)

        # for ref in cell.references:
        #     ref = gdspy.CellReference()
        #     ref.
        
        for info, polygon in cell.get_polygons(True).items():
            for pol in polygon:
                xy = list()
                for p in pol:
                    xy.append(QPointF(
                        p[0] * scale, 
                        p[1] * scale
                    ))
                
                self.insert(info[0], info[1], Boundary(xy))


def loadGdsFromFile(infile: str) -> Layout:
    return gdspy.GdsLibrary().read_gds(infile)

