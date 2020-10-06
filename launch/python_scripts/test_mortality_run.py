import pickle
import sys
sys.path.append('../../')
from src.impact_calculation.impact_monte_carlo_parallel import impact_monte_carlo

def convert(string):  # function that converts 'lists' from the bash input (strings) to python lists
    li = list(string.split(","))
    return li


directory_output = '../../output/impact_ch/'  # where to save to output
directory_hazard = '../../input_data/ch2018_sample/' # test data

n_mc = 1

# check the third input, which determines if the input should be calculated for Switzerland,
# all cantons indepentently or for one specific canton:
kantons = ['Zürich'] # the None is put into a list, as we further loop through the cantons given

# get fourth input, the years for which to compute the impact
years_list = [2020]

# get fifth input, the scenarios for which to compute the impact
scenarios = ['RCP85']

# check if any age groups were given, or if the impact for all age groups should be computed

age_group = None
groups_str = 'all_age_groups' # string to name the file later on

# determine if the median damage matrix should be saved as output
save_median_mat = False

# in this base model run, all uncertainties are taken into account.
# This is not the case in the sensibility testing code where all are taken one by one.
uncertainty_variables_list = ['None']
uncertainty = 'none'

for kanton in kantons:  # loop through given kantons, one file per element in the kantons loop will be produced.
    # If cantons only contains None, only one file corresponding to all of Switzerland is produced,
    # otherwise one per canton will be written.

    if kanton is None:
        kanton_name = 'CH'
    else:
        kanton_name = kanton

    # compute the impact. impact[0] is the loss for each category and Monte Carlo run, impact[0] is the impact matrix
    # for each category and Monte Carlo run

    IMPACT = impact_monte_carlo(directory_hazard, scenarios, years_list, n_mc,
                                uncertainty_variables_list=uncertainty_variables_list, kanton=kanton,
                                age_group=age_group, save_median_mat=save_median_mat)

    with open(''.join([directory_output, 'loss_', groups_str, '_', str(n_mc), 'mc_',
                       uncertainty, '_', kanton_name, '.pickle']), 'wb') as handle:
        pickle.dump(IMPACT[0], handle, protocol=pickle.HIGHEST_PROTOCOL)
    if save_median_mat:
        with open(''.join([directory_output, 'matrix_',
                           groups_str, '_', str(n_mc), 'mc_', uncertainty, '_', kanton_name,
                           '.pickle']) , 'wb') as handle:
            pickle.dump(IMPACT[1], handle, protocol=pickle.HIGHEST_PROTOCOL)