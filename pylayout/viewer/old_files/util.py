from gdsii.library import Library
from gdspy import GdsLibrary

class GdsFileResource:

    def __init__(self, filein: str):
        self.file = filein

    def getlib(self):
        with open(self.file) as stream:
            return Library.load(stream)