
class Rule:
    def __init__(self, name, value, doc, layer=None):
        self.name = name
        self.doc = doc
        self.value = value
        self.layer = layer

    def __repr__(self):
        return "%s: %s %s %s" % (
            self.name, 
            self.value, 
            '(layer: %s)' % self.layer.name if not self.layer is None else '', 
            self.doc if not self.doc is None else '')


class DesignRules:
    def __init__(self, unit=1e-6, precision=1e-9, **kwargs):
        self.unit = unit
        self.precision = precision
        self.rules = dict()

        # default rules
        self.add_rule('GRID', True, 'Require vertices to be snapped to grid coordinates')
        self.add_rule('MIN_WIDTH', .1, 'Minimum element width')
        self.add_rule('MIN_SPACE', .2, 'Minimum spacing around element')
        self.add_rule('MIN_SPACE_DT', 1, 'Minimum sopacing to nearest deep trench')
        self.add_rule('MIN_DENSITY', .2, 'Minimum material density ratio')
        self.add_rule('MAX_DENSITY', .7, 'Maximum material density ratio')
        
        for k, v in kwargs.items():
            self.rules[k].value = Rule(k, v)
    
    def __getitem__(self, key):
        if not key in self.rules:
            raise KeyError("Key '%s' not found in rules!" % key)
        return self.rules[key]

    def __setitem__(self, key, value):
        if not key in self.rules:
            raise KeyError("Key '%s' not found in rules!" % key)
        self.rules[key].value = value

    def __delitem__(self, key):
        if not key in self.rules:
            raise KeyError("Key '%s' not found in rules!" % key)
        del self.rules[key]

    def __iter__(self):
        return iter(self.rules)

    def __len__(self):
        return len(self.rules)

    def __repr__(self):
        return "\n".join(map(repr, self.rules.values()))
    
    def add_rule(self, name: str, value: float, doc=None, layer=None):
        self.rules[name] = Rule(name, value, doc, layer)

    def remove_rule(self, name):
        if not name in self.rules:
            raise KeyError("Rule '%s' not found in rules!" % name)
        del self.rules[name]
        
    def clear(self):
        self.rules.clear()


class ProcessLayer:
    """ ProcessLayer - defines GDSII layer/dtype to match fab process layer specification
    """
    def __init__(self, name, layer, dtype, doc=None, export=True, facecolor=None, edgecolor=None, dither=None):
        self.name = name
        self.doc = doc
        self.layer = layer
        self.dtype = dtype
        self.export = export
        self.facecolor = facecolor
        self.edgecolor = edgecolor
        self.dither = dither

    def __repr__(self):
        return "%s:\t(%s/%s) %s (exported: %s)" % (self.name, self.layer, self.dtype, self.doc, self.export)


class ProcessLayers:
    """ defines GDSII fabrication process layers

    Each foundry has its own predefined set of process layers with instructions,
    this is the container to group these layers and query them by human readable name
    """
    def __init__(self, name='Unknown Process'):
        self.name = name
        self.layers = dict()

    def __getitem__(self, key):
        if not key in self.layers:
            raise KeyError("Layer name '%s' not in layers!" % key)
        return self.layers[key]

    def __iter__(self):
        return iter(self.layers)

    def __len__(self):
        return len(self.layers)

    def __repr__(self):
        return "\n".join(map(repr, self.layers.values()))

    def add_layer(self, name, layer, dtype, doc=None, export=True, facecolor=None, edgecolor=None, dither=None):
        self.layers[name] = ProcessLayer(name, layer, dtype, doc, export, facecolor, edgecolor, dither)
    
    def remove_layer(self, name):
        if name in self.layers:
            del self.layers[name]

    def clear(self):
        self.layers.clear()
    
    def get_layer(self, name):
        if name in self.layers:
            return self.layers[name]
        return None

    def get_layer_by_spec(self, layer, dtype):
        for l in self.layers.values():
            if l.layer == layer and l.dtype == dtype:
                return l
        return None

    def get_exported_layers(self):
        layers = {}
        for i, l in self.layers.items():
            if l.export:
                layers[i] = l
        return layers