import numpy as np
import xarray as xr
import random
import glob
from pandas import Timestamp
from scipy import sparse
import math
from climada.hazard import Hazard

t_to_wbgt = np.poly1d(
    [0.64879697, 4.22085354])  # fit found by analyzing station data from T to WBGT in the day_startadow
t_to_wbgt_sun = np.poly1d([0.61111305, 6.64870352])  # same in the sun
sd_mean_sun = 1.686897665324121  # standards deviation
sd_mean = 1.2956438427881554  # standard deviation
Tin_est = np.array(
    [0.18797175, 0.27614082, -0.05381464, 0.67076506])  # parameters for the inside temperature fitting function


def t_diff_fit(x, a, b, c, phi):  # function fitting the difference btw inside and outside temperature
    return a * np.sin(b * x + phi) + c


# In[ ]:


def call_hazard_mortality(directory_hazard, scenario, year, nyears_hazards):
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


def call_hazard_productivity(directory_hazard, scenario, year, nyears_hazard=6, uncertainty_variable='all', sun_protection=False,
                working_hours=[8, 12, 13, 17], only_outside=False):
    """Compute heat inside and heat outside hazards for the ch2018 data, considered as any hour where the WBGT is higher
        than 22 degrees celsius

            Parameters:
                directory_hazard (str): directory to a folder containing one tasmax and one tasmin folder with all the
                                        data files
                scenario (str): scenario for which to compute the hazards
                year(str): year for which to compute the hazards
                uncertainty_variable (str): variable for which to consider the uncertainty. Default: 'all'
                kanton (str or None): Name of canton. Default: None (all of Switzerland)
                sun_protection (bool): rather to consider the adaptation measure sun_protection. Default: False
                working_hours (list): hours where people are working. list with the first number being when they
                        start in the day, the second when they start their midday break,
                        third when they start in the afternoon and last when they finished in the evening
                        Default:[8,12,13,17]
                only_outside (bool): rather damage occurs only outside (buildings are well insulated from heat)
                        Default: False

            Returns:
                hazards(dict): dictionary containing the hazard 'heat outside' and 'heat inside'
                  """

    if not sun_protection:
        ones_zero_random = np.random.choice([0, 1], size=(
            8,))  # randomly pick the number of hours where people working outside are in the sun
    else:
        ones_zero_random = np.ones(8, dtype=int)

    rmse_hourly_t = 0.028530743129040116  # Root mean square error from the hourly T transformation
    error_hourly_t = np.random.normal(0, rmse_hourly_t)  # distribution for the transformation from
    # min T and max T to hourly T
    error_temp_in = np.random.triangular(0, 1, 1.2)  # distribution for the inside temperature estimation.
    error_wbgt = np.random.normal(0, 2 / 3.92)  # error for the transformation between T and WBGT

    if uncertainty_variable == 'all' or uncertainty_variable == 'years':
        ny = random.randint(-nyears_hazard/2, nyears_hazard/2)  # to be added to the year, so that any year in the +5 to -5 range can be picked
    else:  # if we are testing the sensitivity to the change in variables, we always want to be taking
        # the same year and therefore add 0
        ny = 0

    if uncertainty_variable == 'simulations' or uncertainty_variable == 'all':
        nc_max_temp = np.random.choice(list(set(glob.glob(''.join([directory_hazard, '/tasmax/', '*', scenario, '*'])))))
    else:
        nc_max_temp = glob.glob(directory_hazard + '/tasmax/' + '*SMHI-RCA_NORESM_EUR44*')[0]

    nc_min_temp = nc_max_temp.replace('max', 'min')  # take equivalent tasmin file
    tasmax = xr.open_dataset(nc_max_temp).sel(time=slice(''.join([str(year + ny), '-01-01']),
                                                         ''.join([str(year + 1 + ny), '-01-01'])))  # open as xr dataset
    tasmin = xr.open_dataset(nc_min_temp).sel(time=slice(''.join([str(year + ny), '-01-01']),
                                                         ''.join([str(year + 1 + ny), '-01-01'])))

    # replace all values where the maximum
    # temperature does not reach 22 degrees by nas in both TASMIN and TASMAX and drop time steps that only have NAs
    # for the entire area:
    tasmin = tasmin.where(tasmax['tasmax'] > 22).dropna(dim='time', how='all')
    tasmax = tasmax.where(tasmax['tasmax'] > 22).dropna(dim='time', how='all')

    nlats = len(tasmax.lat)  # number of latitudes
    nlons = len(tasmax.lon)  # number of longitudes
    day_start = working_hours[0]  # beginning of working day
    day_end = working_hours[3]  # End of working day
    daily_working_hours = day_end - day_start  # length of working day

    # variables needed for the model (h_max is the hour at which the temperature is highest, h_min lowest)

    number_days = len(tasmax.time)

    n_hours = number_days * daily_working_hours
    h_max = 15  # set 15 as the warmest hour of the day
    h_min = 5  # set 5 as the coldest hour
    pi = math.pi
    cos = math.cos
    temp = np.zeros([n_hours, nlats, nlons])
    wbgt_out = np.zeros([n_hours, nlats, nlons])  # array where we save the data for the heat outside hazard
    wbgt_in = np.zeros([n_hours, nlats, nlons])  # array where we save the data for the heat inside hazard
    temp_in = np.zeros([n_hours, nlats, nlons])
    day = 0  # start at day 0
    h = day_start + 1  # the first temperature that we want to consider is at the end of the hour 8 on the first day
    # where the temperature reached 22 degress
    week_day = day  # also start at 0
    dates = np.zeros(n_hours)

    # create an array with the maximum, the minimum, the average and the amplitude of the day

    for t in range(n_hours):  # loop over the number of working hours in a year, everyone is considered to have the same

        if week_day < 6:  # ignores 2 out of 7 days because it is the weekend, do not really correspond to real days
            # in the week

            dates[t] = Timestamp(tasmax.time.values[day]).toordinal()

            if day < (len(tasmax.tasmax.values) - 1):  # if day is not the last day of the dataset
                next_day = day + 1  # next days, needed to calculate the hourly temperature.
            else:
                next_day = day  # when the last day of the year is reached, we just consider that the next day
                # has the same temperature curve as itself

            if h <= working_hours[1] or h > working_hours[2]:  # continue if not the midday break

                # model to give the hourly temperature based on the maximum and minimum temperature of this day,
                # as well as the min temperature of the next. Here as we removed some data, the following or next day
                # may not always be the same

                if h_min <= h < h_max:  # between 5 and 15, the last known temperature is the minimum temperature of
                    # the day at 5 and the next is the maximum which is considered to happens at 15
                    temp[t, :, :] = ((tasmax.tasmax.values[day] + tasmin.tasmin.values[day]) / 2 -
                                     (tasmax.tasmax.values[day] - tasmin.tasmin.values[day])
                                     / 2 * cos(pi * (h - h_min) / (h_max - h_min)))

                if h_max <= h:  # after 15h, the next known temperature is the one of the next day
                    temp[t, :, :] = (tasmin.tasmin.values[next_day] + tasmax.tasmax.values[next_day]) \
                                    / 2 - (tasmin.tasmin.values[next_day] - tasmax.tasmax.values[day]) \
                                    / 2 * cos(pi * (h - h_max) / (h_min - h_max))
                # here we would have to add conditions if we wanted to have the temperature before 5:00 but it is not
                # needed in hour model

                if uncertainty_variable == 'hourly_temperature' or uncertainty_variable == 'all':
                    temp[t, :, :] = temp[t, :, :] + error_hourly_t  # if we consider the error,
                    # the temperature is the temperature as calculate + the error for the transformation

                # in the case that the wbgt for any of the points on the map is larger then 22,
                # save the temperature transformed to a wbgt

                sun_or_shadow_functions = [t_to_wbgt_sun, t_to_wbgt]  # list of the two possible function for the
                # transformation to WBGT
                sun_or_shadow_sd = [sd_mean_sun, sd_mean]

                if uncertainty_variable == 'sun_or_shadow' or uncertainty_variable == 'all':
                    one_zero = np.random.choice(ones_zero_random)  # randomly chose if people outside are working in
                    # the sun or shadow for the current hour from the distribution set at the beginning of the file
                    sun_or_shadow = sun_or_shadow_functions[one_zero]  # then take the corresponding function
                    sd = sun_or_shadow_sd[one_zero]

                else:
                    sun_or_shadow = sun_or_shadow_functions[1]  # if we do not consider this uncertainty, just fix
                    # that people are protected from the sun at all times
                    sd = sun_or_shadow_sd[1]

                if uncertainty_variable == 't_to_wbgt' or uncertainty_variable == 'all':  # uncertainty from the
                    # transformation to wbgt
                    wbgt_out[t, :, :] = np.random.normal(sun_or_shadow(temp[t, :, :]), sd) + error_wbgt
                else:
                    wbgt_out[t, :, :] = np.random.normal(sun_or_shadow(temp[t, :, :]), sd)

                if not only_outside:  # only_outside is set when we have the adaptation measure 'efficient buildings'
                    # meaning that there is only impacts outside

                    if uncertainty_variable == 'temp_in' or uncertainty_variable == 'all':

                        temp_in[t, :, :] = temp[t, :, :] * (1 + (np.array(t_diff_fit(h, *Tin_est))) * error_temp_in)
                        # transform to inside temperature to make the wbgt>22 test for inside events

                    else:  # without considering the uncertainty
                        temp_in[t, :, :] = temp[t, :, :] * (1 + np.array(t_diff_fit(h, *Tin_est)))

                        # transformation to wbgt for the inside temperature:

                    if uncertainty_variable == 't_to_wbgt' or uncertainty_variable == 'all':
                        wbgt_in[t, :, :] = (np.random.normal(t_to_wbgt(temp_in[t, :, :]), sd_mean)) + error_wbgt

                    else:  # without uncertainty
                        wbgt_in[t, :, :] = (np.random.normal(t_to_wbgt(temp_in[t, :, :]), sd_mean))

            h = h + 1  # add +1 to the hour
            if h == day_end + 1:  # if this is the end of the day add 1 to day and go back to hour=1
                h = day_start + 1  # go back to the hour where the day starts
                day = day + 1
                week_day = week_day + 1
                if week_day == 8:  # if it is the end of the week, go back to the start
                    week_day = 0

        # again, we get rid this time of the hours where the wbgt is lower than 22 everywhere:
        hours_in = np.zeros(len(wbgt_in), dtype=bool)
        hours_out = np.zeros(len(wbgt_out), dtype=bool)

        for i_ in range(len(wbgt_in)):
            hours_out[i_] = np.any(wbgt_out[i_, :, :] > 22)
            hours_in[i_] = np.any(wbgt_in[i_, :, :] > 22)

        hours_in[0] = True
        hours_out[0] = True  # I here set the first hour as being a hazard, whatever the real wbgt. this is because it
        # happens maybe once in a 1000 times that there are 0 hazards inside, which further leads to an error and to the
        # model to fail

        wbgt_out = wbgt_out[hours_out == True]
        wbgt_in = wbgt_in[hours_in == True]
        dates_out = dates[hours_out == True].astype('int')
        dates_in = dates[hours_in == True].astype('int')

        nevents = [len(wbgt_out), len(wbgt_in)]  # number of events inside and outside
        events = [range(len(wbgt_out)), range(len(wbgt_in))]  # number of each event
        event_dates = [dates_out, dates_in]
        wbgt_data = [wbgt_out, wbgt_in]
        hazard_types = ['heat outside', 'heat inside']

        hazards = {}

        for w_ in range(len(wbgt_data)):  # write down the events in Hazard class

            grid_x, grid_y = np.meshgrid(tasmax.lon.values, tasmax.lat.values)
            heat = Hazard('heat')
            heat.centroids.set_lat_lon(grid_y.flatten(), grid_x.flatten(), crs={'init': 'epsg:4326'})
            heat.units = 'degrees c'
            heat_data = wbgt_data[w_]
            heat_data[np.isnan(heat_data)] = 0.  # replace NAs by 0
            heat.intensity = sparse.csr_matrix(heat_data.reshape(nevents[w_], nlons * nlats))
            heat.event_id = np.array(events[w_])
            heat.event_name = heat.event_id
            heat.frequency = np.ones(nevents[w_])
            heat.fraction = heat.intensity.copy()
            heat.fraction.data.fill(1)
            heat.date = event_dates[w_]
            hazards[hazard_types[w_]] = heat
            heat.check()

        tasmax.close()
        tasmin.close()
        del tasmax
        del tasmin
        del wbgt_in
        del wbgt_out
        del temp_in
        del temp

        return hazards  # return the hazards
