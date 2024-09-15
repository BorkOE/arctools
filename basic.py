'''This module contains basic operations (loading, exporting, selecting) for arcgis
TODO:
    - load directory: loads all files of specified filetype(s) in dir, use glob
        - Check what filetypes requires what loading procedure

    - lyr.visible = False
        - Updates in map view. Can build functionality around this consept. lyr is layer object

    - Export spatial dataframe 
        - sdf.spatial.to_featureclass(location=r"c:\output_examples\census.shp")

    - delete fields (new file: data?)
        arcpy.management.DeleteField(lyr, sdf.loc[:,'CEEAC':'LDC'].columns.to_list())

    - Add fields
        arcpy.management.AddField(
        lyr,
        'Area',
        'FLOAT',
        )

    - Other interesting:
        - map.clearSelection() # Clears the selection for all layers and tables in a map
'''

from arcgis.features import GeoAccessor, GeoSeriesAccessor
from arcgis.gis import GIS
import pandas as pd
import arcpy
import os
from . import helpers
import tempfile

cwd = os.getcwd()
# Keep as globals to simplyfy workflow, change with relevant set function
aprx = None
map = None
lyr = None

def get_currrent_project():
    return arcpy.mp.ArcGISProject("CURRENT")

def get_map(**kwargs):
    if not kwargs.get('map_name'):   # Fetch by map_index, def. first project map
        map_name = aprx.listMaps()[kwargs.get('map_index', 0)].name
    else:
        map_name = kwargs.get('map_name')

    print(f'fetching map: {map_name}')
    return aprx.listMaps(map_name)[0]

def get_layer(supress_print=False, **kwargs):
    '''returns layer object'''
    if not map:
        set_map()
    if not kwargs.get('layer_name'):
        layer_name = map.listLayers()[kwargs.get('layer_index', 0)].name    # def. first layer
    else:
        layer_name = kwargs.get('layer_name')
    
    if not supress_print:
        print(f'fetching layer: {layer_name}')
    return map.listLayers(layer_name)[0]

def get_layer_names(**kwargs):
    '''returns list of layers in map'''
    if not map:
        set_map()
    return [l.name for l in map.listLayers()]

def set_map(**kwargs):
    '''
    map_name: str
    map_index: int, def. 0'''
    global map
    map = get_map(**kwargs)
    print(f'map set: {map.name}')
    return map

def set_layer(**kwargs):
    '''
    sets layer in module memory, also returns it
    layer_name: str
    layer_index: int, def. 0'''
    global lyr, map
    if not map:
        set_map()
    lyr = get_layer(**kwargs)
    print(f'layer set: {lyr.name}')
    return lyr

def set_visible(show_layers, hide_all_other=True, **kwargs):
    '''
    show_layers: list of layer names to be set as visible'''
    all_layers = set(get_layer_names(**kwargs))
    show_layers = set(show_layers)

    # Find and print faulty layer input
    not_recognized = show_layers.difference(all_layers)
    if not_recognized:
        print(f'Did not recognize layers: {not_recognized}')
    
    # Only make visible layers that exist
    show_layers = show_layers.intersection(all_layers)

    # Find layers to hide
    hide_layers = all_layers.difference(show_layers)

    # print('Show:')
    # print(show_layers)
    # print('Hide:')
    # print(hide_layers)

    if hide_all_other:
        for l in hide_layers:
            lyr_temp = get_layer(supress_print=True, layer_name=l)
            lyr_temp.visible = False

    for l in show_layers:
        lyr_temp = get_layer(supress_print=True, layer_name=l)
        lyr_temp.visible = True

def sdf_to_df(sdf_frame, **kwargs):
    '''writes/reads tempfile in cwd
    shapecol_to_drop: str, def. SHAPE
    
    Note encoding='latin-1' in pd.read_csv to handle scandinavian letters'''
    path = os.getcwd() + r'\temp'
    os.makedirs(path, exist_ok=True)
    f = tempfile.NamedTemporaryFile(dir=path)
    with open(f.name + '.csv', 'w') as file:
        (sdf_frame
            .drop(columns=kwargs.get('shapecol_to_drop', 'SHAPE'))
            .to_csv(file , sep=';', encoding='UTF-8'))
    frame = pd.read_csv(f.name + '.csv', sep=';', encoding='latin-1', index_col=0)
    f.close()   # Close tempfile
    return frame

def get_layer_dataframe(clear_select=True, sdf=False, **kwargs):
    '''Fetches dataframe
    layer_name: str
    layer_idx: int
    clear_selection: bool, it False, only return dataframe for selected features in layer attribute table. Else clears selection.
    sdf: bool, returns spatially enabled dataframe instead of regular pandas dataframe
    '''
    set_layer(**kwargs)
    if not lyr:
        print('Needs to set layer first!')
        return
    if clear_select:
        clear_selection(layer=lyr)   # Clears possible selection, else incomplete dataframe is returned
    out_frame = pd.DataFrame.spatial.from_featureclass(lyr)
    if sdf:
        return out_frame
    else:
        return sdf_to_df(out_frame)
        # return pd.read_clipboard(out_frame.drop(columns='SHAPE').to_clipboard())

def load_data(paths, **kwargs):
    '''Loads data from path, tested with shapefile. If no map specified, fetches first map
    paths: iterable with paths files, eg. r'path/to/shapefile.shp'
    map_name: str, map to add data to
    map_index: int, def. 0
    '''
    map = get_map(**kwargs)
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

def select(sql_where, selection_type="NEW_SELECTION", **kwargs):
    '''Selects features in attribute table based on sql query, uses layer set in this module
    sql_where: str, eg. """pop > 10000"""
    selection_type: str, selection behaviour, def. "NEW_SELECTION", see also "REMOVE_FROM_SELECTION"
    '''
    arcpy.SelectLayerByAttribute_management(in_layer_or_view=lyr, 
                                            selection_type=selection_type,
                                            where_clause=sql_where,
                                            **kwargs)

def select_by_location(in_layer, overlap_type, select_features, **kwargs):
    '''Select by location
    in_layer: str or layer
    overlap_type: str, eg. "BOUNDARY_TOUCHES", "WITHIN_A_DISTANCE"
    select_features: str or layer of target layer
    kwargs:
        - search_distance= numeric, eg. 30_000
        - selection_type: str, def. "NEW_SELECTION", see also "SUBSET_SELECTION", "ADD_TO_SELECTION", "REMOVE_FROM_SELECTION"
    '''
    
    with arcpy.EnvManager(scratchWorkspace=f"{cwd}\Default.gdb", workspace=f"{cwd}\Default.gdb"):
        arcpy.management.SelectLayerByLocation(helpers.get_layer_name(in_layer), 
                                               overlap_type, 
                                               helpers.get_layer_name(select_features),
                                               **kwargs)

def clear_selection(how='', layer=''):
    '''
    '''
    if how == 'all':
        if not map:
            print('load a map first using set_map')
            return
        map.clearSelection()
        # for lyr in [l.name for l in map.listLayers()]:
        #     try:
        #         arcpy.SelectLayerByAttribute_management(lyr, "CLEAR_SELECTION")
        #     except Exception as e:
        #         print(f'Exception occured while clearing selection for layer: {lyr}')
    elif layer:
        arcpy.SelectLayerByAttribute_management(helpers.get_layer_name(layer), "CLEAR_SELECTION")    
    else:
        print('Unclear arguments, specify how="all" or layer="layername" ')

def initialize():
    global aprx
    aprx = get_currrent_project()

initialize()