__all__ = (
    'Layer',
    'Process',
    'GENERIC'
)

class Layer:
    """ process layer for the specification of lithographic mask """
    __slots__ = ('name', 'layer', 'datatype', 'docstring', 'exported')
    def __init__(self, name, layer, datatype, docstring='', exported=True):
        self.name = name
        self.layer = layer
        self.datatype = datatype
        self.docstring = docstring
        self.exported = exported
    
    def __str__(self):
        return f"{self.name} \t- ({self.layer}/{self.datatype}) {self.docstring} (export={self.exported})"


class Process:
    """ process object contains target fab process information """
    def __init__(self, name):
        self.name = name
        self.layers = dict()

    def __str__(self):
        return f"{self.name}\n" + "\n".join(map(str, self.layers.values()))

    def __getitem__(self, key):
        if not key in self.layers:
            raise ValueError('Invalid layer name specified.')
        return self.layers[key]

    def define(self, name, layer, datatype, doc='', exported=True):
        self.layers[name] = Layer(name, layer, datatype, doc, exported)


# Default process provided with the library
GENERIC = Process('Generic Technology')
GENERIC.define('Si',    1,  0, 'Silicon device layer')
GENERIC.define('Etch',  1,  1, 'Negative resist etch mask')
GENERIC.define('N++',   10, 0, 'N-doped semiconducter')
GENERIC.define('Metal', 20, 0, 'Metalization device layer')
GENERIC.define('Floor', 100,0, 'Floor plan')