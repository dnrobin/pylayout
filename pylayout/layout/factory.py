import inspect

__all__ = ["ComponentParameter", "ComponentFactory"]

def __extract_lambda_expression(lam):
    """ extract expression string from lambda function """
    import re, inspect
    s = inspect.getsource(lam)
    i = s.find('lambda')
    j = re.search(':[^,)]*', s[i:]).span()
    return s[i+j[0]+1:i+j[1]].strip()


"""
    Base class for component factory construction parameters
"""
class BaseParameter(property):
    """ Component factory parameter
    
    input:
    -----
        description - general description used for documentation
        type        - restrict value type associated with property
        default     - default value when property not set
        readonly    - set as readonly property
        required    - set as required property
        validated   - set validation lambda expression to be run on value
    """
    
    __slots__ = ('name', 'value', 'default', 'type', 'description', 'required', 'readonly', 'validation')

    def __init__(self, default=None, type=None, description='', required=False, readonly=True, validation=None):
        super(Parameter, self).__init__(self._get, self._set, doc=description)
        
        self.name           = None
        self.type           = type
        self.default        = default
        self.description    = description
        self.readonly       = readonly
        self.validation     = validation
        self.required       = required

    def copy(self):
        return Parameter(self.default, self.type, self.description, self.required, self.readonly, self.validation)

    def _get(self, parent):
        return parent._values[self.name]

    def _set(self, parent, value):
        if self.readonly:
            raise ValueError(f"Cannot set value for '{self.name}' because it is a readonly property")

        if not self.type is None:
            if not type(value) is self.type:
                raise ValueError(f"Unexpected type for parameter '{type(value)}', expecting {self.type}.")

        if not self.validation is None:
            if not self.validation( value ):
                raise ValueError(f"Invalid value supplied for '{self.name}'." + 
                " Value must satisfy expression '{}'".format(_extract_lambda_expression(self.validation)) if self.validation.__name__ == '<lambda>' else '')
        
        parent._values[self.name] = value


"""
    Utility class to define construction parameters used by component factories
"""
class ComponentParameter(BaseParameter):
    """ defines a construction parameter used by component factories """
    def _set(self, parent, value):
        super()._set(parent, value)
        # rebuild the component to reflect the value change
        parent.rebuild()


"""
    provides a class type containing '_params', a dictionary 
    defining dynamic parameters assigned at runtime
"""
class _ComponentFactoryMeta(type):
    def __new__(cls, *args):
        inst = type.__new__(cls, *args)

        inst._params = dict()   # holds a ref to the calss parameters
        for key, param in args[2].items():
            if isinstance(param, Parameter):
                param.name = key
                inst._params[key] = param

        return inst
    

"""
    Base class for component factories providing dynamic runtime parameter association through kwargs
"""
class BaseComponentFactory(metaclass=_ComponentFactoryMeta):
    def __init__(self, *args, **kwargs):
        self._values = dict()   # holds the parameter instance values
        for key, param in self._params.items():
            self._values[key] = param.default
            if key in kwargs:
                self._values[key] = kwargs[key]
                kwargs.pop(key)
            else:
                if param.required:
                    raise AttributeError("Required parameter '%s' not initialized!" % key)

        # fire the build sequence
        self.before_build()
        self.build()
        self.after_build()
    
    def __repr__(self):
        # default string representation serializing factory parameters
        p = { k: v for k, v in self._values.items() if isnumber(v) or (type(v) is str) }
        if len(p) > 0:
            return '(' + ', '.join(["%s=%s" % (k,v) for k, v in p.items()]) + ')'
        return None

    """ must be implemented: called to generate the component geometry """
    def build(self):...
    
    """ must be implemented: called to reset/erase the component geometry """
    def destroy(self):...

    """ life-cycle hooks """
    def before_destroy(self):
        # do nothing
        pass

    def before_build(self):
        # do nothing
        pass

    def after_build(self):
        # do nothing
        pass

"""
    General purpose component factory class
"""
class ComponentFactory(BaseComponentFactory):
    """General purpose component factory class

    input:
    -----
        kwargs - name, value pairs to intialize component parameters
    """
    def __repr__(self):
        return self.unique_name()

    def destroy(self):
        self.shapes = list()
        self.ports = dict()

    def get_bounds(self):
        xy = []
        for layer, shape in self.shapes:
            xy.extend(shape.get_points())
        for port in self.ports.values():
            xy.append(port.position)
        return Bounds.fit(xy)

    def unique_name(self):
        return self.__class__.__name__  # TODO: This is not a unique instance name!

    def insert(self, layer: ProcessLayer, shape,  scale=1.0, rotation=0.0, translation=(0,0)):
        """ insert shape into component layer
        
        input:
            layer - ProcessLayer
            shape - SimplePolygon, Path, Text or a list of points Nx2 to build a polygon shape
        """

        self.before_insert()

        if isinstance(shape, list):
            shape = SimplePolygon(shape)

        if not isinstance(shape, (SimplePolygon, Path, Text)):
            raise ValueError('Invalid shape type supplied to insert()')
        
        # always keep a copy, not a ref
        item = shape.copy()
        item.transform(
            scale, 
            rotation, 
            translation)

        self.shapes.append((layer, item))

        self.after_insert()

    def port(self, name, position, direction='e', width=1.0):
        """ define a new port by name at position with given direction and width """
        self.before_port_define()

        self.ports[name] = Port(name, position, direction, width)
        
        self.after_port_define()

    def before_insert(self):
        # do nothing
        pass

    def after_insert(self):
        # do nothing
        pass

    def before_port_define(self):
        # do nothing
        pass

    def after_port_define(self):
        # do nothing
        pass