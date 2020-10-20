import numpy as np
import pandas as pd
from climada.entity import Exposures
import geopandas as gpd
from shapely.geometry import Point


def call_exposures_switzerland(file_info, file_locations, shp_cantons, epsg_input, epsg_output):
    exposures = Exposures()
    population_info = pd.read_csv(file_info)  # file containing the information on the categories
    population_loc = pd.read_csv(file_locations)
    categories = np.unique(population_info['Category'])
    exposures['latitude'] = np.concatenate([np.asarray(population_loc['N_KOORD']).flatten() for cat in categories])
    exposures['longitude'] = np.concatenate([np.asarray(population_loc['E_KOORD']).flatten() for cat in categories])
    exposures['if_heat'] = np.concatenate([np.ones(len(population_loc))*(n+1) for n in range(len(categories))])
    exposures['category'] = np.concatenate([[categories[c]
                                             for n in range(len(population_loc))] for c in range(len(categories))])
    categories_code = {cat: population_info['GIS_Data_code'][population_info['Category'] == cat] for cat in categories}
    exposures['value'] = np.concatenate([np.asarray(population_loc[categories_code[cat]]).sum(axis=1) for cat in categories])
    exposures.crs = {'init': ''.join(['epsg:', str(epsg_input)])}  # crs: Coordinate Reference Systems
    exposures.set_geometry_points()
    exposures.to_crs(epsg=epsg_output, inplace=True)
    exposures.fillna(0)
    exposures = add_cantons(exposures, shp_cantons)
    return exposures


def add_average_deaths(exposures, average_deaths):
    average_deaths['daily_deaths'] = average_deaths['annual_deaths']/365
    exposures = pd.merge(exposures, average_deaths[['canton', 'category', 'daily_deaths']], on=['canton', 'category'])
    return exposures


def call_exposures_switzerland_mortality(file_info, file_locations, shp_cantons, annual_deaths, epsg_input=2056, epsg_output=4326,
                                         population_ratio=True, save=False):
    exposures = call_exposures_switzerland(file_info, file_locations, shp_cantons, epsg_input, epsg_output)
    total_population_canton = exposures[['canton', 'category', 'value']]. \
        groupby(['canton', 'category'], as_index=False).sum(numeric_only=True)
    total_population_canton = total_population_canton.rename(columns={'value': 'total_population_canton'})
    exposures = exposures.merge(total_population_canton, on=['canton', 'category'])
    if population_ratio:
        exposures['value'] = exposures['value'].divide(exposures['total_population_canton'])
    exposures = add_average_deaths(exposures, annual_deaths)

    if save:
        for c in exposures['category'].unique():
            exposures_category = Exposures(exposures[exposures['category'] == c])
            exposures_category.check()
            exposures_category.write_hdf5(''.join(['../../input_data/exposures/exposures_mortality_ch_',c,'.h5']))

    return exposures


def add_cantons(vector, shp_dir): # this is used for the exposures, but is
    # quite slow (not a big problem in the monte carlo as the exposures are called only once)
    regions = gpd.read_file(shp_dir)
    vector = gpd.sjoin(vector, regions[['NAME', 'geometry']], how='left', op='intersects')
    return vector.rename(columns={'NAME': 'canton'})