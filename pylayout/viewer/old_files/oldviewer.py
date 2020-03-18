#!/usr/local/bin/python3

from PySide2.Qt import *
from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtWidgets import *

from layout import LayerInfo
from util import GdsFileResource

import sys
import math
import random
import gdspy
import gdsii
import argparse

class LayersPaletteWidgetIcon(QIcon):
    """ custom layer graphics matching visual appearance in layout """
    
    def __init__(self, borderColor: QColor, fillColor: QColor, visibleFlag = True):
        super(LayersPaletteWidgetIcon, self).__init__()

        self.pen = QPen(QBrush(borderColor), 0)
        self.brush = QBrush(fillColor, Qt.BrushStyle().Dense1Pattern)
        self.draw(visibleFlag)
        
    def draw(self, visibleFlag: bool):
        sz = QSize(25,25)
        img = QPixmap(sz)

        painter = QPainter(img)
        painter.setPen(self.pen)
        painter.setBrush(self.brush)

        painter.drawRect(img.rect())
        if not visibleFlag:
            painter.drawLine(0, 0, sz.width(), sz.height())
        
        painter.end()

        self.addPixmap(img)


class LayersPaletteWidgetItem(QListWidgetItem):
    """
      custom layer list item with icon, name and layer_id/data_type info,
      double clicking an item turns hiding on/off of all display items 
      belonging to that layer in the scene view
    """

    def __init__(self, layer_id, layer_str, layer_color, layer_fill):
        super(LayersPaletteWidgetItem, self).__init__(
            LayersPaletteWidgetIcon(QColor(layer_color), QColor(layer_fill)), layer_str)

        self.layer_id = layer_id
        self.layer_color = layer_color
        self.layer_fill = layer_fill

        # indicates wether or not the graphics items are visible in scene
        self.visible = True 

    def toggleVisibilityState(self):
        self.visible = not self.visible
        if self.visible:
            self.setTextColor(Qt.red)
        else:
            self.setTextColor(Qt.white)

class LayersPaletteWidget(QListWidget):
    """ side widget to display active layers by name and color """
    
    def __init__(self, parent: QWidget):
        super(LayersPaletteWidget, self).__init__(parent)

        self.viewMode = self.ListMode
        self.itemDoubleClicked.connect(self.handleDoubleClick)
        self.setUniformItemSizes(True)
        self.setFont(QFont("Arial", 22, 100))

    def addLayer(self, layer: LayerInfo):
        layerItem = LayersPaletteWidgetItem(layer.layer_id,
            "".join([str(layer.layer_id),'/',str(layer.data_type),' ',layer.name])
            , layer.color, layer.fill)
        self.addItem(layerItem)

    def insertLayer(self, row: int, layer: LayerInfo):
        layerItem = LayersPaletteWidgetItem(layer.layer_id,
            "".join([str(layer.layer_id),'/',str(layer.data_type),' ',layer.name])
            , layer.color, layer.fill)
        self.insertItem(row, layerItem)

    def setLayers(self, layers: list):
        self.clear()
        for layer in layers:
            self.addLayer(layer)
    
    def handleDoubleClick(self, item: LayersPaletteWidgetItem):
        item.toggleVisibilityState()
        if item.visible:
            self.graphicsLayers[item.layer_id].show()
        else:
            self.graphicsLayers[item.layer_id].hide()


class ScaleWidget(QWidget):
    """ displays a scale metric overlay on the layout view """

    units = ['fm', 'pm', 'nm', 'µm', 'mm', 'm']

    def __init__(self, parent: QWidget):
        super(ScaleWidget, self).__init__(parent)
        self.unit = 1
        self.scale = 1

    def setScale(self, scale: float):
        self.scale = scale

    def setUnits(self, unit: float):
        self.unit = unit

    def unitStr(self, unit: int, base = 2) -> str:
        u = base
        while unit >= 1000:
            unit /= 1000
            u += 1
        
        if u > len(self.units) - 1:
            return '#err'
        
        return str(math.floor(unit)).join([' ', self.units[u]])

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setPen(QPen(Qt.lightGray))

        scale = self.scale * self.unit

        painter.setBrush(QBrush(Qt.lightGray, Qt.BrushStyle.SolidPattern))
        painter.setFont(QFont("Times", 22))
        painter.drawText(2*scale + 10, 0, 100, 20, 
            Qt.AlignLeft, self.unitStr(self.unit))
        painter.drawRect(0, 0, scale, 20)
        painter.setBrush(QBrush(Qt.transparent))
        painter.drawRect(scale, 0, scale, 20)
        

class RulerWidget(QWidget):
    """ Displays a thin scalable ruler on the edge of the view """

    def __init__(self, parent: QWidget):
        super(RulerWidget, self).__init__(parent)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setBrush(QBrush(Qt.lightBlue))
        painter.fillRect(self.rect())


class LayoutViewWidget(QGraphicsView):
    """
      main widget to display layout scene view, the widget responds to 
      gestures for zooming in/out as well as rotating
    """

    gridLinesPerRow = 50
    
    def __init__(self, parent: QWidget):
        super(LayoutViewWidget, self).__init__(parent)

        self.grabGesture(Qt.PinchGesture)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        # create scale reference widget overlay
        self.scaleOverlay = ScaleWidget(self)
        self.scaleOverlay.show()

        # horzLayout = QHBoxLayout()
        # horzLayout.insertWidget(1)
        # container = QWidget()
        # container.setLayout(horzLayout)

        vertLayout = QVBoxLayout()
        # vertLayout.addChildLayout()
        vertLayout.insertWidget(1, self.scaleOverlay, 1)
        self.setLayout(vertLayout)

        self.zoomOrigin = QPointF(0,0)

    def zoom(self, scaleFactor: float):
        # limit zooming range
        newScale = abs(scaleFactor * self.transform().m11())
        if (newScale > 0.00001) and (newScale < 10):
            self.scale(scaleFactor, scaleFactor)
            self.scaleOverlay.setScale(abs(self.transform().m11()))

    def event(self, event: QEvent):
        if isinstance(event, QGestureEvent):
            return self.handleGestureEvent(event)
        return super().event(event)

    def handleGestureEvent(self, event: QGestureEvent):
        if event.gesture(Qt.PinchGesture):
            event.accept()

            pinch = event.gesture(Qt.PinchGesture)

            # TODO: fix rotations!
            # apply transformations
            # if abs(pinch.rotationAngle()) > 0:
            #     self.rotate(pinch.rotationAngle()/10)
            # else:

            # track zoom origin for grid behavior
            self.zoomOrigin = event.mapToGraphicsScene(pinch.centerPoint())
            self.zoom(pinch.scaleFactor())

            return True
        
        return False

    def drawBackground(self, painter: QPainter, rect: QRect):

        # draw the grid lines
        gridPen = QPen(QBrush(Qt.lightGray), 0)

        # adaptive rescaling every factor of 10 in view dimensions
        units = 1
        while (rect.width() / units / self.gridLinesPerRow) > 1:
            units *= 10

        # update the units on the overlay
        self.scaleOverlay.setUnits(units)

        # compute grid line positions
        x0 = self.zoomOrigin.x()
        nx = math.ceil(rect.width() / units / 2)
        xpos = [x0 + x*units for x in range(-nx,nx)]

        y0 = self.zoomOrigin.y()
        ny = math.ceil(rect.height() / units / 2)
        ypos = [y0 + y*units for y in range(-ny,ny)]

        # draw grid on white background
        painter.fillRect(rect, Qt.white)
        painter.setPen(gridPen)

        for i, x in enumerate(xpos):
            # if i % 10:
            #     painter.setPen(lightPen)
            # else:
            #     painter.setPen(darkPen)
            
            painter.drawLine(x, rect.bottom(), x, rect.top())

        for i, y in enumerate(ypos):
            # if i % 10:
            #     painter.setPen(lightPen)
            # else:
            #     painter.setPen(darkPen)
            
            painter.drawLine(rect.left(), y, rect.right(), y)

#------------------------------------------------------------------------------------
#
# Viewer
#
#------------------------------------------------------------------------------------

class Viewer(QMainWindow):
    """
      main window housing all widgets and providing an API to interact
      with the scene view as well as loading/unloading of layout GDS data
    """

    def __init__(self):
        super(Viewer, self).__init__()

        self.setWindowTitle('pylayout Viewer')

        # create graphics scene
        self.graphicsScene = QGraphicsScene()

        # create layout view widget
        self.layoutViewWidget = LayoutViewWidget(self)
        self.layoutViewWidget.setScene(self.graphicsScene)

        # create layers palette widget
        self.layersPaletteWidget = LayersPaletteWidget(self)

        # create center widget layout
        boxLayout = QHBoxLayout()
        boxLayout.addWidget(self.layoutViewWidget, 3)
        boxLayout.addWidget(self.layersPaletteWidget, 1)
        boxLayout.setSpacing(0)
        boxLayout.setContentsMargins(0,0,0,0)
        centralWidget = QWidget()
        centralWidget.setLayout(boxLayout)
        self.setCentralWidget(centralWidget)

        # show status bar
        self.statusBar().show()

        # maximize before setting menus (size fix)
        self.maximize()

        # show menu bar
        # fileOpen = QAction('&File', self)
        # fileOpen.setShortcut(QKeySequence().Open)
        # fileOpen.setStatusTip("Open a GDS file")
        # self.menuBar().addAction(fileOpen)
        # self.menuBar().setNativeMenuBar(False)
        # self.menuBar().show()

    def maximize(self):
        rect = self.screen().availableGeometry()
        self.setMinimumSize(rect.width(), rect.height())
        self.move((rect.width() - self.width())/2,
            (rect.height() - self.height())/2)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.close()

        # respond to certain hot keys
        if event.key() == Qt.Key_F:
            self.fitInView()

        speed = self.layoutViewWidget.sceneRect().width()

        if event.key() == Qt.Key_Up:
            self.layoutViewWidget.translate(-speed,0)

        if event.key() == Qt.Key_Down:
            self.layoutViewWidget.translate(+speed,0)
            
        if event.key() == Qt.Key_Left:
            self.layoutViewWidget.translate(-speed,0)

        if event.key() == Qt.Key_Right:
            self.layoutViewWidget.translate(+speed,0)

    def load(self, file):
        self.set(load_gds(file))

    def clear(self):
        self.graphicsScene.clear()

    def setUnit(self, unit: float):
        pass

    def setPrecision(self, precision: float):
        pass

    def set(self, lib: gdspy.GdsLibrary):
        self.graphicsScene.clear()

        self.setUnit(lib.unit)
        self.setPrecision(lib.precision)

        # walk tree and create graphics items

        self.fitInView()

    def setOrigin(self, x: int, y: int):
        pass

    def setViewRect(self, left: int, bottom: int, width: int, height: int):
        pass

    def fitInView(self):
        self.layoutViewWidget.resetTransform()
        self.layoutViewWidget.fitInView(
            self.graphicsScene.itemsBoundingRect(), 
            Qt.KeepAspectRatio)

#------------------------------------------------------------------------------------
#
# SimpleViewer displays flat gds layout without cell information
#
#------------------------------------------------------------------------------------

class SimpleViewer:
    """ simplified viewer does not represent high order objects """

    def __init__(self):
        self.app = QApplication()
        self.layout = QGraphicsScene()
        self.view = LayoutViewWidget(self)
        self.view.setScene(self.layout)

    def attach(self, gds):
        if isinstance(gds, GdsFileResource):
            self.setLibrary(gds)
        else:
            Warning("invalid argument supplied to attach()")
    
    def setLibrary(self, lib: gdsii.library.Library):
        self.scene.clear()

        for struct in lib:
            for elem in struct:

                if isinstance(elem, gdsii.elements.Boundary):
                    layers

    def show(self):
        self.layoutView.show()
        self.app.exec_()






if __name__ == '__main__':
    # prs = argparse.ArgumentParser(description='GDS layout viewer')
    # prs.add_argument('file', type=str, required=True)
    # args = prs.parse_args()

    # viewlayout(load_gds(args.file))

    layers = []
    for i in range(1,10):
        c = '#%02X%02X%02X' % (random.randint(0,255),random.randint(100,255),random.randint(100,255))
        layers.append(LayerInfo(i, 0, "dummy", c, c))
    
    app = QApplication()
    view = Viewer()
    view.layersPaletteWidget.setLayers(layers)
    view.show()
    sys.exit(app.exec_())
