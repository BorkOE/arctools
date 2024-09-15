from arcgis.features import GeoAccessor, GeoSeriesAccessor
from arcgis.gis import GIS
import pandas as pd
import arcpy
import os
from . import helpers

cwd = os.getcwd()

def calculate_geometry(in_features, geometry_property, **kwargs):
    '''
    in features: str, eg. "Roads_within"
    geometry_property: str, eg. "LENGTH LENGTH", "Area_field AREA_GEODESIC"
    length_unit: str, eg. "METERS"
    area_unit: str, eg. "SQUARE_KILOMETERS", "HECTARES"
    '''
    arcpy.management.CalculateGeometryAttributes(in_features, 
                                                 geometry_property, 
                                                 **kwargs)

def overlay_intersect(in_features, out_path, out_name, **kwargs):
    '''Performs intersect
    in_features: list, eg. ["suitable_roads", "nature reserve"]
    out_path: str
    out_name: str, eg. Roads_within.shp
    '''
    with arcpy.EnvManager(scratchWorkspace=f"{cwd}\Default.gdb", workspace=f"{cwd}\Default.gdb"):
        arcpy.analysis.Intersect(in_features, 
                                f"{out_path}\{out_name}", 
                                **kwargs
                                )

def coordinates_from_point_geometry(frame, new_x_col='x', new_y_col='y', shape_col='SHAPE'):
    '''returns frame with new coordinate cols
    TODO: expect it to work with polygons also, check
    '''
    frame[new_x_col], frame[new_y_col] = zip(*frame[shape_col].apply(lambda x: (x.centroid[0], x.centroid[1])))
    return frame