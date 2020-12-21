import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from climada.entity import ImpactFunc, ImpactFuncSet

# define a truncated normal distribution, to not have extreme outliers
def truncated_normal(mean, stddev, minval, maxval):
    return np.clip(np.random.normal(mean, stddev), minval, maxval) 


def sigmoid(x, L, x0, k, b):
    y = L / (1 + np.exp(-k * (x - x0))) + b
    return (y)


#  define the function to fit the points:
def polynomial(x, a, b, c, d):
    return a*x**3 + b*x**2 + c*x + d


# function to get a random impact function:
def sample_impact_functions_mortality(file):
    """get curve for the impact function:

                       Parameters:
                           file (str): directory to file with the data
                           category (str): age category
                           error (bool): rather to give best estimate or to add a random variation. Default: True
                           
                       Returns: curve for the impact function

                             """

    data = file[['T', 'best_estimate', '95CI_low', '95CI_high']]  # get best estimated from the csv files
    xdata = data['T']

    ydata = np.clip(np.random.normal(loc=data['best_estimate'], scale=1), data['95CI_low']*0.9, data['95CI_high']*1.1)

    # set RR=1 up to T=22°C:
    ydata = np.append(ydata, [1, 1])
    xdata = np.append(xdata, [21, 22])

    p0 = [max(ydata), np.median(xdata), 1, min(ydata)]  # this is an mandatory initial guess to fit the curve

    fit, pcov = curve_fit(polynomial, xdata, ydata, p0, method='dogbox')  # get curve
    return fit


# In[8]:


def call_impact_functions_mortality():
    """get curve for the impact function:

                        Parameters:
                            with_without_error (bool): rather to give best estimate or to add a random variation. Default: True
                        
                        Returns: climada impact functions set

                              """

    # get the data from the Excel files:
    directory_if = '../../input_data/impact_functions/'

    file_under75 = pd.read_csv(''.join([directory_if, 'impact_under75.csv']))
    function_under75 = sample_impact_functions_mortality(file_under75)

    file_over75 = pd.read_csv(''.join([directory_if, 'impact_over75.csv']))
    function_over75 = sample_impact_functions_mortality(file_over75)

    # make impact function set:

    if_heat_set = ImpactFuncSet()
    x = np.linspace(20, 40, num=30)

    if_heat1 = ImpactFunc()
    if_heat1.haz_type = 'heat'
    if_heat1.id = 1
    if_heat1.name = 'u75'
    if_heat1.intensity_unit = 'Degrees C'
    if_heat1.intensity = x
    if_heat1.mdd = (polynomial(x, *function_under75))
    if_heat1.mdd[if_heat1.mdd < 1] = 1  # to avoid having values under RR=1
    if_heat1.paa = np.linspace(1, 1, num=30)
    if_heat_set.append(if_heat1)

    if_heat2 = ImpactFunc()
    if_heat2.haz_type = 'heat'
    if_heat2.id = 2
    if_heat2.name = 'o75'
    if_heat2.intensity_unit = 'Degrees C'
    if_heat2.intensity = x
    if_heat2.mdd = (polynomial(x, *function_over75))
    if_heat2.mdd[if_heat2.mdd < 1] = 1
    if_heat2.paa = np.linspace(1, 1, num=30)
    if_heat_set.append(if_heat2)

    return if_heat_set


def sample_impact_function_productivity(file, intensity, error=True):
    """get curve for the impact function:

                       Parameters:

                           file (str): directory to file of the impact studies
                           intensity (str): intensity of the work
                           error (bool): rather to give best estimate or to add a random variation. Default: True
                       Returns: curve for the impact function

                             """

    data = file[['wbgt', 'best estimate']]  # get best estimated from the csv files
    data = data.dropna()  # get rid of missing values
    xdata = data['wbgt']

    if error:
        if intensity == 'high':
            mult = truncated_normal(1, 0.3, 0.2, 1.8)
        elif intensity == 'moderate':
            mult = truncated_normal(1, 0.3, 0.2, 1.8)
        else:
            mult = truncated_normal(1, 0.3, 0.2, 1.8)
    else:
        mult = 1

    ydata = data['best estimate'] * mult  # multiply the points by the random factor

    # set 100% loss from 60 degrees on and 0% up to 22:
    ydata = np.append(ydata, [100, 100, 100])
    ydata = np.append(ydata, [0, 0, 0])
    xdata = np.append(xdata, [60, 61, 62])
    xdata = np.append(xdata, [20, 21, 22])

    p0 = [max(ydata), np.median(xdata), 1, min(ydata)]  # this is an mandatory initial guess to fit the curve

    fit, pcov = curve_fit(sigmoid, xdata, ydata, p0, method='dogbox')  # get curve
    return fit


# In[8]:


def call_impact_functions_productivity(with_without_error):
    """get curve for the impact function:

                        Parameters:

                            with_without_error (bool): rather to give best estimate or to add a random variation. Default: True
                        Returns: climada impact functions set

                              """

    # get the data from the studies:
    directory_if = '../../input_data/impact_functions/'

    file_low = pd.read_csv(''.join([directory_if, 'impact_low.csv']))
    function_low = sample_impact_function_productivity(file_low, 'low', with_without_error)

    file_moderate = pd.read_csv(''.join([directory_if, 'impact_moderate.csv']))
    function_moderate = sample_impact_function_productivity(file_moderate, 'moderate', with_without_error)

    file_high = pd.read_csv(''.join([directory_if, 'impact_high.csv']))
    function_high = sample_impact_function_productivity(file_high, 'high', with_without_error)

    # make impact function set:

    if_heat_set = ImpactFuncSet()
    x = np.linspace(20, 40, num=30)

    if_heat1 = ImpactFunc()
    if_heat1.haz_type = 'heat'
    if_heat1.id = 1
    if_heat1.name = 'low physical activity'
    if_heat1.intensity_unit = 'Degrees C'
    if_heat1.intensity = x
    if_heat1.mdd = (sigmoid(x, *function_low)) / 100
    if_heat1.mdd[if_heat1.mdd < 0] = 0  # to avoid having negative values
    if_heat1.mdd[if_heat1.mdd > 100] = 100  # to avoid having values over a 100
    if_heat1.paa = np.linspace(1, 1, num=30)
    if_heat_set.append(if_heat1)

    if_heat2 = ImpactFunc()
    if_heat2.haz_type = 'heat'
    if_heat2.id = 2
    if_heat2.name = 'medium physical activity'
    if_heat2.intensity_unit = 'Degrees C'
    if_heat2.intensity = x
    if_heat2.mdd = (sigmoid(x, *function_moderate)) / 100
    if_heat2.mdd[if_heat2.mdd < 0] = 0
    if_heat2.mdd[if_heat2.mdd > 100] = 100
    if_heat2.paa = np.linspace(1, 1, num=30)
    if_heat_set.append(if_heat2)

    if_heat3 = ImpactFunc()
    if_heat3.haz_type = 'heat'
    if_heat3.id = 3
    if_heat3.name = 'high physical activity'
    if_heat3.intensity_unit = 'Degrees C'
    if_heat3.intensity = x
    if_heat3.mdd = (sigmoid(x, *function_high)) / 100
    if_heat3.mdd[if_heat3.mdd < 0] = 0
    if_heat3.mdd[if_heat3.mdd > 100] = 100
    if_heat3.paa = np.linspace(1, 1, num=30)
    if_heat_set.append(if_heat3)

    return if_heat_set