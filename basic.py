'''This submodule contains basic operations for arcgis'''

from arcgis.features import GeoAccessor, GeoSeriesAccessor
from arcgis.gis import GIS
import pandas as pd
import arcpy

def get_currrent_project():
    return arcpy.mp.ArcGISProject("CURRENT")

def get_project_map(aprx, **kwargs):
    if not kwargs.get('map_name'):   # Fetch by map_index, default first project map
        map_name = aprx.listMaps()[kwargs.get('map_index', 0)].name

    print(f'fetching map: {map_name}')
    return aprx.listMaps(map_name)[0]

def get_layer(project_map, **kwargs):
    if not kwargs.get('layer_name'):
        layer_name = project_map.listLayers()[kwargs.get('layer_index', 0)].name
    else:
        layer_name = kwargs.get('layer_name')
    
    print(f'fetching layer: {layer_name}')
    return project_map.listLayers(layer_name)[0]

def get_layer_dataframe(**kwargs):
    '''Fetches data from the current working file. Returns sdf (pd.DataFrame), lyr, project_map, aprx
    map_name: str
    map_index: int, def. 0
    layer_name: str
    layer_index: int, def. 0
    '''
    aprx = get_currrent_project()
    project_map = get_project_map(aprx, **kwargs)
    lyr = get_layer(project_map, **kwargs)
    sdf = pd.DataFrame.spatial.from_featureclass(lyr)
    return sdf, lyr, project_map, aprx

