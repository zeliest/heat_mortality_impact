import pickle
import sys
import pandas as pd
from climada.entity import Exposures
import time
sys.path.append('../../')
from src.impact_calculation.impact_heat import ImpactsHeatMortality
from src.write_entities.define_exposures import call_exposures_switzerland_mortality


startTime = time.time()

directory_output = '../../output/mortality_results/'  # where to save to output
#directory_hazard = '/Users/zeliestalhanske/Desktop/Master/Thesis/Hazard/ch20182/'  # test data
directory_hazard = '../../input_data/ch2018_sample/'  # test data
n_mc = 4
years = [2050]
scenarios = ['RCP85']
nyears_hazards = 6

directory_if = '../../input_data/impact_functions/'
annual_deaths_file = ''.join([directory_if, 'annual_deaths.xlsx'])

directory_exposures = '../../input_data/exposures/'
file_info = ''.join([directory_exposures, 'age_categories.csv'])
file_locations = ''.join([directory_exposures, 'STATPOP2018.csv'])
shp_dir = '../../input_data/shapefiles/KANTONS_projected_epsg4326/'
file_cantons = ''.join([shp_dir, 'swissBOUNDARIES3D_1_3_TLM_KANTONSGEBIET_epsg4326.shp'])
#exposure = call_exposures_switzerland_mortality(file_info, file_locations, file_cantons, annual_deaths_file,
#                                              cantonal_average_deaths=False, save=True)
exposures = {}
for code, category in {'O': 'Over 75', 'U': 'Under 75'}.items():
    exposures_file = ''.join([directory_exposures, 'exposures_mortality_ch_', code, '2.h5'])
    exposures[category] = Exposures()
    exposures[category].read_hdf5(exposures_file)
    exposures[category] = exposures[category][exposures[category]['canton'] == 'Zürich']
    exposures[category] = Exposures(exposures[category])
    exposures[category].check()

impacts_mortality = ImpactsHeatMortality(scenarios, years, n_mc)
impacts_mortality.impacts_years_scenarios(exposures, directory_hazard, nyears_hazards)

#with open(''.join([directory_output, 'impact_', str(n_mc), 'mc', '.pickle']), 'wb') as handle:
#    pickle.dump(impacts_mortality, handle, protocol=pickle.HIGHEST_PROTOCOL)

executionTime = (time.time() - startTime)

print('Execution time in seconds: ' + str(executionTime))