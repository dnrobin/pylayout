from pylayout.utils import get_lambda_expr, isnumeric

import copy

class Parameter(property):
    __slots__ = ('name', 'value', 'default', 'description', 'readonly', 'validate', 'required', 'type')

    def __init__(self, default=None, type=None, description='', readonly=True, validated=None, required=False):
        super().__init__(self._get, self._set, doc=description)
        
        self.name           = None
        self.type           = type
        self.default        = default
        self.description    = description
        self.readonly       = readonly
        self.validate       = validated
        self.required       = required

    def copy(self):
        return Parameter(self.default, self.type, self.description, self.readonly, self.validate, self.required)

    def _get(self, parent):
        return parent._values[self.name]

    def _set(self, parent, value):
        if self.readonly:
            raise ValueError("Cannot set value for '%s' because it is a readonly property" % self.name)

        if not self.type is None:
            if not type(value) is self.type:
                raise ValueError("Unexpected type for parameter '%s', expecting %s." % (type(value), self.type))

        if not self.validate is None:
            if not self.validate(value):
                raise ValueError("Invalid value supplied for '{}'. {}"
                    .format(self.name, "Value must satisfy '{}'"
                        .format(get_lambda_expr(self.validate)) if self.validate.__name__ == '<lambda>' else ''))
        
        parent._values[self.name] = value


class _ParameterContainerMeta(type):
    """ provides a class with a _params dictionary defining dynamic paramaters assigned in constructor """
    def __new__(cls, *args):
        instance = type.__new__(cls, *args)

        instance._params = dict()   # holds a ref to the calss parameters
        for key, param in args[2].items():
            if isinstance(param, Parameter):
                param.name = key
                instance._params[key] = param

        return instance
    

class ParameterContainer(metaclass=_ParameterContainerMeta):
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
    
    def __repr__(self):
        p = { k: v for k, v in self._values.items() if isnumeric(v) or (type(v) is str) }
        if len(p) > 0:
            return '(' + ', '.join(["%s=%s" % (k,v) for k, v in p.items()]) + ')'
        return None