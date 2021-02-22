
class Component:
    """ Component """
    __slots__ = ('__shapes', '__components')
    def __init__(self):
        self.__shapes = []
        self.__components = []

    def insert(self, layer, item):
        self.__shapes.append( (layer, item) )

    def place(self, comp, origin=(0,0)):
        self.__components.append(ComponentReference(comp, origin))

    def get_shapes(self):
        pass

    def get_children(self):
        pass

