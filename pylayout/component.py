from .mixin import ParameterType, TransformableMixin, ParameterizableMixin
from .shape import Shape, Text, Path
from .routing import Pin
from . import math

import inspect

__all__ = (
    'PinRef',
    'Component',
    'ComponentRef',
    'Parameter',
    'Builder'
)

class Component: pass   # stub for ref

#####################################################################################################################
#
# Reference objects
#
#####################################################################################################################

class PinRef(TransformableMixin):
    __slots__ = ('name', 'pin')

    def __init__(self, name, pin: Pin, position=(0,0), rotation=0, scale=1.0, flipH=False):
        
        self.name = name
        self.pin = pin
        self.local.transform(position, rotation, scale)
        if flipH:
            self.local.flipH()
    
    @property
    def position(self):
        return self.local * self.pin.position

    @property
    def direction(self):
        return math.degrees(self.local.rotation) + self.pin.direction

    @property
    def width(self):
        return self.pin.width

    def __str__(self):
        return "Pin %s, at %s, width: %s, direction: %s" % (self.name, self.position, self.width, self.direction)


class ComponentRef(TransformableMixin):
    """
    Reprensents an instanced component active in a parent component layout
    """
    __slots__ = ('name', 'component', 'pins')
    def __init__(self, name, component: Component, position=(0,0), rotation=0, scale=1.0, flipH=False):

        self.name = name
        self.component = component
        
        self.local.transform(position, rotation, scale)
        if flipH:
            self.local.flipH()

        # create pin references
        self.pins = dict()
        for name, pin in component.get_pins().items():
            if isinstance(pin, PinRef):
                self.pins[name] = PinRef(pin.pin, self.local * pin.local)
            else:
                self.pins[name] = PinRef(pin, self.local)
    
    def __getitem__(self, key):
        self.get_pin(key)
    
    def get_pin(self, key):
        if math.isnumber(key):
            if not key in self.pins.items():
                raise KeyError(f"Invalid pin name '{key}' for component {self.name}!")
            return self.pins.values()[key]
        
        if not key in self.pins:
            raise KeyError(f"Invalid pin name '{key}' for component {self.name}!")
        
        return self.pins[key]
    
    def get_bounds(self):
        return self.component.get_bounds()

    def get_area(self):
        return self.component.get_bounds().area()

    @property
    def origin(self):
        return self.local.translation + self.component.origin()


#####################################################################################################################
#
# Component
#
#####################################################################################################################

class Component:
    """
        Base class for all component stuff
    """
    __slots__ = ('__pins', '__shapes', '__components')
    def __init__(self):
        self.__pins = dict()
        self.__shapes = []
        self.__components = []

    def place(self, name, item, position=(0,0), rotation=0.0, scale=1.0, flipH=False, params={}):

        if inspect.isclass(item):
            if not issubclass(item, Builder):
                raise ValueError("wrong type provided to place(), item must be a Component instance or a Builder")

            if params is None:
                item = item()
            else:
                item = item(**params)
        
        if not isinstance(item, Component):
            raise ValueError('invalid argument supplied to place(), item must be a Component instance or a Builder')

        self.__components.append(ComponentRef(name, item, position, rotation, scale, flipH))

    def insert(self, layer, element, translation=(0,0), rotation=0.0, scale=1.0, flipH=False):

        if isinstance(element, list):
            element = Shape(element)

        if isinstance(element, (Shape, Path, Text)):
            # always grab a copy to avoid referencing
            element = element.copy()
            element.transform(
                translation, 
                rotation, 
                scale)
            
            if flipH:
                element.flipH()

        self.__shapes.append( (layer, element) )

    def addpin(self, name, position, direction='e', width=1.0):
        if name in super().__pins:
            raise KeyError(f"a pin with the name '{name}' already exists on this component")

        self.__pins[name] = Pin(name, position, direction, width)

    def get_pins(self):
        return self.__pins
    
    def get_shapes(self):
        return self.__shapes

    def get_children(self):
        return self.__components

    def get_bounds(self):
        bb = math.BoundingBox()

        for _, element in self.__shapes:
            for xy in element.xy:
                bb.include(xy)
        
        for cmp in self.__components:
            bb.include(cmp.get_bounds())
        
        return bb


#####################################################################################################################
#
# Builder
#
#####################################################################################################################

class Parameter(ParameterType):
    __slots__ = ('name', 'default', 'type', 'required', 'fvalidate')
    def __init__(self, default, type=None, required=False, fvalidate=None, doc=""):
        super().__init__(fget=self.get, fset=self.set, doc=doc)

        self.name = None    # will be assigned at runtime

        self.type = type
        self.default = default
        self.required = required
        self.fvalidate = fvalidate

    def __str__(self) -> str:
        return f"Parameter({self.name}): {self.doc}"

    def get(self, obj):
        return obj.__llvalues__[self.name]
    
    def set(self, obj, value):

        def get_lambdaexpr(arg):
            import re, inspect
            s = inspect.getsource(arg)
            i = s.find('lambda')
            j = re.search(':[^,)]*', s[i:]).span()
            return s[i+j[0]+1:i+j[1]].strip()
        
        if not self.type is None:
            if not type(value) is self.type:
                raise ValueError(f"invalid type for parameter '{self.name}', type must be '{self.type.__name__}'")
        
        if callable(self.fvalidate):
            if not self.fvalidate(value):
                extra = ", check validation function"
                if self.fvalidate.__name__ == '<lambda>':
                    extra = f", must satisfy expression '{get_lambdaexpr(self.fvalidate)}'"
                raise ValueError(f"invalid value supplied for '{self.name}'{extra}")
        
        obj.__llvalues__[self.name] = value


class Builder(ParameterizableMixin):
    """
        Creates a Parameterizable Component object by calling its Build() method
    """
    def __new__(cls, *args, **kwargs) -> Component:
        obj = super().__new__(cls, Parameter, *args, **kwargs)

        # build runtime component instance
        obj.__component = Component()
        obj.build()

        return obj.__component
    
    def build(self): ...

    def place(self, name, item, position=(0,0), rotation=0.0, scale=1.0, flipH=False, params={}):
        self.before_place()
        self.__component.place(name, item, position, rotation, scale, flipH, params)
        self.after_place()

    def insert(self, layer, element, translation=(0,0), rotation=0.0, scale=1.0, flipH=False):
        self.before_insert()
        self.__component.insert(layer, element, translation, rotation, scale, flipH)
        self.after_insert()
    
    def define_pin(self, name, position, direction='e', width=1.0):
        self.before_addpin()
        self.__component.addpin(name, position, direction, width)
        self.after_addpin()

    # life-cycle hooks
    def before_place(self): pass
    def after_place(self):  pass
    def before_insert(self): pass
    def after_insert(self):  pass
    def before_addpin(self): pass
    def after_addpin(self):  pass
