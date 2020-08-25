from pylayout.core import _pylayout_exception
from pylayout.math import Transform, AABB, direction_angle, radians, degrees
from pylayout.shapes import SimplePolygon, Path, Text
from pylayout.builder import ComponentBuilder
from pylayout.routing import Port, Connection
from pylayout.utils import isnumber, dict_at, unique_name_for

import gdspy
import inspect

class Component:
    """ Combines a GDSII cell with a dictionary of ports for routing

    Compoments are the building blocks of circuit layouts and are composed of shape primitives
    like simple polygons, paths and text labels attached to process layers. They should always 
    define art least one I/O port for routing if they are to be used in circuits.
    """
    def __init__(self, cell: gdspy.Cell, ports=None):
        assert isinstance(cell, gdspy.Cell)

        if ports is None:
            ports = dict()
        
        self.cell = cell
        self.ports = ports
    
    def get_bounds(self):
        return AABB(self.cell.get_bounding_box())

    def get_port(self, key):
        if isnumber(key):
            return dict_at(self.ports, key)
        else:
            if key in self.ports:
                return self.ports[key]
            else:
                raise KeyError("Port name '%s' not found on component!" % key)


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

    def __iter__(self):
        return iter(self._components)

    def __len__(self):
        return len(self._components)

    def __repr__(self):
        return "\n".join(["%s ['"%key + "', '".join(item.ports) + "']\n" for key, item in self._components.items()])

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
                    raise KeyError("Component '%s' not found in GDS file '%s'!" % (name, filename))

                self._components[name] = Component(lib.cells[name])


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
                    raise KeyError("Missing component '%s' cannot be exported!" % name)

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

    __slots__ = ("name", "cell", "ports")

    def __init__(self, name: str, comp: Component, local: Transform):

        origin = local.translation
        rotation = degrees(local.rotation)
        magnification = abs(local.get_scale(1))
        x_reflection = local.get_scale(0) < 0

        # flipV implemententation
        if local.get_scale(1) < 0:
            origin = (origin[0], -origin[1])
            rotation = 180 + rotation
            x_reflection = True
        
        self.name = name
        self.cell = gdspy.CellReference(
            comp.cell, 
            origin, 
            rotation,
            magnification,
            x_reflection)   # !!! x_reflection doesn't seem to apply...

        self.ports = dict()
        for name, port in comp.ports.items():
            if isinstance(port, PortReference):
                self.ports[name] = PortReference(port._port, local * port._local)
            else:
                self.ports[name] = PortReference(port, local)

    def __getitem__(self, port_name):
        return self.get_port(port_name)

    def get_bounds(self):
        return AABB(self.cell.get_bounding_box())
    
    def get_origin(self):
        return self.cell.origin
    
    def get_area(self):
        return self.cell.area()

    def get_port(self, key):
        if isnumber(key):
            return dict_at(self.ports, int(key))
        else:
            if key in self.ports:
                return self.ports[key]
            else:
                raise KeyError("Port name '%s' not found on component!" % key)


class ComponentArray:
    """ Defines a proxy array combining a component reference and a transform in the parent layout """

    __slots__ = ("name", "cell", "ports")
        
    def __init__(self, rows, cols, name: str, comp: Component, local: Transform, spacing=0):
        assert cols > 0
        assert rows > 0

        origin = local.translation
        rotation = degrees(local.rotation)
        magnification = abs(local.get_scale(1))
        x_reflection = local.get_scale(0) < 0

        # flipV implemententation
        if local.get_scale(1) < 0:
            origin = (origin[0], -origin[1])
            rotation = 180 + rotation
            x_reflection = True

        if isnumber(spacing):
            spacing = (spacing, spacing)

        self.name = name
        self.cell = gdspy.CellArray(
            comp.cell,
            cols,
            rows,
            spacing,  
            origin, 
            rotation,
            magnification,
            x_reflection)   # !!! x_reflection doesn't seem to apply...

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

        if isnumber(key):
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
    def __init__(self):
        raise NotImplementedError("ComponentVariants is not yet implemented")


class Layout:
    """ Defines a circuit-level description of components and routes

    The Layout is the parent cell for components and defines placed component references
    and port connections which are later used to generate traces for waveguides or electrical
    connections. It is possible to place sub layouts within a layout and thus build a hierarchy
    of cells from component definitions to device layout to system layout.
    """
    def __init__(self, name, lib=None, unit=1e-6, precision=1e-9):
        """
        input:
            name - str, a allow_duplicates name for this layout
            lib - ComponentLibrary, shared component library or None to create a new one
            unit, precision - number, snap all layout elements to the grid defined by grid=(precision/unit)
        """
        self.cell = gdspy.Cell(name, exclude_from_current=True)
        self._name = name
        
        if lib is None:
            lib = ComponentLibrary(unit=unit, precision=precision)

        self._lib = lib
        self._unit = lib.unit
        self._precision = lib.precision

        self.ports = dict()            # dictionary of exposed ports
        
        self._references = dict()       # dictionary of placed components
        self._connections = list()      # list of connections between ports

    def __getitem__(self, key):
        if isnumber(key):
            return dict_at(self.ports, int(key))
        else:
            if key in self.ports:
                return self.ports[key]
            else:
                raise KeyError("Port name '%s' not found in layout!" % key)

    def __getattribute__(self, key):
        if key in object.__getattribute__(self, '_references'):
            return object.__getattribute__(self, '_references')[key]
        else:
            return object.__getattribute__(self, key)

    def port(self, name, port):
        self.ports[name] = self._port(port)

    def get_bounds(self):
        return AABB(self.cell.get_bounding_box())

    def place_layout(self, layout, origin=(0,0), orientation='e', scalefactor=1.0, flipV=False, allow_duplicates=False):
        """ insert a layout into this layout at coordinates given by origin 
        
        input:
            layout - Layout, the layout instance to be inserted
            allow_duplicates - bool, if false, allow inserting multiple copies of the same layout generating a allow_duplicates name for them

        output:
            name of the inserted layout (same if allow_duplicates or generated name if a copy)
        """
        if not isinstance(layout, Layout):
            raise ValueError('Invalid argument supplied to place_layout(), must be a Layout instance!')

        name = layout._name
        if name in self._references:
            if not allow_duplicates:
                raise ValueError("A sub layout by the name '%s' already exists in the layout '%s'" % (name, self._name))
            name = unique_name_for(name, self._references)
            
            # TODO: changing all names???
            layout._name = name
            layout.cell.name = name
        
        def _rename_children(parent):
            # TODO: only rename what is truly unique...??
            for ref in parent.get_dependencies(True):
                _rename_children(ref)
                ref.name = "%s.%s" % (parent.name, ref.name)
        _rename_children(layout.cell)

        local = Transform(
            scalefactor, 
            radians(direction_angle(orientation)), 
            origin, 
            self._unit, 
            self._precision)
        if flipV:
            local.flipV()

        reference = ComponentReference(name, layout, local)
        self.cell.add(reference.cell)
        self._references[name] = reference        

        return reference

    def _place(self, name, item, origin=(0,0), orientation='e', scalefactor=1.0, flipV=False, params=None, allow_duplicates=False):
        
        if name == self._name:
            raise ValueError("Cannot place a component with the same name as the layout name!")
        
        if name in self._references:
            if not allow_duplicates:
                raise ValueError("A component with the name '%s' already exists in the layout!" % name)
            name = unique_name_for(name, self._references)

        if isinstance(item, Component):
            comp = item

        elif isinstance(item, str):
            if not item in self._lib:
                raise ValueError("Component name '%s' not found in layout's component library!" % item)
            comp = self._lib[item]

        else:

            if inspect.isclass(item):
                if params is None:
                    item = item()
                else:
                    item = item(**params)
            
            if not isinstance(item, ComponentBuilder):
                raise ValueError('Invalid argument supplied to place(), item must be a component instance or a builder!')

            comp = self._builer_to_cell(item)

        local = Transform(
            scalefactor, 
            radians(direction_angle(orientation)), 
            origin, 
            self._unit, 
            self._precision)
        if flipV:
            local.flipV()
        
        return (name, comp, local)

    def place(self, name, item, origin=(0,0), orientation='e', scalefactor=1.0, flipV=False, params=None, allow_duplicates=False):
        """ place a component at (x, y) in the layout """
        (name, comp, local) = self._place(name, item, origin, orientation, scalefactor, flipV, params, allow_duplicates)

        reference = ComponentReference(name, comp, local)
        self.cell.add(reference.cell)
        self._references[name] = reference

        return reference

    def array(self, name, item, rows, cols, spacing=0, origin=(0,0), orientation='e', scalefactor=1.0, flipV=False, params=None, allow_duplicates=False):
        """ place a 2x2 array of components at (x, y) in the layout """
        (name, comp, local) = self._place(name, item, origin, orientation, scalefactor, flipV, params, allow_duplicates)

        reference = ComponentArray(rows, cols, name, comp, local, spacing)
        self.cell.add(reference.cell)
        self._references[name] = reference

        return reference

    def _port(self, port):
        if isinstance(port, PortReference):
            return port
        elif isinstance(port, ComponentReference):
            return self._find_internal_port(port.name)
        elif isinstance(port, str):
            return self._find_internal_port(port)
        elif isinstance(port, Component):
            raise ValueError("Cannot route a library component! The component must first be place on the layout.")
        else:
            raise TypeError("Invalid argument type for port in connect(), got %s" % type(port))
    
    def connect(self, port1, port2):
        """ connect two ports to create a route 

        input:
            port1, port2 - PortRef, ComponentReference or string of the form '<component_name> ([<row>]) ([<col>]) (.<port_name>)'
            Note: if a ComponentReference is passed, or a component_name alone is given, the function checks to see if the 
            component has only a single port, and if so, uses that one, otherwise raises an error to require more identification.
        """
        _port1 = self._port(port1)
        _port2 = self._port(port2)

        if _port1.width != _port2.width:
            _pylayout_exception("Cannot connect ports '%s' and '%s' with different width" % (_port1, _port2))

        connection = Connection(_port1, _port2, self._unit, self._precision)
        
        self._connections.append(connection)

        return connection

    def get_component(self, name: str):
        """ get placed component by name """
        if not name in self._references:
            raise KeyError("Component '%s' not found in layout '%s'" % (name, self._name))
        return self._references[name]

    def get_layout(self, name: str):
        """ get placed layout by name """
        if not name in self._references:
            raise KeyError("Sublayout '%s' not found in layout '%s'" % (name, self._name))
        return self._references[name]

    def get_port(self, name: str):
        """ get layout port by name """
        if not name in self.ports:
            raise KeyError("Port '%s' not found in layout '%s'" % (name, self._name))
        return self.ports[name]
        
    def _find_internal_port(self, identifier: str):
        import re

        match = re.fullmatch('(\w+)(?:\[(\d+)\])?(?:\[(\d+)\])?(?:\.(\w+))?', identifier)
        if match is None:
            raise ValueError('Invalid port identifier string!')
        
        groups = match.groups()
        
        comp_name = groups[0]
        if not comp_name in self._references:
            raise KeyError("Component '%s' not found in layout '%s'" % (comp_name, self._name))

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

        name = repr(builder)

        # NOTE: this automotamic behavior can be a real pain to debug in the event of two distinct
        #   component builder instances generating the same name without the user aware! Always make
        #   a unique name?

        if name in self._lib:
            return self._lib[name]

        else:
            cell = gdspy.Cell(name, exclude_from_current=True)

            for layer, shape in builder.shapes:
                # TODO: consider wrapping all gdspy primitives at the shape level
                if isinstance(shape, SimplePolygon):
                    cell.add(gdspy.Polygon(shape.get_points(self._unit, self._precision), layer.layer, layer.dtype))
                
                elif isinstance(shape, Path):
                    path = shape._path

                    # apply the local transform
                    path.transform(
                        shape._local.translation,
                        shape._local.rotation,
                        shape._local.get_scale(1),
                        shape.get_scale(0) < 0)
                    
                    # set the layer/datatype of all polygons
                    for i in range(len(path.layers)):
                        path.layers[i] = layer.layer
                        path.datatypes[i] = layer.dtype
                    
                    cell.add(path)

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

            c = Component(cell, builder.ports)
            self._lib.add(name, c)
            return c

    def save(self, filename=None):
        """ export layout to GDSII file """
        from os.path import realpath

        if filename is None:
            filename = self._name + '.gds'

        lib = gdspy.GdsLibrary(self._name, unit=self._unit, precision=self._precision)
        lib.add(self.cell, True, False, True)

        filename = realpath(filename)
        with open(filename, 'wb') as outfile:
            lib.write_gds(outfile)

class Device:
    """ a combination of a layout containing placed cells, routes and optional connectivity ports to be used at the system level """
    pass

class DeviceReference:
    pass