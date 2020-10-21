import numpy as np
import xarray as xr
import random
import glob
from pandas import Timestamp
from scipy import sparse

from climada.hazard import Hazard
np.warnings.filterwarnings('ignore')


# In[ ]:


def call_hazard(directory_hazard, scenario, year, nyears_hazards):
    """Compute heat hazard for the CH2018 data, considered as any day where the T_max is higher than 22 degrees celsius

            Parameters:
                directory_hazard (str): directory to a folder containing one tasmax folder with all the data files
                scenario (str): scenario for which to compute the hazards
                year(str): year for which to compute the hazards
                uncertainty_variable (str): variable for which to consider the uncertainty. Default: 'all'
                region (str or None): Name of canton. Default: None (all of Switzerland)

            Returns:
                hazards(dict): dictionary containing the hazard heat
                  """
    ny = random.randint(-(nyears_hazards/2), nyears_hazards/2)  # to be added to the year, so that any year in the +5 to -5 range can be picked

    nc_max_temp = np.random.choice(list(set(glob.glob(''.join([directory_hazard, '/tasmax/', '*', scenario, '*'])))))
    tasmax = xr.open_dataset(nc_max_temp).sel(time=slice(''.join([str(year + ny), '-01-01']),
                                                         ''.join([str(year + 1 + ny), '-01-01'])))  # open as xr dataset
    if not len(tasmax.tasmax):
        tasmax = xr.open_dataset(nc_max_temp).sel(time=slice(''.join([str(year), '-01-01']),
                                                             ''.join([str(year + 1), '-01-01'])))

    # replace all values where the maximum
    # temperature does not reach 22 degrees by nas in TASMAX and drop time steps that only have NAs
    # for the entire area: (21.5 because of rounding that happens later)
    tasmax = tasmax.where(tasmax['tasmax'] > 21.5).dropna(dim='time', how='all')

    nlats = len(tasmax.lat)  # number of latitudes
    nlons = len(tasmax.lon)  # number of longitudes

    number_days = len(tasmax.time)

    dates = [Timestamp(tasmax.time.values[t]).toordinal() for t in range(number_days)]

    nevents = len(dates)  # number of events
    events = range(len(dates))  # number of each event

    grid_x, grid_y = np.meshgrid(tasmax.lon.values, tasmax.lat.values)
    heat = Hazard('heat')
    heat.centroids.set_lat_lon(grid_y.flatten(), grid_x.flatten(), crs={'init': 'epsg:4326'})
    heat.units = 'degrees C'
    tasmax.tasmax.values[np.isnan(tasmax.tasmax.values)] = 0.  # replace NAs by 0
    heat.intensity = sparse.csr_matrix(tasmax.tasmax.values.reshape(nevents, nlons * nlats))
    heat.event_id = np.array(events)
    heat.event_name = heat.event_id
    heat.frequency = np.ones(nevents)
    heat.fraction = heat.intensity.copy()
    heat.fraction.data.fill(1)
    heat.date = np.array(dates)
    heat.check()

    tasmax.close()
    del tasmax

    return heat  # return the hazards