import pickle
from ast import literal_eval
import sys

from climada.entity import Exposures
sys.path.append('../../')

from src.impact_calculation.impact_heat import ImpactsHeatProductivity


def convert(string):  # function that converts 'lists' from the bash input (strings) to python lists
    li = list(string.split(","))
    return li


directory_output = '../../output/productivity_results/'  # where to save to output
directory_hazard = sys.argv[1]  # first input from the bash script, which is the directory to the temperature files.

n_mc = literal_eval(sys.argv[2])  # number of Monte Carlo runs

# get fourth input, the years for which to compute the impact
years = [int(i) for i in convert(sys.argv[3])]

# get fifth input, the scenarios for which to compute the impact
scenarios = convert(sys.argv[4])

# determine if the median damage matrix should be saved as output
if sys.argv[5] == '0':
    save_median_mat = False
else:
    save_median_mat = True

#check if the sensibility analysis should be performed
if sys.argv[6] == '1':
    sensibility_analysis = True

nyears_hazards = 6 #number of years arround the given year to be considered

directory_if = '../../input_data/impact_functions/'
directory_exposures = '../../input_data/exposures/'

file_info = ''.join([directory_exposures, 'age_categories.csv'])
file_locations = ''.join([directory_exposures, 'STATPOP2018.csv'])
shp_dir = '../../input_data/shapefiles/KANTONS_projected_epsg4326/'


#call_exposures_switzerland_productivity(file_info, file_locations, shp_dir, save=True)
exposures = {}
for code, category in {'IL': 'inside low physical activity', 'IM': 'inside moderate physical activity',
                       'OM': 'outside moderate physical activity', 'OH': 'outside high physical activity'}.items():
    exposures_file = ''.join([directory_exposures, 'exposures_productivity_ch_', code, '.h5'])
    exposures[category] = Exposures()
    exposures[category].read_hdf5(exposures_file)
    exposures[category] = Exposures(exposures[category])
    exposures[category].check()

if sensibility_analysis:

    uncertainty_variables = ['hourly_temperature', 'sun_or_shadow', 't_to_wbgt', 'temp_in', 'impactfunction'
        , 'simulations', 'years']
    impacts_productivity_sensibility = {}
    for variable in uncertainty_variables:
        impacts_productivity = ImpactsHeatProductivity(scenarios, years, n_mc)
        impacts_productivity_sensibility[variable] = \
            impacts_productivity.impacts_years_scenarios(exposures, directory_hazard, nyears_hazards,
                                                     save_median_mat=save_median_mat, uncertainty_variable=variable)
    with open(''.join([directory_output, 'sensitivity_', str(n_mc), 'mc', '.pickle']), 'wb') as handle:
        pickle.dump(impacts_productivity, handle, protocol=pickle.HIGHEST_PROTOCOL)
else:
    impacts_productivity = ImpactsHeatProductivity(scenarios, years, n_mc)
    impacts_productivity.impacts_years_scenarios(exposures, directory_hazard, nyears_hazards, save_median_mat=save_median_mat)


    with open(''.join([directory_output, 'impact_', str(n_mc), 'mc', '.pickle']), 'wb') as handle:
        pickle.dump(impacts_productivity, handle, protocol=pickle.HIGHEST_PROTOCOL)
