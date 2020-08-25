from .common import *
from .vector import Vector

__all__ = ["Transform"]

class Transform:
    """ Represents a 2D transformation

    The transform is a local-to-parent representation used to transform sets of vertices to
    new coordinates. The components of the transform, ie. scale, rotation and translation, 
    are stored and can be altered with the respective functions or by applying another transform.

    input:
    -----
        scale - number or vector-like combining (scale_x, scale_y)
        rotation - number, angle in *radians*
        translation - vector-like, translation (dx, dy)
    """
    def __init__(self, scale=1.0, rotation=0.0, translation=(0,0)):
        """
        input:
        ------
            scale - number or vector-like, scale factor for x and y
            rotation - number, angle in *degrees*
            translation - vector-like, translation (dx, dy)
        """
        if not __isvectortype(translation):
            raise TypeError("'translation' must be a valid vector type")

        self.setTransform(scale, 
                          rotation, 
                          translation)

    def setTransform(self, scale=1,  rotation=0, translation=(0,0)):
        self.__scale = Vector(scale)
        self.__rotation = radians(rotation)
        self.__translation = Vector(translation)

    def assign(self, t):
        assert isinstance(t, Transform)
        self.__scale = t.__scale
        self.__rotation = t.__rotation
        self.__translation = t.__translation

    @property
    def origin(self):
        return -self.__translation

    @property
    def translation(self):
        return self.__translation

    @property
    def rotation(self):
        return degrees(self.__rotation)
    
    @property
    def scale(self):
        return self.__scale

    @property
    def scaleX(self):
        return self.__scale.x

    @property
    def scaleY(self):
        return self.__scale.x

    @translation.setter
    def translation(self,value):
        assert(__isvectortype(value))
        self.__translation = Vector(value)

    @rotation.setter
    def rotation(self,value):
        assert(__isnumbertype(value))
        self.__rotation = radians(value)

    @scale.setter
    def scale(self,value):
        assert __isnumbertype(value) or __isvectortype(value)
        self.__scale = Vector(value)

    @scale.setter
    def scaleX(self,value):
        assert __isnumbertype(value)
        self.__scale.x = value

    @scale.setter
    def scaleY(self,value):
        assert __isnumbertype(value)
        self.__scale.y = value

    def scale(self, scale):
        """ apply scaling factor """
        self.__scale *= Vector(scale)

    def rotate(self, angle):
        """ apply rotation by angle in *degrees* """
        self.__rotation = wrapangle(self.__rotation + radians(angle))

    def translate(self, d, y=False):
        """ apply translation """
        if not y:
            self.__translation += Vector(d)
        else:
            self.__translation += Vector(d, y)

    def flipV(self):
        """ reflect y-coordinate (mutates the transform) """
        self.__scale.y *= -1

    def flipH(self):
        """ reflect x-coordinate (mutates the transform) """
        self.__scale.x *= -1

    def reflect(self):
        """ reflect off the diagonal (mutates the transform) """
        self.__scale *= -1

    def reset(self):
        """ reset transformation to identity """
        self.setTransform()
    
    def __repr__(self):
        return "scale: (%.2f, %.2f), rotation: %.2f, translation: (%.2f, %.2f)" %(
            self.__scale.x, self.__scale.y, self.__translation.x, self.__translation.y, self.__rotation)