import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from climada.entity import ImpactFunc, ImpactFuncSet

# define a truncated normal distribution, to not have extreme outliers
def truncated_normal(mean, stddev, minval, maxval):
    return np.clip(np.random.normal(mean, stddev), minval, maxval) 

#  define the function to fit the points:
def polynomial(x, a, b, c, d):
    return a*x**3 + b*x**2 + c*x + d


# function to get a random impact function:
def impact_functions_random(file):
    """get curve for the impact function:

                       Parameters:
                           file (str): directory to file with the data
                           category (str): age category
                           error (bool): rather to give best estimate or to add a random variation. Default: True
                           
                       Returns: curve for the impact function

                             """

    data = file[['T', 'best_estimate', '95CI_low', '95CI_high']]  # get best estimated from the csv files
    #data = data.dropna()  # get rid of missing values
    xdata = data['T']

    #ydata = np.random.uniform(low=data['95CI_low'], high=data['95CI_high'])
    #ydata = np.clip(np.random.normal(loc=data['best_estimate'], scale=1), data['95CI_low'], data['95CI_high'])
    ydata = truncated_normal(data['best_estimate'], (data['95CI_high']-data['95CI_low']/3.92), data['95CI_low'], data['95CI_high'])

    # set RR=1 up to T=22°C:
    ydata = np.append(ydata, [1, 1])
    xdata = np.append(xdata, [21, 22])

    p0 = [max(ydata), np.median(xdata), 1, min(ydata)]  # this is an mandatory initial guess to fit the curve

    fit, pcov = curve_fit(polynomial, xdata, ydata, p0, method='dogbox')  # get curve
    return fit


# In[8]:


def call_impact_functions(with_without_error=True):
    """get curve for the impact function:

                        Parameters:
                            with_without_error (bool): rather to give best estimate or to add a random variation. Default: True
                        
                        Returns: climada impact functions set

                              """

    # get the data from the Excel files:
    directory_if = '../../input_data/impact_functions/'

    file_under75 = pd.read_csv(''.join([directory_if, 'impact_under75.csv']))
    function_under75 = impact_functions_random(file_under75)

    file_over75 = pd.read_csv(''.join([directory_if, 'impact_over75.csv']))
    function_over75 = impact_functions_random(file_over75)

    # make impact function set:

    if_heat_set = ImpactFuncSet()
    x = np.linspace(20, 40, num=30)

    if_heat1 = ImpactFunc()
    if_heat1.haz_type = 'heat'
    if_heat1.id = 1
    if_heat1.name = 'Under 75 years'
    if_heat1.intensity_unit = 'Degrees C'
    if_heat1.intensity = x
    if_heat1.mdd = (polynomial(x, *function_under75))
    if_heat1.mdd[if_heat1.mdd < 1] = 1  # to avoid having values under RR=1
    if_heat1.paa = np.linspace(1, 1, num=30)
    if_heat_set.append(if_heat1)

    if_heat2 = ImpactFunc()
    if_heat2.haz_type = 'heat'
    if_heat2.id = 2
    if_heat2.name = 'Over 75 years'
    if_heat2.intensity_unit = 'Degrees C'
    if_heat2.intensity = x
    if_heat2.mdd = (polynomial(x, *function_over75))
    if_heat2.mdd[if_heat2.mdd < 1] = 1
    if_heat2.paa = np.linspace(1, 1, num=30)
    if_heat_set.append(if_heat2)

    return if_heat_set
