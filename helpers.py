import arcpy

spatial_references = {
      'RT90_25_gon_V' : arcpy.SpatialReference(3021),
}

def get_layer_name(in_features):
    '''Takes any object - if layer returns name of layer'''
    if isinstance(in_features, arcpy._mp.Layer):
            in_features = in_features.name
    return in_features

def hex_to_rgb(hex_color):
    '''returns rgb list: [r,g,b]
    hex_color: str'''
    # Remove the '#' character if it exists
    hex_color = hex_color.lstrip('#')
    
    # Convert the hex to RGB
    rgb = list(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    return rgb

def get_fields(lyr):
    '''Returns all editable (not readonly) and non-geometry fields in layer
        lyr: str'''
    desc = arcpy.Describe(lyr)
    return [f.name for f in desc.fields if (f.editable) and (not f.type.lower() == 'geometry')]
