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



# # PolarAxes.PolarTransform takes radian. However, we want our coordinate
# # system in degree
# tr = Affine2D().scale(np.pi/180, 1) + PolarAxes.PolarTransform()
# # Polar projection, which involves cycle, and also has limits in
# # its coordinates, needs a special method to find the extremes
# # (min, max of the coordinate within the view).
# extreme_finder = angle_helper.ExtremeFinderCycle(
#     nx=20, ny=20,  # Number of sampling points in each direction.
#     lon_cycle=360, lat_cycle=None,
#     lon_minmax=None, lat_minmax=(0, np.inf),
# )



# fig = plt.figure(figsize=(60, 10))

# # Find grid values appropriate for the coordinate (degree, minute, second).
# grid_locator1 = angle_helper.LocatorDMS(12)
# # Use an appropriate formatter.  Note that the acceptable Locator and
# # Formatter classes are a bit different than that of Matplotlib, which
# # cannot directly be used here (this may be possible in the future).
# tick_formatter1 = angle_helper.FormatterDMS()

# grid_helper = GridHelperCurveLinear(
#     tr, extreme_finder=extreme_finder,
#     grid_locator1=grid_locator1, tick_formatter1=tick_formatter1)
# ax1 = fig.add_subplot(
#     1, 2, 2, axes_class=HostAxes, grid_helper=grid_helper)

# # make ticklabels of right and top axis visible.
# ax1.axis["right"].major_ticklabels.set_visible(False)
# ax1.axis["top"].major_ticklabels.set_visible(False)
# # let right axis shows ticklabels for 1st coordinate (angle)
# ax1.axis["right"].get_helper().nth_coord_ticks = 0
# # let bottom axis shows ticklabels for 2nd coordinate (radius)
# ax1.axis["bottom"].get_helper().nth_coord_ticks = 1

# ax1.set_aspect(1)
# ax1.set_xlim(-100, 100)
# ax1.set_ylim(0, 100)

# ax1.grid(True, zorder=0)

# # A parasite axes with given transform
# ax2 = ax1.get_aux_axes(tr)
# # note that ax2.transData == tr + ax1.transData
# # Anything you draw in ax2 will match the ticks and grids of ax1.
# ax1.parasites.append(ax2)
# ax2.plot(np.linspace(0, 30, 51), np.linspace(10, 10, 51), linewidth=2)

# background colors
# ax2.pcolor(np.linspace(0, 90, 4), np.linspace(0, 100, 4),
#             np.arange(9).reshape((3, 3)))
# # lines
# ax2.contour(np.linspace(0, 90, 4), np.linspace(0, 10, 4),
#             np.arange(16).reshape((4, 4)), colors="k")

# ax2.bar(np.linspace(0, 90, 4), np.linspace(50, 100, 4))

# Fixing random state for reproducibility
# np.random.seed(19680801)


# %%


# POLAR PLOT
# Compute areas and colors
N = 50
r = np.pi * np.random.rand(N)
theta = 60 * np.random.rand(N) + 40
# area = 20 * r**2
area = 20
colors = theta

fig = plt.figure()
ax = fig.add_subplot(projection='polar')
ax.set_aspect(1)
ax.set_xlim(0, np.pi)
ax.set_ylim(40, 100)
ax.scatter(r, theta, c=colors, s=area, cmap='hsv', alpha=0.75)
# ax2.scatter(np.linspace(0, 90, 4), np.linspace(50, 100, 4), np.linspace(20, 10, 10))

ax.set_rorigin(-40)
# ax.set_theta_zero_location('W', offset=10)

plt.show()# %%


# %%
