import arcpy

def get_layer_name(in_features):
    '''Takes any object - if layer returns name of layer'''
    if isinstance(in_features, arcpy._mp.Layer):
            in_features = in_features.name
    return in_features