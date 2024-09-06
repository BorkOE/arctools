from arcgis.features import GeoAccessor, GeoSeriesAccessor
from arcgis.gis import GIS
import pandas as pd
import arcpy
import os
from . import helpers

cwd = os.getcwd()

def calculate_geometry(in_features, geometry_property, length_unit='METERS', **kwargs):
    '''
    in features: str, eg. "Roads_within"
    geometry_property: str, eg. "LENGTH LENGTH"'''
    arcpy.management.CalculateGeometryAttributes(in_features, 
                                                 geometry_property, 
                                                 length_unit,
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
