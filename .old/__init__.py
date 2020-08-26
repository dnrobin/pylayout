from pylayout.core import PylayoutNotice, PylayoutWarning, PylayoutException
from pylayout.math import Vec, Transform, QuickPath, AABB
from pylayout.process import ProcessLayers, DesignRules
from pylayout.routing import Port, Connection
from pylayout.builder import BuildParameter, ComponentBuilder, TraceTemplate, Waveguide
from pylayout.layout import (
    Component, 
    PortReference,
    ComponentLibrary, 
    ComponentReference, 
    ComponentArray, 
    ComponentVariants, 
    Layout)

import pylayout.utils as utils
import pylayout.shapes as shapes
# import pylayout.viewer as viewer
import pylayout.routines as routines

import sys
import warnings

__exceptions_as_warnings = True
def print_warnings(print_warnings=True):
    global __exceptions_as_warnings
    if print_warnings:
        if __exceptions_as_warnings:
            warnings.simplefilter("default", PylayoutException)
        warnings.simplefilter("default", PylayoutWarning)
    else:
        if __exceptions_as_warnings:
            warnings.simplefilter("ignore", PylayoutException)
        warnings.simplefilter("ignore", PylayoutWarning)

def treat_exceptions_as_warnings(as_warnings=True):
    global __exceptions_as_warnings
    __exceptions_as_warnings = as_warnings
    if __exceptions_as_warnings:
        warnings.simplefilter("default", PylayoutException)
    else:
        warnings.simplefilter("error", PylayoutException)

def __print_pylayout_warning(message, category, filename, lineno, file=None, line=None):
    if category in (PylayoutNotice, PylayoutWarning, PylayoutException):
        print('%s' % message)
    else:
        sys.stderr.writelines(warnings.formatwarning(message, category, filename, lineno, line))

warnings.showwarning = __print_pylayout_warning
