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

    - reclassify raster, arcpy.sa.Reclassify

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
from glob import glob

cwd = os.getcwd()
# Keep as globals to simplyfy workflow, change with relevant set function
aprx = None
map = None
lyr = None

def set_cwd(set_cwd):
   global cwd
   cwd = set_cwd

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

def set_layer(layer_name='', **kwargs):
    '''
    sets layer in module memory, also returns it
    layer_name: str
    layer_index: int, def. 0'''
    global lyr, map
    if not map:
        set_map()
    lyr = get_layer(layer_name=layer_name, **kwargs)
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

def get_layer_dataframe(layer_name='', clear_select=True, sdf=False, **kwargs):
    '''Fetches dataframe
    layer_name: str
    layer_idx: int
    clear_selection: bool, it False, only return dataframe for selected features in layer attribute table. Else clears selection.
    sdf: bool, returns spatially enabled dataframe instead of regular pandas dataframe
    '''
    if not layer_name in get_layer_names():
        print(f'could not find "{layer_name}" in layers. Attempting to interpret as table.')
        return pd.DataFrame(arcpy.da.TableToNumPyArray(layer_name, '*'))
    
    set_layer(layer_name=layer_name, **kwargs)
    if not lyr:
        print('Needs to set layer first!')
        return
    if clear_select:
        clear_selection(layer=lyr)   # Clears possible selection, else incomplete dataframe is returned
    try:
        out_frame = pd.DataFrame.spatial.from_featureclass(lyr)
        if sdf:
            return out_frame
        else:
            return sdf_to_df(out_frame)
    except KeyError as ke:
        print(ke)
        print('Trying to interpret input layer as table')
        return pd.DataFrame(arcpy.da.TableToNumPyArray(lyr, '*'))

def raster_to_dataframe(infeature, repeat_col='COUNT', field_names='*', **kwargs):
    '''Returns pd.DataFrame representation of raster where every row represent one cell
    infeature: str
    repeat_col: str, what column holds value for repeating rows'''
    
    frame = pd.DataFrame(arcpy.da.TableToNumPyArray(get_layer(infeature), 
                                                    field_names, 
                                                    **kwargs))
    return (frame
             .reindex(frame.index.repeat(frame[repeat_col]))
             .reset_index(drop=True))

def raster_float_to_dataframe(infeature):
    '''Returns pd.DataFrame representation of raster where every row represent one cell. NOTE: can be very slow due to iterating over every raster cell
    infeature: str, input raster layer name
    '''
    rast = arcpy.Raster(infeature)
    idx = []
    vals = []
    with arcpy.sa.RasterCellIterator({"rasters":[rast]}) as rci:
        for r in rci:
            idx.append(f'{r}')
            vals.append(rast[r])

    return pd.DataFrame.from_dict({'cell_val':vals, 'index':idx}).set_index('index')

def frame_to_raster(frame, ref_raster):
    '''Takes frame in tuple index of coordinates and one column with values and writes to raster. Returns raster object.
        frame: pd.DataFrame
        ref_raster: raster properties will be based on this raster'''
    rasInfo = ref_raster.getRasterInfo()
    out_raster = arcpy.Raster(rasInfo)
    for idx, val in frame.iloc[:, 0].items():
        if pd.isnull(val):
            continue    # No need to write null values
        
        x, y = eval(idx) # idx is a string tuple, so we evaluate to get true tupple
        out_raster[x, y] = val

    return out_raster

def find_input_files(dirpath='indata', filetypes=('tif', 'shp', 'jpg')):
    files = glob(f'{dirpath}/**/*', recursive=True)
    return [f'{cwd}\\{f}' for f in files if f.endswith(filetypes)]

def load_data(paths, **kwargs):
    '''Loads data from path, tested with shapefile. If no map specified, fetches first map
    paths: iterable with paths files, eg. r'path/to/shapefile.shp'
    map_name: str, map to add data to
    map_index: int, def. 0
    '''
    map = get_map(**kwargs)
    for path in paths:
        try:
            map.addDataFromPath(path)
            print(f'loaded {path}')
        except Exception as e:
            print(f'failed to load file: {path}')
            print(e)

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

def delete(in_data):
    '''Delete given data element
    in_data: str | list'''
    arcpy.management.Delete(in_data)

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

def clear_selection(how='all', layer='', **kwargs):
    '''
    how: str
    layer: str
    '''
    if (how == 'all') and (not layer):
        if not map:
            set_map(**kwargs)
        map.clearSelection()
        print('Cleared all selections!')
    elif layer:
        arcpy.SelectLayerByAttribute_management(helpers.get_layer_name(layer), "CLEAR_SELECTION")    
        print(f'Cleared selection in layer: {layer}')
    else:
        print('Unclear arguments, specify how="all" or layer="layername" ')

def update_symbology(lyr, label_color_dict,  alpha=100, renderer_name=None):
    '''Loops trough symbology items and updates labels and color
    lyr: arcpy layer object
    label_color_dict: dict of type {old_label:(new_label, [r,g,b,a]|hexcolor)}
        Leave new label or color as a falsey value to leave previous setting as is
    alpha: int, 0-100 that sets transparency, 0 is fully transparent
    renderer_name: str, if supplied will set symbology to this renderer. Avilable are:
            GraduatedColorsRenderer - A graduated colors renderer.
            GraduatedSymbolsRenderer - A graduated symbols renderer.
            UnclassedColorsRenderer - Unclassed colors renderer
            SimpleRenderer - A single symbol renderer.
            UniqueValueRenderer - A unique value renderer.
'''
    sym = lyr.symbology
    label_color_dict = {str(k):v for k,v in label_color_dict.items()} # cast keys to string
    
    if renderer_name is not None:
        sym.updateRenderer(renderer_name)
        lyr.symbology = sym    # Update symbology
        sym = lyr.symbology


    for sym_grp in sym.renderer.groups: # NOTE: sym.renderer prev was sym.colorizer
        for item in sym_grp.items:
            new_item_spec = label_color_dict.get(item.label)
            if new_item_spec:
                new_lab, color = new_item_spec
                if new_lab:
                    item.label = new_lab
                if color:
                    if isinstance(color, str):  # hex color, transform
                        color = helpers.hex_to_rgb(color)

                    if len(color) == 4:
                        item.symbol.color = {'RGB': color}
                    elif len(color) == 3:
                        item.symbol.color = {'RGB': color + [alpha]}
                    else:
                        print('Faulty RGB input!')
                    
    
    lyr.symbology = sym    # Update symbology

def initialize():
    global aprx
    aprx = get_currrent_project()

initialize()