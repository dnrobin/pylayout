#!/usr/local/bin/python3

from PySide2.Qt import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

import sys
import gdspy
import argparse


class LayerListWidgetVisual(QIcon):
    """ custom layer graphics matching visual appearance in layout """
    pass


class LayerListWidgetItem(QListWidgetItem):
    """
      custom layer list item with icon, name and layer_id/data_type info,
      double clicking an item turns hiding on/off of all display items 
      belonging to that layer in the scene view
    """
    pass


class LayerListWidget(QListWidget):
    """ side widget to display active layers by name and color """
    pass


class LayoutViewWidget(QGraphicsView):
    """
      main widget to display layout scene view, the widget responds to 
      gestures for zooming in/out as well as rotating
    """
    pass


class Viewer(QMainWindow):
    """
      main window housing all widgets and providing an API to interact
      with the scene view as well as loading/unloading of layout GDS data
    """

    def __init__(self):
        super(Viewer, self).__init__()

    def load(self, file):
        pass

    def clear(self):
        pass

    def set(self, lib: gdspy.GdsLibrary):
        pass

    def setOrigin(self, x: int, y: int):
        pass

    def setViewRect(self, left: int, bottom: int, width: int, height: int):
        pass


def load_gds(file):
    return gdspy.GdsLibrary().read_gds(file)


def viewlayout(lib: gdspy.GdsLibrary):
    pass


def viewsection(lib: gdspy.GdsLibrary):
    pass


def view3d(lib: gdspy.GdsLibrary):
    pass


if __name__ == '__main__':
    prs = argparse.ArgumentParser(description='GDS layout viewer')
    prs.add_argument('file', type=str, required=True)
    args = prs.parse_args()

    viewlayout(load_gds(args.file))
