

"""


I did not write most of this code:  these come from those threads
https://stackoverflow.com/questions/51398563/python-mask-netcdf-data-using-shapefile,
https://gist.github.com/shoyer/0eb96fa8ab683ef078eb
Libraries like salem or regionmask could be used for this task but I didn't understand how to

"""

from rasterio import features
from affine import Affine
import pandas as pd
import numpy as np
import xarray as xr
import geopandas as gpd
from shapely.geometry import Point
from pyproj import Proj, transform
from geopandas import GeoDataFrame


def transform_from_latlon(lat, lon):
    """ input 1D array of lat / lon and output an Affine transformation
    """
    lat = np.asarray(lat)
    lon = np.asarray(lon)
    trans = Affine.translation(lon[0], lat[0])
    scale = Affine.scale(lon[1] - lon[0], lat[1] - lat[0])
    return trans * scale


def rasterize(shapes, coords, latitude='latitude', longitude='longitude',
              fill=np.nan, **kwargs):
    """Rasterize a list of (geometry, fill_value) tuples onto the given
    xray coordinates. This only works for 1d latitude and longitude
    arrays.

    usage:
    -----
    1. read shapefile to geopandas.GeoDataFrame
          `states = gpd.read_file(shp_dir+shp_file)`
    2. encode the different shapefiles that capture those lat-lons as different
        numbers i.e. 0.0, 1.0 ... and otherwise np.nan
          `shapes = (zip(states.geometry, range(len(states))))`
    3. Assign this to a new coord in your original xarray.DataArray
          `ds['states'] = rasterize(shapes, ds.coords, longitude='X', latitude='Y')`

    arguments:
    ---------
    : **kwargs (dict): passed to `rasterio.rasterize` function

    attrs:
    -----
    :transform (affine.Affine): how to translate from latlon to ...?
    :raster (numpy.ndarray): use rasterio.features.rasterize fill the values
      outside the .shp file with np.nan
    :spatial_coords (dict): dictionary of {"X":xr.DataArray, "Y":xr.DataArray()}
      with "X", "Y" as keys, and xr.DataArray as values

    returns:
    -------
    :(xr.DataArray): DataArray with `values` of nan for points outside shapefile
      and coords `Y` = latitude, 'X' = longitude.


    """
    transform = transform_from_latlon(coords[latitude], coords[longitude])
    out_shape = (len(coords[latitude]), len(coords[longitude]))
    raster = features.rasterize(shapes, out_shape=out_shape,
                                fill=fill, transform=transform,
                                dtype=float, **kwargs)
    spatial_coords = {latitude: coords[latitude], longitude: coords[longitude]}
    return xr.DataArray(raster, coords=spatial_coords, dims=(latitude, longitude))


def add_shape_coord_from_data_array(xr_da, shp_path, region):
    """ Create a new coord for the xr_da indicating whether or not it 
         is inside the shapefile

        Creates a new coord - "coord_name" which will have integer values
         used to subset xr_da for plotting / analysis/

    """
    # 1. read in shapefile
    shp_gpd = gpd.read_file(shp_path)
    shp_gpd = shp_gpd[shp_gpd['NAME'] == region]

    # 2. create a list of tuples (shapely.geometry, id)
    #    this allows for many different polygons within a .shp file (e.g. States of US)
    shapes = [(shape, n) for n, shape in enumerate(shp_gpd.geometry)]

    # 3. create a new coord in the xr_da which will be set to the id in `shapes`
    xr_da[region] = rasterize(shapes, xr_da.coords,
                              longitude='lon', latitude='lat')

    return xr_da


def vector_shapefile_mask(vector, shp_dir, region, epsg_input, epsg_output): # this is used for the exposures, but is
    # quite slow (not a big problem in the monte carlo as the exposures are called only once)
    regions = gpd.read_file(shp_dir)
    crs = {'init': 'epsg:' + str(epsg_input)}
    geometry = [Point(xy) for xy in zip(vector.longitude, vector.latitude)]
    vector = gpd.GeoDataFrame(vector, crs=crs, geometry=geometry)
    vector = vector.to_crs(crs={'init': 'epsg:' + str(epsg_output)})

    vector = gpd.sjoin(vector, regions[['NAME', 'geometry']], how='left', op='intersects')
    vector = vector[vector['NAME'] == region]
    vector = vector.drop(columns=['NAME', 'index_right', 'longitude', 'latitude'])
    return vector
