from PySide2.Qt import *
from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtWidgets import *

from model import *

import math
import random


class ViewLayer(QGraphicsItemGroup):
    """
    Group containing similar styled objects

    """

    def __init__(self, layer: int, dtype: int, pen: QPen, brush: QBrush, model: Layer):
        super(ViewLayer, self).__init__()

        self.pen = pen
        self.brush = brush

        # add signal connections
        model.item_inserted.connect(self.on_ItemAdded)
        model.item_removed.connect(self.on_ItemRemoved)

    def addPolygon(self, item: QGraphicsPolygonItem):
        item.setPen(self.pen)
        item.setBrush(self.brush)
        self.addToGroup(item)
    
    def removePolygon(self, item: QGraphicsPolygonItem):
        self.removeFromGroup(item)

    def clear(self):
        for i in self.childItems():
            self.removeFromGroup(i)

    def scaleBrushes(self, scale):
        self.brush.setTransform(self.brush.transform().scale(scale,scale))
        for i in self.childItems():
            i.setBrush(self.brush)

    def on_ItemAdded(self, item: Element):
        if item.type == ElementType.Boundary:
            self.addPolygon(QGraphicsPolygonItem(QPolygonF(item.xy)))
    
    def on_ItemRemoved(self, item: Element):
        pass

class LayoutView(QGraphicsView): ...

class ViewLayers(QObject):
    """
    Visual representation of model layers containing graphics elements

    """

    def __init__(self, view: LayoutView):
        super(ViewLayers, self).__init__()

        self.scene = view.scene
        self.layers = dict()

        view.view_scaled.connect(self.on_ViewScaleChange)

    def addLayer(self, layer: int, dtype: int, pen: QPen, brush: QBrush, model: Layer):
        item = ViewLayer(layer, dtype, pen, brush, model)
        self.scene.addItem(item)
        self.layers[(layer, dtype)] = item

    def removeLayer(self, layer: int, dtype: int):
        item = self.layers[(layer, dtype)]
        self.scene.removeItem(item)
        self.layers.pop((layer, dtype))

    def clear(self):
        for i in self.layers:
            self.layers[i].clear()
        self.layers.clear()

    def addPolygon(self, layer: int, dtype: int, item: QGraphicsPolygonItem):
        l = self.layers.get((layer, dtype))
        if l: l.addPolygon(item)

    def addText(self, layer: int, dtype: int, item: QGraphicsSimpleTextItem):
        l = self.layers.get((layer, dtype))
        if l: l.addText(item)

    def on_VisibilityChange(self, layer: int, dtype: int, visible: bool):
        l = self.layers.get((layer, dtype))
        if l is not None:
            if visible:
                l.show()
            else:
                l.hide()

    def on_ViewScaleChange(self, scale: float):
        for key, layer in self.layers.items():
            layer.scaleBrushes(1/scale)


class LayoutView(QGraphicsView):
    """
    Widget representing the main view into the layout

    This is the main view widget that holds the graphics scene and displays
    overlays to help the user interact with the view. This widget offers
    responsive zomming, panning and rotation of the scene view.
    """

    view_scaled = Signal(float)
    mouse_moved = Signal(int, int)
    layer_added = Signal(int, int, str, QPen, QBrush)
    layer_removed = Signal(int, int)

    gridLinesPerRow = 20
    gridLinesScaleInc = 10

    def __init__(self, model: Layout):
        super(LayoutView, self).__init__()

        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.view_layers = ViewLayers(self)

        self.grabGesture(Qt.PinchGesture)
        self.setResizeAnchor(self.NoAnchor)
        self.setTransformationAnchor(self.AnchorUnderMouse)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, False)
        self.setBackgroundBrush(QBrush(Qt.white))

        # keep track of viewport state
        unit = model.logical_unit * model.physical_unit
        # TODO: actually get the model's view rect dimensions for max zoom factor = unit / max_size
        self.units = 100*unit
        self.limits = (0.001, 1/unit)
        self.angle = 0
        self.origin = QPointF()
        self.scale = 1

        # add signal connections
        model.layer_added.connect(self.on_LayerAdded)
        model.layer_removed.connect(self.on_LayerRemoved)

        self.fitInView()

    def event(self, evt: QEvent):
        if isinstance(evt, QGestureEvent):
            if evt.gesture(Qt.PinchGesture):

                pinch = evt.gesture(Qt.PinchGesture)

                if pinch.rotationAngle():
                    newAngle = pinch.rotationAngle()
                    delta = self.angle - newAngle
                    self.rotate(-delta)
                    self.angle = newAngle

                else:
                    self.angle = 0
                
                if pinch.ScaleFactorChanged:
                    self.zoom(pinch.scaleFactor())

            elif evt.gesture(Qt.PanGesture):

                pan = evt.gesture(Qt.PanGesture)
                self.pan(pan.delta().x(), pan.delta().y())

        return super().event(evt)

    def mouseMoveEvent(self, evt: QMouseEvent):
        newPos = self.mapToScene(evt.pos())
        self.mouse_moved.emit(newPos.x(), newPos.y())

        if evt.button() == Qt.LeftButton:
            delta = newPos - self.origin
            self.translate(delta.x(), delta.y())
            self.origin = newPos

        else:
            self.origin = newPos

    def drawBackground(self, painter: QPainter, rect: QRect):
        super().drawBackground(painter, rect)

        # draw the grid lines
        gridPen = QPen(QBrush(Qt.darkGray), 2)
        gridPen.setCosmetic(True)
        gridPen.setDashPattern([1,10])

        x0 = math.floor(rect.center().x() / self.units) * self.units
        y0 = math.floor(rect.center().y() / self.units) * self.units

        nx = math.ceil(rect.width() / self.units / 2) + 1
        xpos = [x0 + x*self.units for x in range(-nx,nx)]

        ny = math.ceil(rect.height() / self.units / 2) + 1
        ypos = [y0 + y*self.units for y in range(-ny,ny)]

        painter.setPen(gridPen)
        for i, x in enumerate(xpos):
            painter.drawLine(x, rect.bottom(), x, rect.top())
        for i, y in enumerate(ypos):
            painter.drawLine(rect.left(), y, rect.right(), y)

    def updateGrid(self):
        rect = self.mapToScene(self.viewport().geometry()).boundingRect()
        self.units = 1
        while (rect.width() / self.units / self.gridLinesPerRow) > 1:
            self.units *= self.gridLinesScaleInc

    def zoom(self, factor: float):
        if self.limits[0] < abs(factor * self.transform().m11()) < self.limits[1]:
            self.scale(factor, factor)
            self.scale = factor
            self.updateGrid()
            self.view_scaled.emit(factor)

    def rotate(self, angle: float):
        super().rotate(angle)

    def pan(self, dx: float, dy: float):
        super().translate(dx, dy)

    def fitInView(self):
        self.resetTransform()
        self.updateGrid()
        super().fitInView(
            self.scene.itemsBoundingRect(), 
            Qt.KeepAspectRatio)

        self.scale = self.transform().m33()
        self.view_scaled.emit(self.scale)
        self.mouse_moved.emit(self.x(), self.y())

    def on_LayerAdded(self, layer: int, dtype: int, model: Layer):
        pen = QPen(QBrush(model.base_color), 0)
        brush = QBrush(model.base_color, model.pattern)
        self.view_layers.addLayer(layer, dtype, pen, brush, model)
        self.layer_added.emit(layer, dtype, model.name, pen, brush)

    def on_LayerRemoved(self, layer: int, dtype: int):
        self.view_layers.removeLayer(layer, dtype)
        self.layer_removed.emit(layer, dtype)


class LayersListItem(QListWidgetItem):

    w, h = 40, 20

    def __init__(self, layer: int, dtype: int, name: str, pen: QPen, brush: QBrush):
        super(LayersListItem, self).__init__()

        self.layer = layer
        self.dtype = dtype
        self.shown = True
        self.pen = pen
        self.brush = brush

        text = "({}/{})".format(str(layer), str(dtype))
        if len(name) > 0:
            text = "{}\t{}".format(name, text)

        self.setFont(QFont('Arial', 14, 100))
        self.setText(text)
        self.setPixmap()

    def toggleVisibility(self):
        self.shown = not self.shown
        self.setPixmap()

    def setPixmap(self):

        m = QPixmap(self.w+1, self.h+1)
        m.fill(Qt.transparent)

        p = QPainter(m)
        p.setPen(self.pen)
        if self.shown:
            p.fillRect(m.rect(), self.brush)
        p.drawRect(0, 0, self.w, self.h)
        p.end()

        self.setIcon(QIcon(m))


class LayersList(QListWidget):
    """
    List widget showing all layers used by the layout

    Double clicking an item in the list will toggle the layer visibility in view
    """

    visibility_changed = Signal(int, int, bool)

    def __init__(self):
        super(LayersList, self).__init__()

        self.setIconSize(QSize(40,20))
        self.setSelectionMode(self.ExtendedSelection)
        self.itemDoubleClicked.connect(self.on_DblClick)

    def on_DblClick(self, item: LayersListItem):
        item.toggleVisibility()
        self.visibility_changed.emit(item.layer, item.dtype, item.shown)


class LayersPalette(QDockWidget):
    """
    Widget listing all active and inactive layers used by the layout

    This widget is docked by the main view and allows hiding and showing of
    layers in the layout via double click events on the items.
    """

    def __init__(self, view: LayoutView):
        super(LayersPalette, self).__init__()

        self.list = LayersList()
        self.setWidget(self.list)
        self.setWindowTitle("Layers")

        # add signal connections
        view.layer_added.connect(self.on_LayerAdded)
        view.layer_removed.connect(self.on_LayerRemoved)

    def clear(self):
        self.list.clear()

    def on_LayerAdded(self, layer: int, dtype: int, name: str, pen: QPen, brush: QBrush):
        self.list.addItem(LayersListItem(layer, dtype, name, pen, brush))

    def on_LayerRemoved(self, layer: int, dtype: int):
        for i in self.list.items():
            if i.layer == layer and i.dtype == dtype:
                self.list.removeItemWidget(i)


class ViewerMenuBar(QMenuBar):
    def __init__(self, parent: QMainWindow):
        super(ViewerMenuBar, self).__init__(parent)

        fileMenu = self.addMenu("&File")

        openAction = fileMenu.addAction("&Open")
        openAction.setStatusTip('Open GDS file...')

        fileMenu.addSeparator()

        closeAction = fileMenu.addAction("Clos&e")


class Viewer(QMainWindow):
    """
    Main window widget
    
    The main window houses the layout view, the layers palette and a simple
    menu for loading/unloading gds files and interacting with the view
    """

    def __init__(self, model: Layout):
        super(Viewer, self).__init__()

        self.model = model

        self.view = LayoutView(model)
        self.setCentralWidget(self.view)

        self.layers_palette = LayersPalette(self.view)
        self.addDockWidget(Qt.RightDockWidgetArea, self.layers_palette, Qt.Vertical)
        # connect list double click event to view_layers change visibility
        self.layers_palette.list.visibility_changed.connect(self.view.view_layers.on_VisibilityChange)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.positionStatus = QLabel("xy: {1:.2f} {1:.2f}".format(0, 0))
        self.status.addPermanentWidget(self.positionStatus, 1)

        self.menu = ViewerMenuBar(self)
        self.setMenuBar(self.menu)

        # add signal connections
        self.view.view_scaled.connect(self.on_ViewScaled)
        self.view.mouse_moved.connect(self.on_MouseMoved)

    def keyPressEvent(self, evt: QKeyEvent):
        if evt.key() == Qt.Key_Escape:
            self.close()

        if evt.key() == Qt.Key_F:
            self.fitInView()

        d = self.view.sceneRect().width() / 2

        if evt.key() == Qt.Key_Up:
            self.view.pan(0, +d)

        if evt.key() == Qt.Key_Down:
            self.view.pan(0, -d)

        if evt.key() == Qt.Key_Left:
            self.view.pan(-d, 0)

        if evt.key() == Qt.Key_Right:
            self.view.pan(+d, 0)

    def zoom(self, factor: float):
        self.view.scale(factor, factor)

    def rotate(self, angle: float):
        self.view.rotate(angle)

    def pan(self, dx: float, dy: float):
        self.view.pan(dx, dy)

    def fitInView(self):
        self.view.fitInView()

    def on_ViewScaled(self, factor: float):
        pass

    def on_MouseMoved(self, x: int, y: int):
        self.positionStatus.setText("xy: {1:.2f} {1:.2f}".format(x, y))