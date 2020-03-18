from model import *
from view import *

import os

app = QApplication()
layout = Layout()
v = Viewer(layout)
v.showMaximized()

layout.set(loadGdsFromFile(os.path.realpath('nand2.gds2')))

app.exec_()



class ViewSession(object):
    def __init__(self):
        self.procid = None

    def start(self):
        # create process to run the viwer in and grab the proc id
        pass

    def stop(self):
        # kill the active process (if any)
        pass

    def view(self, layout: Layout):
        # update the layout on the viewer process (if exists)

        # NOTE: might need to raise an event or signal something for the viewer to ask for the new datat
        pass