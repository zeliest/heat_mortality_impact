import numpy as np
from climada.engine import Impact
from scipy.sparse import csr_matrix

from src.write_entities.define_if import call_impact_functions
from src.write_entities.define_hazard import call_hazard


# This function calls a random hazard and impact function and takes the given exposures to calculate an impact. The
# positional arguments are the directory for the hazard file, the impact functions directory, the years,
# the variables in which to pick in a distribution, a dictionary of the exposures, their name?. Other default
# variables can be set if needed


def calculate_impact(directory_hazard, scenario, year, exposures, uncertainty_variable='all',
                     kanton=None, age_group=None, save_median_mat=False):
    """compute the impacts once:

                Parameters:
                    directory_hazard (str): directory to a folder containing one tasmax (and one tasmin) folder with all the
                                            data files
                    scenario (str): scenario for which to compute the hazards
                    year(str): year for which to compute the hazards
                    exposures(Exposures): the exposures which stay fixed for all runs
                    uncertainty_variable(str): variable for which to consider the uncertainty. Default: 'all'
                    kanton (str or None): Name of canton. Default: None (all of Switzerland)
                    age_group (str or None): specific age group, as given in the "GIS_Data_code" of the age_categories.csv file. Default: None
                    save_median_mat (bool): rather we save the impact matrix . Default = True

                Returns:
                    Dictionary of impact loss and dictionary of impact matrices if specified
                      """

    impact_dict = {}

    if save_median_mat:
        matrices = {}
        save_mat = True
    else:
        save_mat = False

    hazard = call_hazard(directory_hazard, scenario, year, uncertainty_variable=uncertainty_variable, kanton=kanton)
    ####################################################################################################

    if uncertainty_variable == 'impactfunction' or uncertainty_variable == 'all':
        TF = True
    else:
        TF = False

    if_hw_set = call_impact_functions(TF)

    for e_ in exposures:  # calculate impact for each type of exposure
        impact = Impact()
        impact.calc(exposures[e_], if_hw_set, hazard['heat'], save_mat=save_mat)

        impact_dict[e_] = np.sum(impact.at_event)

        if save_median_mat:
            matrices[e_] = csr_matrix(impact.imp_mat.sum(axis=0))
        # sum all events to get one 1xgridpoints matrix per type of exposures

    del hazard

    if save_median_mat:
        output = [impact_dict, matrices]
    else:
        output = [impact_dict]

    return output