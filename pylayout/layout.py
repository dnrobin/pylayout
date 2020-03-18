from pylayout.math import Transform, Transformed, AABB, degrees, radians
from pylayout.utils import isnumeric, direction_angle, unique_name_for
from pylayout.builder import ComponentBuilder
from pylayout.process import ProcessLayer, DesignRules
from pylayout.routing import Port, Router
from pylayout.shapes import SimplePolygon, Path, FlexPath, RobustPath, Text

import gdspy

import copy
import inspect

class Component:
    """ Combines a GDSII cell with a dictionary of ports for routing

    Compoments are the building blocks of circuit layouts and are composed of shape primitives
    like simple polygons, paths and text labels attached to process layers. They should always 
    define art least one I/O port for routing if they are to be used in circuits.
    """
    def __init__(self, cell: gdspy.Cell, ports=dict()):
        assert isinstance(cell, gdspy.Cell)
        self.cell = cell
        self.ports = ports
    
    def get_bounds(self):
        return AABB(self.cell.get_bounding_box())


class ComponentLibrary:
    def __init__(self, filename=None, unit=1e-6, precision=1e-9):
        self._unit = unit
        self._precision = precision
        self._components = dict()

        if not filename is None:
            self.import_components(filename)

    @property
    def unit(self): return self._unit

    @property
    def precision(self): return self._precision

    def get_component(self, name):
        if name in self._components:
            return self._components[name]
        return None

    def __setitem__(self, key, value):
        if not isinstance(value, Component):
            raise ValueError("Cannot set item '%s' with value that is not a component!" % key)
        self._components[key] = value

    def __getitem__(self, key):
        if not key in self._components:
            raise KeyError("Component '%s' not found in library!" % key)
        return self._components[key]

    def __delitem__(self, key):
        if not key in self._components:
            raise KeyError("Component '%s' not found in library!" % key)
        del self._components[key]

    def add(self, name, component: Component):
        if not isinstance(component, Component):
            raise ValueError("Invalid argument supplied to add(), must be a component instance!")

        self._components[name] = component

    def import_components(self, filename, name=None):
        """ import components from GDSII file 
        
        input:
            if no name is provided, imports all components found in file
        """
        from os.path import realpath

        filename = realpath(filename)
        with open(filename, 'rb') as infile:
            lib = gdspy.GdsLibrary(unit=self._unit, precision=self._precision)
            lib.read_gds(infile, units='convert')

            if name is None:
                for cell in lib.cells.values():
                    self._components[cell.name] = Component(cell)
            else:
                if not name in lib.cells:
                    raise KeyError("Component '%' not found in GDS file '%s'!")

                self._components[cell.name] = Component(cell)


    def export_components(self, filename, name=None):
        """ export library to GDSII file

        input:
            if no name is provided, exports everything
        """
        from os.path import realpath

        filename = realpath(filename)
        with open(filename, 'wb') as outfile:
            lib = gdspy.GdsLibrary('library', None, self._unit, self._precision)

            if name is None:
                for comp in self._components.values():
                    lib.add(comp.cell, True, False, True)
            else:
                if not name in lib._components:
                    raise KeyError("Missing component '%' cannot be exported!")

                lib.add(self._components[name].cell, True, False, True)
            
            lib.write_gds(outfile)


class PortReference:
    """ Defines a proxy combining a port reference and a transform in the parent layout

    The PortReference references a real Port instance adding a layer of logic like transformations
    which allow generating multiple instances of the same Port over the circuit layout. The instancing is
    done within the parent ComponentReference, ComponentArray or ComponentVariants.
    """

    __slots__ = ("_port", "_local")

    def __init__(self, port: Port, local: Transform):
        self._port = port
        self._local = local

    @property
    def position(self): return self._local.apply(self._port.position)

    @property
    def direction(self): return degrees(self._local.rotation) + self._port.direction

    @property
    def width(self): return self._port.width

    def __repr__(self):
        return "Port %s, width: %s, direction: %s" % (self.position, self.width, self.direction)


class ComponentReference:
    """ Defines a proxy combining a component reference and a transform in the parent layout

    The ComponentReference references a single Component instance adding a layer of logic and control like
    transformations which allows genereting mutliple instances of the same Component over the circuit layout.
    The instancing is done via the place() methods of the layout. The component reference creates port references 
    from the referenced component in order to transform the coordinates of the placed ports in the layout used 
    for routing components together. It is possible to create arrays of references spanning a grid of rows and 
    collumns or event instantiate variations of the component in a side-by-side array (see ComponentArray and
    ComponentVariants).
    """

    __slots__ = ("cell", "ports")

    def __init__(self, comp: Component, local: Transform):
        self.cell = gdspy.CellReference(
            comp.cell, 
            local.translation, 
            degrees(local.rotation), 
            local.get_scale(1),
            x_reflection = local.get_scale(0) < 0)

        self.ports = dict()
        for name, port in comp.ports.items():
            self.ports[name] = PortReference(port, local)

    def get_bounds(self):
        return AABB(self.cell.get_bounding_box())
    
    def get_origin(self):
        return self.cell.origin
    
    def get_area(self):
        return self.cell.area()

    def get_port(self, key):
        if isnumeric(key):
            ports = self.ports.value()
            if key < 0 or key >= len(ports):
                raise IndexError('Port index out of range!')
            return ports[key]
        else:
            if key in self.ports:
                return self.ports[key]
            else:
                raise KeyError("Port name '%s' not found on component!" % key)


class ComponentArray:

    __slots__ = ("cell", "ports")

    def __init__(self, rows, cols, comp: Component, local: Transform, padding=0):
        assert cols > 0
        assert rows > 0
        if isnumeric(padding):
            padding = (padding, padding)

        sx, sy = comp.get_bounds().size()
        spacing = (sx + padding[0], sy + padding[1])

        self.cell = gdspy.CellArray(comp.cell, cols, rows, spacing, 
            local.translation, 
            degrees(local.rotation), 
            local.get_scale(1),
            x_reflection = local.get_scale(0) < 0)

        self.ports = list()
        for i in range(rows):
            self.ports.append([])
            for j in range(cols):

                dx, dy = local.apply((j * spacing[0], i * spacing[1]))
                t = Transform(local.get_scale(), local.rotation, (dx, dy))

                self.ports[i].append(dict())
                for name, port in comp.ports.items():
                    self.ports[i][j][name] = PortReference(port, t)

    def get_bounds(self):
        return AABB(self.cell.get_bounding_box())
    
    def get_origin(self):
        return self.cell.origin
    
    def get_area(self):
        return self.cell.area()

    def get_port(self, row, col, key):
        if row >= self.rows or col >= self.cols:
            raise ValueError("row, column out of range for component array of size [%d,%d]" % (self.rows, self.cols))

        if isnumeric(key):
            ports = self.ports[row][col].values()
            if key < 0 or key >= len(ports):
                raise IndexError('Port index out of range!')
            return ports[key]
        else:
            if key in self.ports[row][col]:
                return self.ports[row][col][key]
            else:
                raise KeyError("Port name '%s' not found on component!" % key)


class ComponentVariants:
    # TODO: ######################
    pass


class Layout:
    """ Defines a circuit-level description of components and routes

    The Layout is the parent cell for components and defines placed component references
    and port connections which are later used to generate traces for waveguides or electrical
    connections. It is possible to place sub layouts within a layout and thus build a hierarchy
    of cells from component definitions to device layout to system layout.
    """
    def __init__(self, name, gdslib=None, unit=1e-6, precision=1e-9):
        self.cell = gdspy.Cell(name)
        
        if gdslib is None:
            gdslib = gdspy.GdsLibrary(name, None, unit, precision)

        self._gdslib = gdslib
        self._unit = gdslib.unit
        self._precision = gdslib.precision
        self._gdslib.add(self.cell)     # add self to lib as top cell

        self._references = dict()       # dictionary of placed components
        self.connections = list()       # lisr of connections between ports

    @property
    def components(self): return self._references

    def get_bounds(self):
        return AABB(self.cell.get_bounding_box())

    def sub_layout(self, name, layout, origin=(0,0), orientation='e', scale=1.0, flipV=False, allow_multiple=False):
        if not isinstance(item, Layout):
            raise ValueError('Invalid argument supplied to sub_layout(), must be a Layout instance!')

        if isnumeric(scale):
            scale = (scale, scale)
        if flipV:
            scale[1] = -scale[1]

        self._gdslib.add(layout.cell, True, not allow_multiple, True)
        self.cell.add(gdspy.CellReference(layout.cell, 
            origin,
            direction_angle(orientation),
            scale[1],
            x_reflection = scale[0] < 0))

    def _place(self, name, item, origin=(0,0), orientation='e', scale=1.0, flipV=False, allow_multiple=False, **kwargs):
        if name in self._references:
            if not allow_multiple:
                raise ValueError("A component with the name '%s' already exists on the layout!" % name)
            name = unique_name_for(name, self._references)

        if isinstance(item, Component):
            comp = item
        else:

            if inspect.isclass(item):
                item = item(**kwargs)
            
            if not isinstance(item, ComponentBuilder):
                raise ValueError('Invalid argument supplied to place(), item must be a component instance or a builder!')

            comp = self._builer_to_cell(item)

        local = Transform(
            scale, 
            radians(direction_angle(orientation)), 
            origin, 
            self._unit, 
            self._precision)
        if flipV:
            local.flipV()

        self._gdslib.add(comp.cell)
        
        return (name, comp, local)

    def place(self, name, item, origin=(0,0), orientation='e', scale=1.0, flipV=False, allow_multiple=False, **kwargs):

        (name, comp, local) = self._place(name, item, origin, orientation, scale, flipV, allow_multiple, **kwargs)

        reference = ComponentReference(comp, local)
        self.cell.add(reference.cell)
        self._references[name] = reference

        return reference

    def place_array(self, name, item, rows, cols, padding=0, origin=(0,0), orientation='e', scale=1.0, flipV=False, allow_multiple=False, **kwargs):
        
        (name, comp, local) = self._place(name, item, origin, orientation, scale, flipV, allow_multiple, **kwargs)

        reference = ComponentArray(rows, cols, comp, local, padding)
        reference.cell.ref_cell.name = name
        self.cell.add(reference.cell)
        self._references[name] = reference

        return reference

    # def place_variants(self, name, item, spacing, vertical=False, **kwargs):
    #     # TODO: create cell instances for each item variation and add them to a parent cell and place that!
    #     pass
    
    def connect(self, port1_id, port2_id, bend_radius=1):
        port1 = self.get_port(port1_id)
        port2 = self.get_port(port2_id)

        if port1.width != port2.width:
            raise ValueError("Cannot connect ports '%s' and '%s' with different width" % (port1_id, port2_id))

        router = Router(port1, port2, self._unit, self._precision)
        
        self.connections.append(router)

        return router

    def get_component(self, name):
        if not name in self._references:
            raise KeyError("Component '%s' not found in current layout!" % name)
        return self._references[name]
        
    def get_port(self, identifier):
        import re
        match = re.fullmatch('(\w+)(?:\[(\d+)\])?(?:\[(\d+)\])?(?:\.(\w+))?', identifier)
        if match is None:
            raise ValueError('Invalid port identifier string!')
        
        groups = match.groups()
        
        comp_name = groups[0]
        if not comp_name in self._references:
            raise KeyError("Component '%s' not found in current layout!" % comp_name)

        component = self._references[comp_name]

        def _get(port_name, ports: dict):
            if len(ports) == 0:
                raise ValueError("Cannot create connection with component '%s', it has no ports!" % comp_name)

            if port_name is None:
                if len(ports) > 1:
                    raise ValueError("Missing port name for component '%s' with mutliple ports" % comp_name)

                return list(ports.values())[0]
            else:
                if not port_name in ports:
                    raise KeyError("Component '%s' has no port with the name '%s'" % (comp_name, port_name))
            
            return ports[port_name]
        

        if not groups[1] is None:
            index1 = int(groups[1])
            if not groups[2] is None:
                index2 = int(groups[2])

                if not isinstance(component, ComponentArray):
                    raise KeyError("Component '%s' is not an instance of ComponentArray" % comp_name)
                
                if len(component.ports) <= index1:
                    raise KeyError("Row index out of range for component array '%s'" % comp_name)

                if len(component.ports[index1]) <= index2:
                    raise KeyError("Column index out of range for component array '%s'" % comp_name)

                return _get(groups[3], component.ports[index1][index2])
            else:
                if not isinstance(component, ComponentVariants):
                    raise KeyError("Component '%s' is not an instance of ComponentVariants" % comp_name)

                if len(component.ports) < index1:
                    raise KeyError("Item index out of range for variations '%s'" % comp_name)

                return _get(groups[3], component.ports[index1])
        
        if not isinstance(component, ComponentReference):
            if isinstance(component, ComponentVariants):
                raise KeyError("Component '%s' is an instance of ComponentVariants and must be addressed by index" % comp_name)
            elif isinstance(component, ComponentArray):
                raise KeyError("Component '%s' is an instance of ComponentArray and must be addressed by [row][column]" % comp_name)
            else:
                raise KeyError("Unexpected type for component '%s'... Report this error." % comp_name)

        return _get(groups[3], component.ports)

    def _builer_to_cell(self, builder: ComponentBuilder):
        import gdspy

        cell = gdspy.Cell(unique_name_for(repr(builder), self._gdslib.cells))

        for layer, shape in builder.shapes:
            if isinstance(shape, (SimplePolygon, FlexPath, RobustPath)):
                cell.add(gdspy.Polygon(shape.get_points(self._unit, self._precision), layer.layer, layer.dtype))
            
            elif isinstance(shape, Path):
                if shape.gds_path:
                    cell.add(gdspy.FlexPath(
                        shape.get_points(self._unit, self._precision),
                        shape.width,
                        precision=self._precision/self._unit,
                        gdsii_path=True, 
                        layer=layer.layer,
                        datatype=layer.dtype))
                else:
                    cell.add(gdspy.Polygon(
                        shape.get_points(self._unit, self._precision), 
                        layer.layer, 
                        layer.dtype))

            elif isinstance(shape, Text):
                if shape.polygonal:
                    cell.add(gdspy.Text(
                        shape.text, 
                        shape.size, 
                        shape.position, 
                        True, 
                        degrees(shape.rotation), 
                        layer.layer, 
                        layer.dtype))
                else:
                    cell.add(gdspy.Label(
                        shape.text, 
                        shape.position,
                        shape.anchor, 
                        degrees(shape.rotation), 
                        shape.size, 
                        False,
                        layer.layer,
                        layer.dtype))

        return Component(cell, builder.ports)

    def save(self, filename):
        """ export layout to GDSII file """
        from os.path import realpath

        filename = realpath(filename)
        with open(filename, 'wb') as outfile:
            self._gdslib.write_gds(outfile)