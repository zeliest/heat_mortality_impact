import pickle
import random

import pandas as pd
import matplotlib.cm as cm
import numpy as np
import matplotlib.pyplot as plt
from climada.engine import Impact
from climada.entity import Exposures
from scipy.sparse import csr_matrix


def plot_impacts_heat(agg_impacts_mc, title, color=None):
    # Add a column to each dataframe with the sum of all exposures for each monte carlo.
    for s_ in agg_impacts_mc:
        for y_ in agg_impacts_mc[s_]:
            agg_impacts_mc[s_][y_] = pd.DataFrame.from_dict(agg_impacts_mc[s_][y_])
            agg_impacts_mc[s_][y_]['total'] \
                = agg_impacts_mc[s_][y_][list(agg_impacts_mc[s_][y_].columns)].sum(axis=1)

    RCPs = {'RCP26': 'RCP2.6', 'RCP45': 'RCP4.5', 'RCP85': 'RCP8.5'}  # to get the correct name in the plots

    median = {}
    minimums = {}
    maximums = {}

    for s_ in agg_impacts_mc:
        median[RCPs[s_]] = pd.DataFrame()  # dataframe containing the median realization for the different exposures
        maximums[RCPs[
            s_]] = pd.DataFrame()  # dataframe containing the 95th percentile realization for the different exposures
        minimums[RCPs[
            s_]] = pd.DataFrame()  # dataframe containing the 5th percentile realization for the different exposures

        for y_ in agg_impacts_mc[s_]:
            median[RCPs[s_]][y_] = ((agg_impacts_mc[s_][y_].iloc[:, 0:-1]).median())  # don't need the total here
            maximums[RCPs[s_]][y_] = ((agg_impacts_mc[s_][y_].iloc[:, 0:-1]).quantile(0.95))
            minimums[RCPs[s_]][y_] = ((agg_impacts_mc[s_][y_].iloc[:, 0:-1]).quantile(0.05))

        median[RCPs[s_]] = median[RCPs[s_]].transpose()
        maximums[RCPs[s_]] = maximums[RCPs[s_]].transpose()
        minimums[RCPs[s_]] = minimums[RCPs[s_]].transpose()

    fig, ax = plt.subplots()
    plot_clustered_stacked(median, title='', color=color)
    plt.ylabel(title)
    ax.ticklabel_format(style='plain')

    # plt.savefig(''.join([fig_dir,'loss_ch/predicted_loss_2020_2065.pdf']),bbox_inches='tight')
    fig, ax = plt.subplots()
    plot_clustered_stacked_with_error(median, minimums, maximums, color=color)
    plt.ylabel(title)


def plot_clustered_stacked(dataframe_dict, title="multiple stacked bar plot", H="/", **kwargs):
    """Given a dict of dataframes, with identical columns and index, create a clustered stacked bar plot.
labels is a list of the names of the dataframe, used for the legend
title is a string for the title of the plot
H is the hatch used for identification of the different dataframe
mostly copied from: https://stackoverflow.com/questions/22787209/how-to-have-clusters-of-stacked-bars-with-python-pandas
"""

    dfall = list(dataframe_dict[list(dataframe_dict.keys())[l_]] for l_ in range(len(dataframe_dict)))
    labels = list(list(dataframe_dict.keys())[k_] for k_ in range(len(dataframe_dict)))

    n_df = len(dfall)
    n_col = len(dfall[0].columns)
    n_ind = len(dfall[0].index)
    axe = plt.subplot(111)

    for df in dfall:  # for each data frame
        axe = df.plot(kind="bar",
                      linewidth=0,
                      stacked=True,
                      ax=axe,
                      legend=False,
                      grid=False,
                      **kwargs, edgecolor='white', alpha=1)  # make bar plots

    h, l = axe.get_legend_handles_labels()  # get the handles we want to modify
    for i in range(0, n_df * n_col, n_col):  # len(h) = n_col * n_df
        for j, pa in enumerate(h[i:i + n_col]):
            for rect in pa.patches:  # for each index
                rect.set_x(rect.get_x() + 1 / float(n_df + 1) * i / float(n_col))
                rect.set_hatch(H * int(i / n_col))  # edited part
                rect.set_width(1 / float(n_df + 1))

    axe.set_xticks((np.arange(0, 2 * n_ind, 2) + 1 / float(n_df + 1)) / 2.)
    axe.set_xticklabels(df.index, rotation=0)
    axe.set_title(title)

    # Add invisible data to add another legend
    n = []
    for i in range(n_df):
        n.append(axe.bar(0, 0, color="silver", hatch=H * i, edgecolor='white'))

    l1 = axe.legend(h[:n_col], l[:n_col], loc=[1.01, 0.5])
    l2 = plt.legend(n, labels, loc=[1.01, 0.1])
    axe.add_artist(l1)
    return axe


def plot_clustered_stacked_with_error(median, minimums, maximums, color=None):
    """Given a dict of dataframes, with identical columns and index, create a clustered stacked bar plot.
labels is a list of the names of the dataframe, used for the legend
H is the hatch used for identification of the different dataframe.
Minimums and maximums are also dict of dataframe with the same structure but containing the extremes to make an error bar
partly copied from: https://stackoverflow.com/questions/22787209/how-to-have-clusters-of-stacked-bars-with-python-pandas
"""

    ax = plt.subplot(111)
    labels_graph = list(median[list(median.keys())[0]])
    lc = len(median[list(median.keys())[0]].columns)
    b_width = 0.2
    hatches = ['', '//', '//////']
    if color is None:
        color = ["#" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)]) for i in range(lc)]
    else:
        color = color

    for j_, s_ in enumerate(median):
        median[s_].columns = (i_ for i_ in range(lc))  # change the names of the columns, otherwise weird legend...
        H = hatches[j_]
        N = len(median[s_])
        index = np.arange(N)
        labels = median[s_].index
        for p_, c_ in enumerate(median[s_]):
            if p_ == 0:
                bottom = None
            else:
                bottom = sum(median[s_].iloc[:, b_] for b_ in range(0, p_))
            if p_ == len(median[s_].columns) - 1:
                err = np.array([minimums[s_].sum(axis=1).values, maximums[s_].sum(axis=1).values])
            else:
                err = None
            ax.bar(index + j_ * b_width, median[s_].iloc[:, p_], data=median[s_], width=0.2, hatch=H,
                   bottom=bottom,
                   color=color[p_], edgecolor='white', label=labels_graph[p_], yerr=err,
                   error_kw=dict(barsabove=True, elinewidth=1, capsize=3, ecolor='gray'))

        ax.set_ylabel('Annual Expected Damage')
        if j_ == 0:
            plt.xticks(index + b_width, labels)

            ax.legend(loc=[1.01, 0.5])
            # ax.legend(h[:lc], l[:lc], loc=[1.01, 0.5])
            # ax.add_artist(l2)
        median[s_].columns = labels_graph

    return ax


def impact_matrix_as_impact(impact_matrix, exposures, percentage=False, canton=None):
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
                        / exposures.value.replace(0, 1)) * 100)  # put impacts in terms of percentage of exposure
    impact.unit = '%'
    return impact

