from .math import Transform

class ParameterType(property):
    pass

class ParameterizableType(type):
    def __new__(cls, *args, **kwargs):
        obj = type.__new__(cls, *args, **kwargs)

        # define custom dunder property
        obj.__llparams__ = dict()
        
        # collect Parameter instances
        for name, prop in args[2].items():
            if isinstance(prop, ParameterType):
                prop.name = name
                obj.__llparams__[name] = prop

        return obj


class ParameterizableMixin(metaclass=ParameterizableType):
    """
        Mixin adding custom class parameter construct
    """
    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)

        # intercept Parameter custom initialisation
        obj.__llvalues__ = dict()
        for name, param in obj.__llparams__.items():
            param.set(obj, param.default)
        
            if name in kwargs:
                param.set(obj, kwargs[name])
            
            elif param.required:
                raise TypeError(f"__init__() missing required positional argument: '{name}'")

        return obj


class TransformableMixin:
    """
    Grant objects the ability to define a local transform.
    
    Children inherit the property 'local' defining a local transform and 
    inherit a few methods for transformations. They also recognize transform
    keywords passed in name/value pair at construct time.
    """
    def __new__(cls, *args, **kwargs):

        kv = {}
        for key in Transform.__init__.__code__.co_varnames:
            if key in kwargs:
                kv[key] = kwargs[key]
                del kwargs[key]

        instance = object.__new__(cls)
        instance.local = Transform(**kv)

        return instance

    def transform(self, translation=None, rotation=None, scale=None):
        self.local.transform(translation, rotation, scale)
    
    def flipH(self):
        self.local.flipH()

    def flipV(self):
        self.local.flipV()

    def flip(self):
        self.local.flip()

    def translate(self, dx, dy=None):
        self.local.translate(dx, dy)

    def rotate(self, angle):
        self.local.rotate(angle)

    def resize(self, scale):
        self.local.resive(scale)