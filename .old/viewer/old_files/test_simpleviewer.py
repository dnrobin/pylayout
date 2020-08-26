from PySide2.Qt import *
from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtWidgets import *

import gdspy
import math
import random

class LayerInfo:
    def __init__(self, id, dt, label = '', color = ''):
        self.id = id
        self.dt = dt
        self.label = label

        if len(color):
            self.color = color
        else:
            c = QColor(random.random()*256)
            self.color = c.HexRgb


class Layer(QGraphicsItemGroup):
    def __init__(self, id, dt, label = '', color = ''):
        super().__init__()
    
        self.id = id
        self.dt = dt
        self.label = label
        self.color = color


class LayoutScene(QGraphicsScene):
    def __init__(self):
        super().__init__()

        self.layers = dict()

    def addLayer(self, id: int, layer: LayerInfo):
        if self.layers.get(id):
            l = self.layers.get(id)
            l.id = layer.id
            l.dt = layer.dt
            l.label = layer.label
            l.color = layer.color
        else:
            self.layers[id] = Layer(layer.id, layer.dt, layer.label, layer.color)

    def removeLayer(self, id):
        if self.layers.get(id):
            self.layers.pop(id)

    def setLayerVisibility(self, id: int, visible: bool):
        if visible:
            self.layers[id].show()
        else:
            self.layers[id].hide()


class ViewerBase:
    def __init__(self):
        self.app = QApplication()
        self.layout = LayoutScene()

    def show(self):
        self.app.exec_()


class LayersPaletteLayer(QListWidgetItem):

    w, h = 40, 20
    bh = True

    def __init__(self, id: int, text: str, pen: QPen, brush: QBrush):
        super().__init__(text)

        LayersPaletteLayer.bh = not LayersPaletteLayer.bh
        brush.setStyle(Qt.BDiagPattern)
        if self.bh:
            brush.setStyle(Qt.FDiagPattern)

        self.id = id
        self.pen = pen
        self.brush = brush
        self.visible = True

        self.setFont(QFont('Arial', 14, 100))
        self.setLayerPixmap()

    def toggleVisibilityFlag(self):
        self.visible = not self.visible
        self.setLayerPixmap()

    def setLayerPixmap(self):
        m = QPixmap(self.w+1, self.h+1)
        m.fill(Qt.transparent)

        p = QPainter(m)
        p.setPen(self.pen)
        if self.visible:
            p.fillRect(m.rect(), self.brush)
        p.drawRect(0, 0, self.w, self.h)
        p.end()

        self.setIcon(QIcon(m))


class LayersPalette(QDockWidget):
    def __init__(self, base: ViewerBase, parent: QWidget):
        super().__init__('Layers', parent)

        self.base = base
        self.list = QListWidget(self)
        self.list.setIconSize(QSize(40,20))
        self.list.setSelectionMode(self.list.ExtendedSelection)
        self.list.itemDoubleClicked.connect(self.handleDoubleClick)
        self.setWidget(self.list)

    def addLayer(self, id: int):
        layer = self.base.layout.layers[id]

        color = QColor(layer.color)
        if len(layer.label):
            text = "{} ({}/{})".format(layer.label, str(layer.id), str(layer.dt))
        else:
            text = "{}/{}".format(str(layer.id), str(layer.dt))
        
        self.list.addItem(LayersPaletteLayer(layer.id, text, QPen(color), QBrush(color)))

    def removeLayer(self, id: int):
        for i in self.list.items:
            if i.id == id:
                self.list.removeItemWidget(i)
                break

    def clear(self):
        self.list.clear()

    def handleDoubleClick(self, item: LayersPaletteLayer):
        item.toggleVisibilityFlag()
        self.base.layout.setLayerVisibility(item.id, item.visible)


class ScaleOverlay(QWidget):

    labels = ['fm', 'pm', 'nm', 'um', 'mm', 'm']

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.label = '#'
        self.units = 1
        self.scale = 1

    def setUnits(self, units, base = 2):
        self.units = units

        u = base
        while units >= 1000:
            units /= 1000
            u += 1
        
        if u > len(self.labels) - 1:
            self.label = '#err'

        self.label = ''.join([str(math.floor(units)), '\t', self.labels[u]])

    def setScale(self, scale):
        self.scale = scale
        
    def paintEvent(self, event: QPaintEvent):
        super().paintEvent(event)
        p = QPainter(self)
        p.setFont(QFont('', 14, 0))
        p.setPen(QPen(QBrush(Qt.gray), 0))

        w = self.scale * self.units

        p.setBrush(QBrush(Qt.gray))
        p.drawRect(50 + 0, self.rect().bottom() - 50, w, 8)
        p.setBrush(QBrush(Qt.transparent))
        p.drawRect(50 + w, self.rect().bottom() - 50, w, 8)
        p.drawText(50, self.rect().bottom() - 65, 2*w, 20, 
            Qt.AlignRight, self.label)


class LayoutViewWidget(QGraphicsView):

    gridLinesPerRow = 20
    gridLinesScaleInc = 5

    def __init__(self, base: ViewerBase, parent: QWidget):
        super().__init__(base.layout, parent)

        self.grabGesture(Qt.PinchGesture)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, False)
        self.setBackgroundBrush(QBrush(Qt.white))

        self.scaleOverlay = ScaleOverlay(self)
        self.scaleOverlay.setUnits(100)

        self.zoomOrigin = QPointF(0,0)
        self.units = 100
        
    def resizeEvent(self, event: QResizeEvent):
        self.scaleOverlay.setGeometry(self.geometry())

    def recalcUnits_(self):
        rect = self.mapToScene(self.viewport().geometry()).boundingRect()
        self.units = 1
        while (rect.width() / self.units / self.gridLinesPerRow) > 1:
            self.units *= self.gridLinesScaleInc
        self.scaleOverlay.setUnits(self.units)

    def scaleBrushes(self, invScale: float):
        

    def zoom(self, factor: float):
        newScale = abs(factor * self.transform().m11())
        if 0.00001 < newScale < 10:
            self.scale(factor, factor)
            self.scaleBrushes(1/factor)
            self.recalcUnits_()
            self.scaleOverlay.setScale(abs(self.transform().m11()))

    def pan(self, dist: float, horiz: bool = True):
        pass

    def event(self, event: QEvent):
        if isinstance(event, QGestureEvent):
            return self.handleGestureEvent(event)
        return super().event(event)

    def handleGestureEvent(self, event: QGestureEvent):
        if event.gesture(Qt.PinchGesture):
            event.accept()

            pinch = event.gesture(Qt.PinchGesture)

            # apply transformations
            if pinch.RotationAngleChanged:
                self.rotate(pinch.rotationAngle()/10)
            
            if pinch.ScaleFactorChanged:
                self.zoomOrigin = event.mapToGraphicsScene(pinch.centerPoint())
                self.zoom(pinch.scaleFactor())

            return True
        
        return False

    def drawBackground(self, painter: QPainter, rect: QRect):
        super().drawBackground(painter, rect)

        # draw the grid lines
        gridPen = QPen(QBrush(Qt.darkGray), 0)
        gridPen.setDashPattern([1,10])

        # compute grid line positions
        x0 = self.zoomOrigin.x()
        nx = math.ceil(rect.width() / self.units / 2)
        xpos = [x0 + x*self.units for x in range(-nx,nx)]

        y0 = self.zoomOrigin.y()
        ny = math.ceil(rect.height() / self.units / 2)
        ypos = [y0 + y*self.units for y in range(-ny,ny)]

        # draw grid on white background
        painter.setPen(gridPen)
        for i, x in enumerate(xpos):
            painter.drawLine(x, rect.bottom(), x, rect.top())
        for i, y in enumerate(ypos):
            painter.drawLine(rect.left(), y, rect.right(), y)


class SimpleViewerWindow(QWidget):
    def __init__(self, base: ViewerBase):
        super().__init__()

        self.setMinimumSize(800, 600)

        self.viewWidget = LayoutViewWidget(base, self)
        self.layersWidget = LayersPalette(base, self)

        splitter = QSplitter()
        splitter.addWidget(self.viewWidget)
        splitter.addWidget(self.layersWidget)
        splitter.setSizes([200, 1])

        horizLayout = QHBoxLayout()
        horizLayout.addWidget(splitter)
        horizLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(horizLayout)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.close()


class SimpleViewer(ViewerBase):
    def __init__(self):
        super().__init__()
        self.window = SimpleViewerWindow(self)

    def show(self):
        self.window.show()
        super().show()

    def makeOrGetLayer(self, id):
        if not self.layout.layers.get(id):
            self.addLayer(Layer(id, 0, '', '#' + ''.join('{:02X}'.format(a) for a in QColor(
                random.randint(100, 200),
                random.randint(100, 200),
                random.randint(100, 200)
            ).getRgb())))

        return self.layout.layers[id]

    def addLayer(self, layer):
        self.layout.addLayer(layer.id, layer)
        self.window.layersWidget.addLayer(layer.id)

    def setLayers(self, layers: list):
        for l in layers:
            self.addLayer(l)

    def setGds(self, gds: gdspy.GdsLibrary):
        scale = 1/gds.unit
        cells = gds.top_level()
        for cell in cells:
            d = cell.get_polygons(True)
            for key in d:
                layer = key[0]
                dtype = key[1]

                l = self.makeOrGetLayer(layer)

                for poly in d[key]:
                    pts = []
                    for xy in poly:
                        pts.append(QPointF(xy[0]*scale, xy[1]*scale))

                    item = QGraphicsPolygonItem(QPolygonF(pts))
                    item.setPen(QPen(QBrush(QColor(l.color)),0))
                    item.setBrush(QBrush(QColor(l.color), Qt.BDiagPattern))
                    self.layout.layers[layer].addToGroup(item)

        for key in self.layout.layers:
            self.layout.addItem(self.layout.layers[key])


gds = gdspy.GdsLibrary().read_gds('ebeam_gc_te1550.gds')

viewer = SimpleViewer()
viewer.addLayer(LayerInfo(10, 0, 'Layer10', '#ff55ff'))
viewer.addLayer(LayerInfo(5, 0, 'Unknown', '#bbbb55'))
viewer.addLayer(LayerInfo(22, 0, 'Etch', '#0055bb'))
viewer.addLayer(LayerInfo(100, 0))
viewer.setGds(gds)
viewer.show()