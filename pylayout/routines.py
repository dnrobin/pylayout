import pylayout.process as process

import os
import re

def import_klayout_layers(filename):
    """ Import *.lyp file and return a ProcessLayers instance

        Author: Thomas Lima (https://github.com/lightwave-lab/zeropdk)
        Modified: Daniel Robin March 2020
    """
    import xmltodict
    
    layers = process.ProcessLayers()

    filename = os.path.realpath(filename)
    with open(filename, 'r') as file:
        layer_dict = xmltodict.parse(file.read())["layer-properties"]["properties"]

        layer_map = {}

        for k in layer_dict:
            layerInfo = k["source"].split("@")[0]
            if "group-members" in k:
                # encoutered a layer group, look inside:
                j = k["group-members"]
                if "name" in j:
                    layerInfo_j = j["source"].split("@")[0]
                    layer_map[j["name"]] = (layerInfo_j, j["frame-color"], j["fill-color"], j["dither-pattern"])
                else:
                    for j in k["group-members"]:
                        layerInfo_j = j["source"].split("@")[0]
                        layer_map[j["name"]] = (layerInfo_j, j["frame-color"], j["fill-color"], j["dither-pattern"])
                if k["source"] != "*/*@*":
                    layer_map[k["name"]] = (layerInfo, j["frame-color"], j["fill-color"], j["dither-pattern"])
            else:
                try:
                    layer_map[k["name"]] = (layerInfo, k["frame-color"], k["fill-color"], k["dither-pattern"])
                except TypeError as e:
                    new_message = "Bad name for layer {}. Check your .lyp XML file for errors.".format(layerInfo)
                    raise TypeError(new_message) from e

        for layer_name, layer_info in layer_map.items():
            layer, dtype = layer_info[0].split('/')
            layers.add_layer(layer_name, int(layer), int(dtype), 
                export=True, edgecolor=layer_info[1], facecolor=layer_info[2], dither=layer_info[3])

    return layers

def import_calibre_layers(filename):
    """ Import *.cal file containing LAYER definitions and return a ProcessLayers instance
    """
    layers = process.ProcessLayers()

    filename = os.path.realpath(filename)
    with open(filename, 'r') as file:
        line = file.readline()

        _i = 1
        _await_layer_name = False
        while line:
            if _await_layer_name:
                match = re.search('LAYER (\w+)', line)
                if match is None:
                    raise ValueError("Error at line %s, expecting layer name following layer definition" % _i)
                
                name = match.group(1)
                _await_layer_name = False
                layers.add_layer(name, int(layer), int(dtype), doc=doc.strip())

            else:
                match = re.search('LAYER MAP (\d+) DATATYPE (\d+).+?// ([\w\s]+)', line)
                if not match is None:
                    layer = match.group(1)
                    dtype = match.group(2)
                    doc = match.group(3)
                    _await_layer_name = True
            
            line = file.readline()
            _i += 1

    return layers

def import_calibre_design_rules(filename):
    """ Import *.cal file containing VARIABLE definitions and return a DesignRules instance

    Note that VARIABLE definitions are not design rules, but constants used by DRC -- this may not apply to all fab conventions!
    """
    rules = process.DesignRules()

    filename = os.path.realpath(filename)
    with open(filename, 'r') as file:
        line = file.readline()

        _i = 1
        while line:
            match = re.search('VARIABLE (\w+)\s+([\d.]+)', line)
            if match:
                rules.add_rule(match.group(1), float(match.group(2)))
            
            line = file.readline()
            _i += 1

    return rules