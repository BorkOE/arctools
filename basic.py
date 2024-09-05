'''This submodule contains basic operations for arcgis
TODO:
    - load directory: loads all files of specified filetype(s) in dir, use glob
        - Check what filetypes requires what loading procedure
'''

from arcgis.features import GeoAccessor, GeoSeriesAccessor
from arcgis.gis import GIS
import pandas as pd
import arcpy
import os
from . import helpers

cwd = os.getcwd()

def get_currrent_project():
    return arcpy.mp.ArcGISProject("CURRENT")

def get_project_map(aprx, **kwargs):
    if not kwargs.get('map_name'):   # Fetch by map_index, default first project map
        map_name = aprx.listMaps()[kwargs.get('map_index', 0)].name

    print(f'fetching map: {map_name}')
    return aprx.listMaps(map_name)[0]

def get_layer(map, **kwargs):
    if not kwargs.get('layer_name'):
        layer_name = map.listLayers()[kwargs.get('layer_index', 0)].name
    else:
        layer_name = kwargs.get('layer_name')
    
    print(f'fetching layer: {layer_name}')
    return map.listLayers(layer_name)[0]

def get_layer_dataframe(**kwargs):
    '''Fetches data from the current working file. Returns sdf, lyr, map, aprx
    map_name: str
    map_index: int, def. 0
    layer_name: str
    layer_index: int, def. 0

    Notes:
    - Any selection will be cleared
    '''
    aprx = get_currrent_project()
    map = get_project_map(aprx, **kwargs)
    lyr = get_layer(map, **kwargs)
    clear_selection(lyr)   # Clears possible selection, else incomplete dataframe is returned
    sdf = pd.DataFrame.spatial.from_featureclass(lyr)
    return sdf, lyr, map, aprx

def load_data(paths, map=None, **kwargs):
    '''Loads data from path, tested with shapefile. If no map specified, fetches first map
    map: arcGIS map object
    paths: iterable with paths files, eg. r'path/to/shapefile.shp'
    map_name: str
    map_index: int, def. 0
    '''
    if not map:
        map = get_project_map(get_currrent_project(), **kwargs)
    for path in paths:
        map.addDataFromPath(path)
        print(f'loaded {path}')

def export_data(in_features, out_path, out_name, **kwargs):
    '''
    in_features: list or str of features, or layer
    out_path: str, directory (creates shapefile) or path to .gdb
    out_name: str
    where_clause: str, SQL where to filters data. Note that only selected 
                  features will be exported.
    field_mapping: TODO, should be able to mutate data etc
    '''
    in_features = helpers.get_layer_name(in_features)

    arcpy.conversion.FeatureClassToFeatureClass(in_features, 
                                out_path,
                                out_name,
                                **kwargs
                               )

def select(lyr, sql_where, selection_type="NEW_SELECTION", **kwargs):
    '''Selects features in attribute table based on sql query
    lyr: layer object
    sql_where: str, eg. """pop > 10000"""
    selection_type: str, selection behaviour, def. "NEW_SELECTION", see also "REMOVE_FROM_SELECTION"
    '''
    arcpy.SelectLayerByAttribute_management(in_layer_or_view=lyr, 
                                            selection_type=selection_type,         # This is def. see docstring for other
                                            where_clause=sql_where,
                                            **kwargs)

def select_by_location(in_layer, overlap_type, select_features, **kwargs):
    '''Select by location
    in_layer: str or layer
    overlap_type: str, eg. "BOUNDARY_TOUCHES", "WITHIN_A_DISTANCE"
    select_features: str or layer of target layer
    '''
    
    with arcpy.EnvManager(scratchWorkspace=f"{cwd}\Default.gdb", workspace=f"{cwd}\Default.gdb"):
        arcpy.management.SelectLayerByLocation(helpers.get_layer_name(in_layer), 
                                               overlap_type, 
                                               helpers.get_layer_name(select_features),
                                               **kwargs)

def clear_selection(lyr):
    '''TODO: option to loop over and clear all layers
    '''
    arcpy.SelectLayerByAttribute_management(lyr, "CLEAR_SELECTION")    
