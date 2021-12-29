from io import StringIO
import matplotlib.pyplot as p
import numpy as np
import pandas as pd
import seaborn as s
import mplcursors
import matplotlib.collections
from mpld3 import plugins

# %matplotlib widget

f = StringIO()

# pip install matplotlib seaborn

def beeplot():

    # dataset
    # iris2 = pd.DataFrame(np.random.randn(777, 1), columns=list('A'))
    beta = 20
    iris = pd.DataFrame(np.random.exponential(beta, 50), columns=['sepal_length',])
    # iris = pd.DataFrame(np.array([[1, 2, 3], [4, 2, 6], [7, 1, 9],[1, 2, 3], [4, 2, 6], [7, 1, 9],[1, 2, 3], [4, 2, 6], [7, 1, 9]]),
                #    columns=['sepal_length', 'species', 'c'])

    # max(iris['sepal_length'])
    # canvas (seaborn)
    # s.set() 
    custom_params = {
        # Borders
        "font.sans-serif": 'Roboto',
        # Axis
        "axes.spines.right": False, "axes.spines.top": False, "axes.spines.bottom": False, "axes.spines.left": False}
    s.set_theme(style="ticks", rc=custom_params)

    # s.set_theme(style="whitegrid")
    # style="darkgrid"


    # GROUP BY: y='species', 
    
    # ax = s.stripplot(x='sepal_length', data=iris)
    # ax = s.violinplot(x="sepal_length", data=iris, inner=None)
    # marker="D", 
    DOT_SIZE = 6

    fig, ax = p.subplots()
    
    ax = s.swarmplot(x='sepal_length', data=iris, color="white", edgecolor="gray", palette="Set2", size=DOT_SIZE, alpha=.25, ax=ax)
    
    # tooltips
    # annot_x = (p.xlim()[1] + p.xlim()[0])/2
    # annot_y = (p.ylim()[1] + p.ylim()[0])/2
    # txt = ax.text(annot_x, annot_y, "Chart Ready", 
    #             ha='center', fontsize=36, color='#DD4012')
    # def hover(event):
    #     txt.set_text("")
    # fig.canvas.mpl_connect("motion_notify_event", hover)
        
    # fig, ax = plt.subplots()
    # sc = ax.scatter(x,y)
    # by default the tooltip is displayed "onclick"
    # we can change it by setting hover to True
    # cursor = mplcursors.cursor(fig, hover=True)
    # # by default the annotation displays the xy positions
    # # this is to change it to the countries name
    # @cursor.connect("add")
    # def on_add(sel):
    #     sel.annotation.set(text='TESTTEST') # tt[sel.target.index]

    # # labels
    # p.title('Graph')


    scatter_collections = [c for c in ax.collections if isinstance(c, matplotlib.collections.PathCollection)]
    
    # assert len(scatter_collections) == 1
    
    tooltip = plugins.PointLabelTooltip(scatter_collections[0], 
                                              labels=list(iris['sepal_length']))
                                                 
    plugins.connect(fig, tooltip)


    # OUTPUT
    p.savefig(f, format='svg')
    content = f.getvalue()
    f.truncate(0)
    return content
    