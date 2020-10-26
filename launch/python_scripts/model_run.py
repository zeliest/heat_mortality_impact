import pickle
from ast import literal_eval
import sys

from climada.entity import Exposures
sys.path.append('../../')

from src.impact_calculation.impact_heat import ImpactsHeatMortality


def convert(string):  # function that converts 'lists' from the bash input (strings) to python lists
    li = list(string.split(","))
    return li


directory_output = '../../output/mortality_results/'  # where to save to output
directory_hazard = sys.argv[1]  # first input from the bash script, which is the directory to the temperature files.

n_mc = literal_eval(sys.argv[2])  # number of Monte Carlo runs

# get third input, the years for which to compute the impact
years = [int(i) for i in convert(sys.argv[3])]
nyears_hazards = 6
# get fifth input, the scenarios for which to compute the impact
scenarios = convert(sys.argv[4])

# determine if the median damage matrix should be saved as output
if sys.argv[5] == '0':
    save_median_mat = False
else:
    save_median_mat = True

exposures = {}
directory_exposures = '../../input_data/exposures/'
for category in ['O', 'U']:
    exposures_file = ''.join([directory_exposures, 'exposures_mortality_ch_', category, '.h5'])
    exposures[category] = Exposures()
    exposures[category].read_hdf5(exposures_file)

impacts_mortality = ImpactsHeatMortality(scenarios, years, n_mc)
impacts_mortality.impacts_years_scenarios(exposures, directory_hazard, nyears_hazards, save_median_mat=save_median_mat)

with open(''.join([directory_output, 'impact_', str(n_mc), 'mc', '.pickle']), 'wb') as handle:
    pickle.dump(impacts_mortality, handle, protocol=pickle.HIGHEST_PROTOCOL)

