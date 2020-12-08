import numpy as np
import xarray as xr
import glob

from src.util.shapefile_masks import add_shape_coord_from_data_array

directory_hazard = '/Users/zeliestalhanske/Documents/ch2018_sample'
kanton = 'Zürich'

nc_max_temp = glob.glob(directory_hazard + '/tasmax/' + '*SMHI-RCA_NORESM_EUR44*')[0]
tasmax = xr.open_dataset(nc_max_temp).sel(time=slice(''.join([str(2045), '-01-01']),
                                                     ''.join([str(2055), '-01-01'])))
shp_dir = '../../input_data/shapefiles/KANTONS_projected_epsg4326/'

tasmax = add_shape_coord_from_data_array(tasmax, shp_dir, kanton)
tasmax = tasmax.where(tasmax[kanton] == 0, other=np.nan)

tasmax = tasmax.where(tasmax['tasmax'] > 21.5).dropna(dim='time', how='all')

tasmax.to_netcdf('../../input_data/ch2018_sample/tasmax/CH2018_zurich_tasmax_SMHI-RCA_NORESM_EUR44_RCP85_QMgrid_2045-2055.nc')
