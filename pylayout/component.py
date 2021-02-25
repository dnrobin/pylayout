from . import math
from . import mixin
from . import shape
from .routing import Pin

import inspect

class Component: pass   # stub for ref


class PinRef(mixin.Transformable):
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


class ComponentRef(mixin.Transformable):
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
        for name, pin in component.pins.items():
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


class Component:
    """ Component """
    
    __slots__ = ('__pins', '__shapes', '__components')
    def __init__(self):
        self.__pins = dict()
        self.__shapes = []
        self.__components = []

    def place(self, name, item, position=(0,0), rotation=0.0, scale=1.0, flipH=False, params={}):

        if inspect.isclass(item):
            if params is None:
                comp = item()
            else:
                comp = item(**params)
            
            if not isinstance(comp, Component):
                raise ValueError('Invalid argument supplied to place(), item must be a component instance or a builder!')

        self.__components.append(ComponentRef(name, comp, position, rotation, scale, flipH))

    def get_shapes(self):
        return self.__shapes

    def get_children(self):
        return self.__components

    def get_bounds(self):
        bb = math.BoundingBox()
        for _, element in self.__shapes:
            bb.include(element.xy)
        return bb


class Builder(Component):

    def insert(self, layer, element, translation=(0,0), rotation=0.0, scale=1.0):

        self.before_insert()

        if isinstance(element, list):
            element = shape.Shape(element)

        if isinstance(element, (shape.Shape, shape.Path, shape.Text)):
            # always grab a copy to avoid referencing
            element = element.copy()
            element.transform(
                translation, 
                rotation, 
                scale)

        super().__shapes.append( (layer, element) )

        self.after_insert()

    def define_pin(self, name, position, direction='e', width=1.0):
        if name in super().__pins:
            raise KeyError(f"A pin with the name '{name}' already exists on this component!")

        self.before_define_pin()

        super().__pins[name] = Pin(name, position, direction, width)

        self.after_define_pin()