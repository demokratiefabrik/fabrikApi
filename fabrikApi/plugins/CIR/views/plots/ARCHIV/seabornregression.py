# %%
# https://stackoverflow.com/questions/8671808/matplotlib-avoiding-overlapping-datapoints-in-a-scatter-dot-beeswarm-plot

import seaborn as sns
iris = sns.load_dataset('iris')

sns.swarmplot('species', 'sepal_length', data=iris)
# sns.regplot(x='sepal_length',
#             y='sepal_width',
#             data=iris,
#             fit_reg=False,  # do not fit a regression line
#             x_jitter=0.3,  # could also dynamically set this with range of data
#             y_jitter=0.3,
#             scatter_kws={'alpha': 0.5})  # set transparency to 50%

# %%
# import seaborn as sns
# iris = sns.load_dataset('iris')
# sns.lmplot(x='sepal_length', y='sepal_width', hue='species', data=iris, fit_reg=False, x_jitter=0.1, y_jitter=0.1)  
# %%


# data = np.random.randn(100)

# width = 0.4     # the maximum width of each 'row' in the scatter plot
# xpos = 0        # the centre position of the scatter plot in x

# counts, edges = np.histogram(data, bins=20)

# centres = (edges[:-1] + edges[1:]) / 2.
# yvals = centres.repeat(counts)

# max_offset = width / counts.max()
# offsets = np.hstack((np.arange(cc) - 0.5 * (cc - 1)) for cc in counts)
# xvals = xpos + (offsets * max_offset)

# fig, ax = plt.subplots(1, 1)
# ax.scatter(xvals, yvals, s=30, c='b')










# # %%

# # ANOTHER ONE:.... (KDE)
# import seaborn as sns
# from scipy.stats import gaussian_kde
# import numpy as np
# import matplotlib.pyplot as plt
# # data = sns.load_dataset('iris')
# width = 10
# data = np.random.randn(100)

# kde = gaussian_kde(data)
# density = kde(data)     # estimate the local density at each datapoint

# # generate some random jitter between 0 and 1
# jitter = np.random.rand(*data.shape) - 0.5 

# # scale the jitter by the KDE estimate and add it to the centre x-coordinate
# xvals = 1 + (density * jitter * width * 2)

# fig = plt.figure()
# ax = fig.add_subplot(projection='polar')
# ax.scatter(xvals, data, s=30, c='g')
# # for sp in ['top', 'bottom', 'right']:
# #     ax.spines[sp].set_visible(False)
# ax.tick_params(top=False, bottom=False, right=False)

# ax.set_xticks([0, 1])
# ax.set_xticklabels(['Histogram', 'KDE'], fontsize='x-large')
# fig.tight_layout()

# plt.show();




# # %%
# import scipy.stats as stats
# import matplotlib.pyplot as plt
# import numpy as np

# def hist_with_kde(data, bandwidth = 0.3):
#     #set number of bins using Freedman and Diaconis
#     q1 = np.percentile(data,25)
#     q3 = np.percentile(data,75)


#     n = len(data)**(.1/.3)
#     rng = max(data) - min(data)
#     iqr = 2*(q3-q1)
#     bins = int((n*rng)/iqr)

#     x = np.linspace(min(data),max(data),200)

#     kde = stats.gaussian_kde(data)
#     kde.covariance_factor = lambda : bandwidth
#     kde._compute_covariance()

#     plt.plot(x,kde(x),'r') # distribution function
#     plt.hist(data,bins=bins,normed=True) # histogram

# data = np.random.randn(500)
# hist_with_kde(data,0.25)

# %%
