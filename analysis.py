from arcgis.features import GeoAccessor, GeoSeriesAccessor
from arcgis.gis import GIS
import pandas as pd
import arcpy
import os
from . import helpers

cwd = os.getcwd()
scratch_workspace = f"{cwd}\Default.gdb"

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
    with arcpy.EnvManager(scratchWorkspace=scratch_workspace, workspace=scratch_workspace):
        arcpy.analysis.Intersect(in_features, 
                                f"{out_path}\{out_name}", 
                                **kwargs
                                )

def buffer(in_features, outdir, out_name, buffer_distance_or_field, line_side='FULL', line_end_type='ROUND', **kwargs):
    '''
    in_features: str, eg. "stream1order"
    outdir: str
    out_name: str
    buffer_distance_or_field: str, eg. "20 Meters"
    '''
    with arcpy.EnvManager(scratchWorkspace=scratch_workspace, workspace=scratch_workspace):
        arcpy.analysis.Buffer(in_features, 
                              f"{outdir}\{out_name}", 
                              buffer_distance_or_field,
                              line_side,
                              line_end_type,
                              **kwargs,
                              )

def overlay(input_layer, overlay_layer, outdir, out_name, overlay_type, **kwargs):
    '''
    input_layer: str
    overlay_layer: str
    outdir: str
    out_name: str
    overlay_type: str, INTERSECT, ERASE, UNION, IDENTITY, SYMMETRICAL_DIFFERENCE
    '''
    arcpy.gapro.OverlayLayers(
        input_layer, 
        overlay_layer, 
        f"{outdir}\{out_name}", 
        overlay_type)

def merge(in_features, outdir, out_name):
    '''
    in_features: list of layer names (str)
    outdir: str
    out_name: str
    '''
    in_features_str = ';'.join(in_features)
    arcpy.management.Merge(in_features_str, 
                           f"{outdir}\{out_name}", 
                          )

def coordinates_from_point_geometry(frame, new_x_col='x', new_y_col='y', shape_col='SHAPE'):
    '''returns frame with new coordinate cols
    TODO: expect it to work with polygons also, check
    '''
    frame[new_x_col], frame[new_y_col] = zip(*frame[shape_col].apply(lambda x: (x.centroid[0], x.centroid[1])))
    return frame

def reclass_raster_criteria(raster_name, frame, criteria, remap_val=None, 
                            criteria_fail_val=None, raster_val_field='Value',
                            **kwargs):
    '''Reclasses a raster based on supplied criteria, returns resulting raster
        raster_name: str, of raster to be reclassed
        frame: pd.Dataframe, criteria appies to this frame
        criteria: str, is sent into df.query(criteria)
        remap_val: int|float|str, if supplied, all values gets mapped to this 
                value, else retains original value
        criteria_fail_val: int|float|str, if supplied, all values failing crit.
                        gets assigned this value
        missing_values: str, DATA (vals not in resulting remap retains original values) 
                    or NODATA (default, unspecified vals become null)'''
    
    
    meet_crit = frame.query(criteria)
    
    if remap_val is not None:
        remap = ';'.join([f'{v} {remap_val}' for v in meet_crit[raster_val_field]])
    else:
        remap = ';'.join([f'{v} {v}' for v in meet_crit])
        
    if criteria_fail_val is not None:
        not_meet_criteria = frame[~frame.index.isin(meet_crit.index)]
        remap += ';' + ';'.join([f'{v} {criteria_fail_val}' for v in not_meet_criteria[raster_val_field]])
    
    print(f'performes reclassify with remap:\n{remap}')
    return arcpy.sa.Reclassify(raster_name, 
                          "Value",
                          remap,
                          **kwargs)
     
def set_value_field(target_raster, frame, current_val_field, new_val_field, raster_val_field='Value'):
    '''Sets a non-value field as the new value field for raster using dataframe
    target_raster: str
    frame: pd.Dataframe
    current_val_field: str
    new_val_field: str
    raster_val_field: str
    '''
    remap = ';'.join(
        (frame[current_val_field].astype(str) + 
        ' ' +
        frame[new_val_field].astype(str)).to_list())
    
    return arcpy.sa.Reclassify(target_raster, 
                    raster_val_field,
                    remap)
    