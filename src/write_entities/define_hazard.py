import numpy as np
import xarray as xr
import random
import glob
from pandas import Timestamp
from scipy import sparse

from climada.hazard import Hazard

import sys
from src.util.shapefile_masks import add_shape_coord_from_data_array

np.warnings.filterwarnings('ignore')


# In[ ]:


def call_hazard(directory_hazard, scenario, year, uncertainty_variable='all', kanton=None):
    """Compute heat hazard for the CH2018 data, considered as any day where the T_max is higher than 22 degrees celsius

            Parameters:
                directory_hazard (str): directory to a folder containing one tasmax folder with all the data files
                scenario (str): scenario for which to compute the hazards
                year(str): year for which to compute the hazards
                uncertainty_variable (str): variable for which to consider the uncertainty. Default: 'all'
                kanton (str or None): Name of canton. Default: None (all of Switzerland)

            Returns:
                hazards(dict): dictionary containing the hazard heat
                  """
    if uncertainty_variable == 'all' or uncertainty_variable == 'years':
        ny = random.randint(-3, 3)  # to be added to the year, so that any year in the +5 to -5 range can be picked
    else:  # if we are testing the sensitivity to the change in variables, we always want to be taking
        # the same year and therefore add 0
        ny = 0

    if uncertainty_variable == 'simulations' or uncertainty_variable == 'all':
        nc_max_temp = np.random.choice(list(set(glob.glob(''.join([directory_hazard, '/tasmax/', '*', scenario, '*'])))))
    else:
        nc_max_temp = glob.glob(directory_hazard + '/tasmax/' + '*SMHI-RCA_NORESM_EUR44*')[0]

    tasmax = xr.open_dataset(nc_max_temp).sel(time=slice(''.join([str(year + ny), '-01-01']),
                                                         ''.join([str(year + 1 + ny), '-01-01'])))  # open as xr dataset

    if kanton:  # if a canton is specified, we mask the values outside of this canton using a day_startapefile
        shp_dir = 'input_data/shapefiles/KANTONS_projected_epsg4326/' \
                  'swissBOUNDARIES3D_1_3_TLM_KANTONSGEBIET_epsg4326.shp'

        tasmax = add_shape_coord_from_data_array(tasmax, shp_dir, kanton)
        tasmax = tasmax.where(tasmax[kanton] == 0, other=np.nan)

    # replace all values where the maximum
    # temperature does not reach 22 degrees by nas in TASMAX and drop time steps that only have NAs
    # for the entire area: (21.5 because of rounding that happens later)
    tasmax = tasmax.where(tasmax['tasmax'] > 21.5).dropna(dim='time', how='all')

    nlats = len(tasmax.lat)  # number of latitudes
    nlons = len(tasmax.lon)  # number of longitudes

    # variables needed for the model

    number_days = len(tasmax.time)
    temp = np.zeros([number_days, nlats, nlons]) # array where we save the data for the heat hazard
    day = 0  # start at day 0
    dates = np.zeros(number_days)

    # create an array with the maximum temperature of the day

    for t in range(number_days):  # loop over the number of days in a year

        dates[t] = Timestamp(tasmax.time.values[day]).toordinal()
        temp[t,:,:] = (tasmax.tasmax.values[day])
            
        day = day + 1

    nevents = len(temp)  # number of events
    events = range(len(temp))  # number of each event
    event_dates = dates
    temp_data = temp
    hazard_types = 'heat'

    grid_x, grid_y = np.meshgrid(tasmax.lon.values, tasmax.lat.values)
    heat = Hazard('heat')
    heat.centroids.set_lat_lon(grid_y.flatten(), grid_x.flatten(), crs={'init': 'epsg:4326'})
    heat.units = 'degrees C'
    heat_data = temp_data
    heat_data[np.isnan(heat_data)] = 0.  # replace NAs by 0
    heat.intensity = sparse.csr_matrix(heat_data.reshape(nevents, nlons * nlats))
    heat.event_id = np.array(events)
    heat.event_name = heat.event_id
    heat.frequency = np.ones(nevents)
    heat.fraction = heat.intensity.copy()
    heat.fraction.data.fill(1)
    heat.date = event_dates
    heat.check()

    tasmax.close()
    del tasmax
    del temp

    return heat  # return the hazards