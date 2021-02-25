from .math import *

class Transformable:
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