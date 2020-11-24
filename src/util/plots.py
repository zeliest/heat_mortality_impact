import pickle
import random

import pandas as pd
import matplotlib.cm as cm
import numpy as np
import matplotlib.pyplot as plt
from climada.engine import Impact
from climada.entity import Exposures
from scipy.sparse import csr_matrix


def plot_impacts_heat(agg_impacts_mc, unit, impact_type, uncertainty=True, color=None, labels_cat=None, save=False):
    # Add a column to each dataframe with the sum of all exposures for each monte carlo.
    for s_ in agg_impacts_mc:
        for y_ in sorted(list(agg_impacts_mc[s_])):
            agg_impacts_mc[s_][y_] = pd.DataFrame.from_dict(agg_impacts_mc[s_][y_])
        # agg_impacts_mc[s_][y_]['total'] \
        #    = agg_impacts_mc[s_][y_][list(agg_impacts_mc[s_][y_].columns)].sum(axis=1)

    rcps = {'RCP26': 'RCP2.6', 'RCP45': 'RCP4.5', 'RCP85': 'RCP8.5'}  # to get the correct name in the plots

    median = {}
    minimums = {}
    maximums = {}

    if uncertainty:
        for s_ in agg_impacts_mc:
            median[rcps[s_]] = pd.DataFrame()  # dataframe containing the median realization for the different exposures
            maximums[rcps[
                s_]] = pd.DataFrame()  # dataframe containing the 95th percentile realization for the different exposures
            minimums[rcps[
                s_]] = pd.DataFrame()  # dataframe containing the 5th percentile realization for the different exposures

            for y_ in sorted(list(agg_impacts_mc[s_])):
                median[rcps[s_]][str(y_)] = ((agg_impacts_mc[s_][y_]).median())  # don't need the total here
                maximums[rcps[s_]][str(y_)] = ((agg_impacts_mc[s_][y_]).quantile(0.95))
                minimums[rcps[s_]][str(y_)] = ((agg_impacts_mc[s_][y_]).quantile(0.05))

            median[rcps[s_]] = median[rcps[s_]].transpose()
            maximums[rcps[s_]] = maximums[rcps[s_]].transpose()
            minimums[rcps[s_]] = minimums[rcps[s_]].transpose()


        if save:
            fig1, ax1 = plot_clustered_stacked(median, minimums, maximums, unit, color=color, error_bars=False, plot_legend=False, labels_cat= labels_cat)
            plt.savefig(''.join(['../figures/', impact_type, '_bar_2020_2080.pdf']), bbox_inches='tight')
            fig2, ax2 = plot_clustered_stacked(median, minimums, maximums, unit, color=color, labels_cat=labels_cat)
            plt.savefig(''.join(['../figures/', impact_type, '_bar_err_2020_2080.pdf']), bbox_inches='tight')


def plot_clustered_stacked(medians, minimums, maximums, unit, color=None, ref_year='2020', error_bars=True,
                           plot_legend=True, labels_cat=None):
    """Given a dict of dataframes, with identical columns and index, create a clustered stacked bar plot.
labels is a list of the names of the dataframe, used for the legend
H is the hatch used for identification of the different dataframe.
Minimums and maximums are also dict of dataframe with the same structure but containing the extremes to make an error bar
partly copied from: https://stackoverflow.com/questions/22787209/how-to-have-clusters-of-stacked-bars-with-python-pandas
"""

    fig, ax = plt.subplots()
    if labels_cat is None:
        labels_cat = list(medians[list(medians.keys())[0]])
    len_col = len(medians[list(medians.keys())[0]].columns)
    b_width = 0.27
    hatches = ['', '/', '///']
    if color is None:
        color = ["#" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)]) for i in range(len_col)]
    else:
        color = color

    for scenario_num, scenario in enumerate(medians):
        medians[scenario].columns = (column for column in
                                     range(len_col))  # change the names of the columns, otherwise weird legend...
        H = hatches[scenario_num]
        N = len(medians[scenario])
        index = np.arange(N)
        labels = medians[scenario].index
        for p, column in enumerate(medians[scenario]):
            if p == 0:
                bottom0 = None
                bottom1 = None
            else:
                bottom = sum(medians[scenario].iloc[:, b] for b in range(0, p))
                bottom0 = bottom[0]
                bottom1 = bottom[1:]
            if p == len(medians[scenario].columns) - 1:
                err = np.array([medians[scenario].sum(axis=1).values - minimums[scenario].sum(axis=1).values,
                                maximums[scenario].sum(axis=1).values - medians[scenario].sum(axis=1).values])
                err0 = [[err[0, 0]], [err[1, 0]]]
                err1 = err[:, 1:]
            if p != (len(medians[scenario].columns) - 1) or error_bars == False:
                err0 = None
                err1 = None
            position = index + scenario_num * b_width
            if scenario == 'RCP8.5':
                bars1 = ax.bar(b_width, medians[scenario].iloc[0, p],
                               width=b_width, hatch=H,
                               bottom=bottom0,
                               color=color[p], edgecolor='white', label=ref_year, yerr=err0,
                               error_kw=dict(barsabove=True, elinewidth=1, capsize=3, ecolor='gray'))
            bars2 = ax.bar(position[1:], medians[scenario].iloc[1:, p], data=medians[scenario].iloc[1:, p],
                           width=b_width, hatch=H,
                           bottom=bottom1,
                           color=color[p], edgecolor='white', label=labels_cat[p], yerr=err1,
                           error_kw=dict(barsabove=True, elinewidth=1, capsize=3, ecolor='gray'))

        ax.set_ylabel(unit)

        plt.xticks(index + b_width, labels)
        if plot_legend:
            if scenario_num == 0:
                dummy_bars = []
                for i in range(len(hatches)):
                    dummy_bars.append(ax.bar(0, 0, color="silver", hatch=hatches[i], edgecolor='white'))
                l1 = ax.legend(bbox_to_anchor=(0.7, -0.43), loc="lower right")
                plt.legend(dummy_bars, list(medians.keys()), bbox_to_anchor=(1, -0.43), loc="lower right")
                l2 = ax.add_artist(l1)

        medians[scenario].columns = labels_cat
    ax.set(xlim=[-0.3, np.max(position)+0.3])
    return fig, ax
