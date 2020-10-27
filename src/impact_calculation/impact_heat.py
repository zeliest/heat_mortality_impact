import pickle

import numpy as np
from climada.engine import Impact
from climada.entity import Exposures
from joblib import Parallel, delayed
from multiprocessing import cpu_count
from climada.entity.exposures.base import INDICATOR_CENTR
from scipy.sparse import vstack, csr_matrix

from src.util.plots import plot_impacts_heat
from src.write_entities.define_hazard import call_hazard
from src.write_entities.define_if import call_impact_functions


class ImpactsHeatProductivity:
    def __init__(self, scenarios, years, n_mc):
        self.scenarios = scenarios
        self.years = years
        self.n_mc = n_mc
        self.agg_impacts_mc = dict()
        self.median_impact_matrices = dict()

    def calculate_impact(self, scenario, year, exposures, directory_hazard, nyears_hazards, crs_exposures=4326):
        hazard = call_hazard(directory_hazard, scenario, year, nyears_hazards)
        if_hw_set = call_impact_functions()
        impact = Impact()
        exposures = Exposures(exposures)
        exposures.crs = {'init': ''.join(['epsg:', str(crs_exposures)])}
        impact.calc(exposures, if_hw_set, hazard, save_mat=True)
        return csr_matrix(impact.imp_mat.sum(axis=0))

    def parallel_impact_calculation(self, scenario, year, exposure, directory_hazard, nyears_hazards, save_median_mat):
        ncores_max = cpu_count()
        impacts = Parallel(n_jobs=ncores_max)(delayed(self.calculate_impact)
                                              (scenario, year, exposure, directory_hazard, nyears_hazards)
                                              for i in range(0, self.n_mc))

        agg_impacts_mc = [np.sum(impacts[n]) for n in range(self.n_mc)]
        if save_median_mat:
            median_impact_matrices = csr_matrix(np.median(vstack(impacts[n]
                                                                 for n in range(self.n_mc)).todense(), axis=0))
            return [agg_impacts_mc, median_impact_matrices]

        return [agg_impacts_mc]

    def impacts_years_scenarios(self, exposures, directory_hazard, nyears_hazards, save_median_mat=True):

        impacts = {scenario: {year: {category: self.parallel_impact_calculation(scenario, year,
                                                                                exposures[category], directory_hazard,
                                                                                nyears_hazards, save_median_mat)
                                     for category in exposures} for year in self.years}
                   for scenario in self.scenarios}
        self.agg_impacts_mc = {scenario: {year: {category: impacts[scenario][year][category][0]
                                                 for category in exposures} for year in self.years} for scenario in
                               self.scenarios}
        if save_median_mat:
            self.median_impact_matrices = {scenario: {year: {category: impacts[scenario][year][category][1]
                                                             for category in exposures} for year in self.years} for
                                           scenario in
                                           self.scenarios}

    # def impact_matrix_to_geotiff(self):

    def median_matrices_as_impacts(self, exposures, unit=None, percentage=False, canton=None):
        impacts_dict = {scenario: {year: {category: self.median_matrix_as_impact
        (self.median_impact_matrices[scenario][year][category],
         exposures[category], unit=unit, percentage=percentage, canton=canton)
                                          for category in exposures} for year in self.years} for scenario in
                        self.scenarios}
        return impacts_dict

    @staticmethod
    def median_matrix_as_impact(impact_matrix, exposures, unit=None, percentage=False, canton=None):
        impact = Impact()
        if canton:
            canton_data = exposures['canton'] == canton
            exposures = exposures[canton_data]
        impact.coord_exp = np.stack([exposures.latitude.values, exposures.longitude.values], axis=1)
        impact.event_id = np.array([1])
        if canton:
            index = [i for i, x in enumerate(canton_data) if x == True]
            impact.imp_mat = impact_matrix[:, index]
        else:
            impact.imp_mat = impact_matrix
        if percentage:
            impact.imp_mat = csr_matrix((csr_matrix(impact_matrix).toarray()[0, :]
                                         / exposures.value.replace(0,
                                                                   1)) * 100)  # put impacts in terms of percentage of exposure
        impact.unit = unit
        return impact

    def calculate_impact_agg_canton(self, canton, exposures):
        impact = self.median_matrices_as_impacts(exposures, canton=canton)
        agg_impact = {scenario: {year: {category: [impact[scenario][year][category].imp_mat.sum()]
                                        for category in exposures} for year in self.years} for scenario in
                      self.scenarios}
        return agg_impact

    def get_relative_change_matrices(self, reference_year, categories):
        relative_median_impact_matrices = {scenario: {year: {category: self.compute_relative_change(
            self.median_impact_matrices[scenario][year][category],
            self.median_impact_matrices[scenario][reference_year][category])
            for category in categories} for year in self.years} for scenario in self.scenarios}
        return relative_median_impact_matrices

    def append_years(self, impacts):
        for year in impacts.years:
            for scenario in impacts.scenarios:
                self.median_impact_matrices[scenario][year] = impacts.median_impact_matrices[scenario][year]
                self.agg_impacts_mc[scenario][year] = impacts.agg_impacts_mc[scenario][year]
        self.years = sorted(self.years + impacts.years)

    @staticmethod
    def compute_relative_change(matrix, matrix_ref):
        matrix_rel = (np.nan_to_num((matrix.toarray() - matrix_ref.toarray())/matrix_ref.toarray()))*100
        return csr_matrix(matrix_rel)


class ImpactsHeatMortality(ImpactsHeatProductivity):
    def __init__(self, scenarios, years, n_mc):
        super().__init__(scenarios, years, n_mc)

    def calculate_impact(self, scenario, year, exposures, directory_hazard, nyears_hazards, crs_exposures=4326):
        exposures = Exposures(exposures)
        exposures.check()
        hazard = call_hazard(directory_hazard, scenario, year, nyears_hazards)
        if_hw_set = call_impact_functions()
        impact = ImpactHeatMortality()
        impact.calc(exposures, if_hw_set, hazard, save_mat=True)
        return csr_matrix(impact.imp_mat.sum(axis=0))


class ImpactHeatMortality(Impact):
    def __init__(self):
        super().__init__()
        self._exp_impact = self._exp_impact_mortality

    def _exp_impact_mortality(self, exp_iimp, exposures, hazard, imp_fun, insure_flag):
        """Compute impact for inpute exposure indexes and impact function.

        Parameters:
            impact (Impact): impact, object to be modified
            exp_iimp (np.array): exposures indexes
            exposures (Exposures): exposures instance
            key (str): exposures names
            hazard (Hazard): hazard instance
            imp_fun (ImpactFunc): impact function instance
            insure_flag (bool): consider deductible and cover of exposures
            kanton (str or None): Name of canton. Default: None (all of Switzerland)
        """
        if not exp_iimp.size:
            return

        # file containing the number of annual deaths per CH / Canton for each age category

        # PREPROCESSING STEP:

        # get assigned centroids
        icens = exposures[INDICATOR_CENTR + hazard.tag.haz_type].values[exp_iimp]
        # get affected intensities
        temperature_matrix = hazard.intensity[:, icens]  # intensity of the hazard
        # get affected fractions
        # get exposure values
        exposure_values = exposures.value.values[exp_iimp]
        daily_deaths = exposures.daily_deaths.values[exp_iimp]

        max_temp = temperature_matrix.max()
        expected_deaths = [daily_deaths / imp_fun.calc_mdr(value)
                           for value in range(22, int(np.ceil(max_temp)) + 1)]
        average_death = np.sum(np.multiply(exposure_values, expected_deaths[t]) for t in range(len(expected_deaths)))
        # Compute impact matrix
        self.imp_mat[:, exp_iimp] = self._impact_mortality(temperature_matrix, exposure_values, average_death,
                                                           imp_fun)

    @staticmethod
    def _impact_mortality(temperature_matrix, exposure_values, average_death, imp_fun):
        temperature_array = temperature_matrix.astype(int).toarray()
        temperatures = np.unique(temperature_array)
        temperatures = temperatures[temperatures > 21]
        occurence = np.apply_along_axis(np.bincount, axis=0, arr=temperature_array,
                                        minlength=np.max(temperature_array) + 1)
        occurence = {t: occurence[t] for t in range(22, len(occurence))}
        value = {t: np.multiply(exposure_values, imp_fun.calc_mdr(t) - 1) for t in temperatures}
        af = {t: np.divide(value[t], value[t] + 1) for t in temperatures}
        return np.sum(af[t] * occurence[t] * average_death for t in temperatures)
