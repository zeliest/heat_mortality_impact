import pandas as pd
import matplotlib.cm as cm
import numpy as np
import matplotlib.pyplot as plt


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
