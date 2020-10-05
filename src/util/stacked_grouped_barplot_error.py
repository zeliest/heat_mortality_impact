import random
import pandas as pd
import matplotlib.cm as cm
import numpy as np
import matplotlib.pyplot as plt


def plot_clustered_stacked_with_error(data, minimums, maximums, color=None):
    """Given a dict of dataframes, with identical columns and index, create a clustered stacked bar plot.
labels is a list of the names of the dataframe, used for the legend
H is the hatch used for identification of the different dataframe.
Minimums and maximums are also dict of dataframe with the same structure but containing the extremes to make an error bar
partly copied from: https://stackoverflow.com/questions/22787209/how-to-have-clusters-of-stacked-bars-with-python-pandas
"""

    ax = plt.subplot(111)
    labels_graph = list(data[list(data.keys())[0]])
    lc = len(data[list(data.keys())[0]].columns)
    b_width = 0.2
    hatches = ['', '//', '//////']
    if color is None:
        color = ["#" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)]) for i in range(lc)]
    else:
        color = color

    for j_, s_ in enumerate(data):
        data[s_].columns = (i_ for i_ in range(lc))  # change the names of the columns, otherwise weird legend...
        H = hatches[j_]
        N = len(data[s_])
        index = np.arange(N)
        labels = data[s_].index
        for p_, c_ in enumerate(data[s_]):
            if p_ == 0:
                bottom = None
            else:
                bottom = sum(data[s_].iloc[:, b_] for b_ in range(0, p_))
            if p_ == len(data[s_].columns) - 1:
                err = np.array([minimums[s_].sum(axis=1), maximums[s_].sum(axis=1)])
            else:
                err = None
            ax.bar(index + j_ * b_width, data[s_].iloc[:, p_], data=data[s_], width=0.2, hatch=H,
                   bottom=bottom,
                   color=color[p_], edgecolor='white', label=labels_graph[p_], yerr=err,
                   error_kw=dict(barsabove=True, elinewidth=1, capsize=3, ecolor='gray'))

        ax.set_ylabel('Annual Expected Damage')
        if j_ == 0:
            plt.xticks(index + b_width, labels)

            ax.legend(loc=[1.01, 0.5])
            # ax.legend(h[:lc], l[:lc], loc=[1.01, 0.5])
            # ax.add_artist(l2)
        data[s_].columns = labels_graph

    return ax
