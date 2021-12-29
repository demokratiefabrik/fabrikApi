# %%
# https://stackoverflow.com/questions/8671808/matplotlib-avoiding-overlapping-datapoints-in-a-scatter-dot-beeswarm-plot


from io import StringIO
import matplotlib.pyplot as p
import numpy as np
import pandas as pd
import seaborn as s
import mplcursors
import matplotlib.collections
from mpld3 import plugins

import math
# https://stackoverflow.com/questions/8671808/matplotlib-avoiding-overlapping-datapoints-in-a-scatter-dot-beeswarm-plot


# %%


# %%




# dataset
# iris2 = pd.DataFrame(np.random.randn(777, 1), columns=list('A'))
beta = 20
iris = pd.DataFrame(np.random.exponential(beta, 50), columns=['sepal_length',])
# iris = pd.DataFrame(np.array([[1, 2, 3], [4, 2, 6], [7, 1, 9],[1, 2, 3], [4, 2, 6], [7, 1, 9],[1, 2, 3], [4, 2, 6], [7, 1, 9]]),
            #    columns=['sepal_length', 'species', 'c'])

# max(iris['sepal_length'])
# canvas (seaborn)
# s.set() 
# custom_params = {
#     # Borders
#     "font.sans-serif": 'Roboto',
#     # Axis
#     "axes.spines.right": False, "axes.spines.top": False, "axes.spines.bottom": False, "axes.spines.left": False}
# s.set_theme(style="ticks", rc=custom_params)

# s.set_theme(style="whitegrid")
# style="darkgrid"


# GROUP BY: y='species', 
# %%
beta = 20
iris = pd.DataFrame(np.random.exponential(beta, 50), columns=['sepal_length',])
     
DOT_SIZE = 6

fig, ax = p.subplots()
sc = ax.scatter([],[])


# %%
