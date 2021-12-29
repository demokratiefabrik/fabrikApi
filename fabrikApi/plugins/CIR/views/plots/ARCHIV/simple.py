# %%

"""
Polar projection, but in a rectangular box.
"""
import numpy as np

import matplotlib.pyplot as plt
from matplotlib.projections import PolarAxes
from matplotlib.transforms import Affine2D

from mpl_toolkits.axisartist import angle_helper, HostAxes
from mpl_toolkits.axisartist.grid_helper_curvelinear import (
    GridHelperCurveLinear)



# %%


CA = [0,4,0,3,0,5]  
CB = 2 * np.pi * np.random.rand(1000)
CC = [0.08423, 4.0078, 0.02936, 0.04862, 3.2105, 3.7796, 1.9974, 1.6986, 1.7443, 1.6615, 1, 1, 1]

lists = [CA, CB, CC]
SPACE = 0.1
x = []
y = []
for index1, my_list in enumerate(lists):
    scores_bins = {}
    for index2, score in enumerate(my_list):
        binx = round(score, 1)
        if binx not in scores_bins:
            scores_bins[binx] = []
        scores_bins[binx].append(score)

    for key, val in sorted(scores_bins.items()):
        values = scores_bins[key]
        points = len(values)
        pos = 1 + index1 + (1 - points) / 50.
        for value in values:
            x.append(pos)
            y.append(value)
            pos += SPACE

plt.plot(x, y, 'o')
plt.xlim((0,4))
plt.ylim((-1,6))

plt.show()
# %%
