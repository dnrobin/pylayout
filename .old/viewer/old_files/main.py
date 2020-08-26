from PySide2.Qt import *
from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtWidgets import *

import math
import random


class Layer(QGraphicsItemGroup):
    """ A collection of graphical items sharing common gds layer and dtype

    Grouping graphics objects into this container allows for runtime hide/show
    behavior triggered by the LayersPalette.

    """

    def __init__(self, layer: int, dtype: int, label: str, pen: QPen, brush: QBrush):
        super().__init__()

        self.pen = pen
        self.brush = brush

        self.layer = layer
        self.dtype = dtype
        # self.key   = (layer, dtype)

    def addPolygon(self, item: QGraphicsPolygonItem):
        item.setPen(self.pen)
        item.setBrush(self.brush)
        self.addToGroup(item)

    def addText(self, item: QGraphicsSimpleTextItem):
        item.setPen(self.pen)
        item.setBrush(self.brush)
        self.addToGroup(item)

    def scaleBrush(self, scale):
        self.brush.setTransform(
            self.brush.transform().scale(scale,scale))

        # reset the brush for all children...
        for i in self.childItems():
            i.setBrush(self.brush)


class Layout(object):
    """ Canvas to hold the graphical items to be rendered by the backend

    This object acts like the model for the LayoutView and LayersPalette 
    widgets which interact with its content.

    """

    def __init__(self, scene: QGraphicsScene):

        self.scene = scene
        self.layers = dict()

    def addLayer(self, layer: int, dtype: int, label: str, pen: QPen, brush: QBrush):
        if self.layers.get((layer, dtype)):
            return
        
        l = Layer(layer, dtype, label, pen, brush)

        self.scene.addItem(l)
        self.layers[(layer, dtype)] = l

    def getLayer(self, layer: int, dtype: int):
        l = self.layers.get((layer, dtype))
        if l: return l

        return None

    def addPolygon(self, layer: int, dtype: int, item: QGraphicsPolygonItem):
        l = self.layers.get((layer, dtype))
        if l: l.addPolygon(item)

    def addText(self, layer: int, dtype: int, item: QGraphicsSimpleTextItem):
        l = self.layers.get((layer, dtype))
        if l: l.addText(item)

    @Slot(float)
    def on_scale(self, scale):
        for layer in self.layers:
            self.layers[layer].scaleBrush(1 / scale)

