import sys
import pandas as pd
from climada.entity import Exposures
import time

from src.write_entities.define_hazard import call_hazard_productivity

sys.path.append('../../')
from src.impact_calculation.impact_heat import ImpactsHeatMortality, ImpactsHeatProductivity
from src.write_entities.define_exposures import call_exposures_switzerland_mortality, \
    call_exposures_switzerland_productivity

startTime = time.time()

directory_output = '../../output/mortality_results/'  # where to save to output
#directory_hazard = '/Users/zeliestalhanske/Desktop/Master/Thesis/Hazard/ch20182/'  # test data
directory_hazard = '../../input_data/ch2018_sample/'  # test data
n_mc = 4
years = [2050]
scenarios = ['RCP85']
nyears_hazards = 6

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
    exposures[category] = exposures[category][exposures[category]['canton'] == 'Zürich']
    exposures[category] = Exposures(exposures[category])
    exposures[category].check()

impacts_productivity = ImpactsHeatProductivity(scenarios, years, n_mc)
impacts_productivity.impacts_years_scenarios(exposures, directory_hazard, nyears_hazards)

#with open(''.join([directory_output, 'impact_', str(n_mc), 'mc', '.pickle']), 'wb') as handle:
#    pickle.dump(impacts_mortality, handle, protocol=pickle.HIGHEST_PROTOCOL)

executionTime = (time.time() - startTime)

print('Execution time in seconds: ' + str(executionTime))