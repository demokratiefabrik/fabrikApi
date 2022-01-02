# %%

"""
Polar projection, but in a rectangular box.
"""
from matplotlib.patches import Patch
import mpld3
import numpy as np
from mpld3 import plugins

import matplotlib.pyplot as plt
from matplotlib.projections import PolarAxes
import math
from io import BytesIO
import matplotlib.style as mplstyle
# from .compass import Compass
# from fabrikApi.plugins.CIR.views.plots.compass import Compass

# import lxml.etree.ElementTree as ET
import lxml.etree as ET


import numpy as np
import math

np.random.seed(5555)


class Dot:
    value = None  # value on 1:100 scale
    x = None  # position in on x-axis (can differ from value...)
    y = None  # row number
    angle = None   # angle (position) number (on X-axis)
    # how wide is the angle used for this dot. (depending on y position)
    angleWidth = None
    isUpperBoundary = False
    isLowerBoundary = False
    index = None

    def __init__(self, value, x, y, angle, angleWidth):
        self.value = value
        self.x = x
        self.y = y
        self.angle = angle
        self.angleWidth = angleWidth

    def overlapping(self, angle):
        """ does current slot overlapps with given angle..."""
        # TODO <=
        # correct also for row intent at boundary dots (with no direct overlapp)
        upperlimit = angle <= self.angle+self.angleWidth/2 or self.isUpperBoundary
        lowerlimit = angle > self.angle-self.angleWidth/2 or self.isLowerBoundary
        return (lowerlimit and upperlimit)

    def overlappingWithTolerance(self, angle):
        """ does current slot overlapps with given angle...
        Tolerance: 40 degree """
        # TODO
        toleranceAngle = 5
        return (angle > self.angle-toleranceAngle and angle <= self.angle+toleranceAngle)



class Row:
    """ Where should the dots be places on each row? """
    y = None  # value on 1:100 scale
    innerMargin = None   # angle (position) number (on X-axis)
    angleWidth = None
    forceJustification = None
    chartAngle = None

    def __init__(self, y, forceJustification, chartAngle):
        self.forceJustification = forceJustification
        self.y = y
        self.chartAngle = chartAngle



class Compass:

    innery = 5 # lowest y-value shown
    outery = 20 # highest y-value shown
    chartAngle = 180 # angle of the polar chart (180 = half-circle) 
    forceJustification = False # force left/rigth justifications of dots on each y-line
    

    # helper
    xAxisMax = 100  # scale from 0 to 100
    ceilingy = 0
    slotsByY = {}  # free slots...
    dots = []

    def __init__(self, config={}):

        if config:
            if 'innery' in config:
                assert config['innery'] > 0
                self.innery = config['innery']
            if 'outery' in config:
                assert config['outery'] > self.innery
                self.outery = config['outery']
            if 'chartAngle' in config:
                assert config['chartAngle'] > 0
                self.chartAngle = config['chartAngle']
            if 'forceJustification' in config:
                assert config['forceJustification'] in [True, False]
                self.forceJustification = config['forceJustification']

                

        # generate angles for baseline (=> innery)
        self.generateRowSlots(self.innery)

    def generateRowSlots(self, y):
        """generate empty slots for new y row"""

        if y > self.outery:
            # maximal y value reached...
            return None

        if y <= self.ceilingy:
            # slots for this row are already defined...
            return None

        assert y > self.ceilingy, (y, self.ceilingy)
        assert y >= self.innery


        row = Row(y, self.forceJustification, self.chartAngle)


        rowSlotsUnrounded = self.rowSlots(y)
        slotAngleWidth = self.slotAngleWidth(rowSlotsUnrounded)
        # rowSlotsInt = math.ceil(rowSlotsUnrounded)
        # substact the boundary gap
        rowSlotsInt = math.floor(rowSlotsUnrounded)

        # TODO: center angles between 0 and 180
        maxAlignGap = ((self.chartAngle) - (slotAngleWidth*(rowSlotsInt)))
        alignGap = maxAlignGap * (y % 2)  # maxAlignGap*np.random.random()
        #  + slotAngleWidth/2
        # alignGap,
        # slotAngleWidth
        slotList = list(np.arange(start=slotAngleWidth/2+alignGap,
                        stop=self.chartAngle, step=slotAngleWidth))[:rowSlotsInt+1]
        dotList = list(map(lambda angle: Dot(value=None, x=self.getXByAngle(
            angle), y=y, angle=angle, angleWidth=slotAngleWidth), slotList))
        # alue, x, y, angle, angleWidth, index
        # debug
        # dotList = list(map(lambda angle: angle, slotAngleWidth), slotList))

        # self.getXByAngle(slotList[1]) - self.getXByAngle(slotList[0])
#
        # self.slots.extend(dotList)
        dotList[0].isLowerBoundary = True
        dotList[-1].isUpperBoundary = True
        self.slotsByY[y] = dotList
        self.ceilingy = y

    def getXByAngle(self, angle):
        return 1/180*angle * self.xAxisMax

    def getAngleByX(self, x):
        return 1/self.xAxisMax*x * self.chartAngle

    # def getPixelByAngle(self, y, pixel):
    #     return

    # def slotPixelWidth(self, y):
    #     """ What is the angle spread for a dot on this y. (how big is the piece of cake)"""
    #     units = int(math.floor(float(y**2)* np.pi / 2))
    #     return self.xAxisMax / units

    def slotAngleWidth(self, rowSlots):
        """ What is the angle spread for a dot (depending on y). (how big is the piece of cake)"""
        return self.chartAngle / rowSlots

    def rowSlots(self, y):
        """ how many dots can be aligned on this y (radius)"""
        yhalf = y + (self.innery) # add space in the inner circle
        return yhalf*2 * np.pi / 2

    def getFreeSlot(self, angle, value):
        """ get lowest free slot (on this position). """

        # print("getFreeSlot %s %s" % (value, angle))

        for y in range(self.innery, self.ceilingy+1):
            if y not in self.slotsByY.keys():
                print("SLOT NOT READY %s %s %s" % (value, angle, y))
                break
            for dot in self.slotsByY[y]:
                if dot.overlapping(angle):
                    self.applySlot(dot, value)
                    return dot

        # No slot found:-(
        # Tolerance:
        # - 40 Grad
        # - no overlapping with other left over...
        # - minimal angle gap
        candidates = []
        print("no slot found: take nearest slot")
        for y in range(self.innery, self.ceilingy+1):
            if not y in self.slotsByY:
                break
            for dot in self.slotsByY[y]:
                if not dot.overlappingWithTolerance(angle):
                    # too far away from ideal point
                    continue

                # slot cannot be built on a free slots (ie.e. slots already inside the candidates list.)
                if not any(candidate.y < dot.y and candidate.overlapping(dot.angle) for candidate in candidates):
                    candidates.append(dot)

                # dot = min(candidates, key=lambda x: x.angle)
                # if next(filter(lambda candidate: not candidates.overlapping(dot.angle), candidates)):
                #     candidates.append(dot)

        # order candidates by angle
        if len(candidates) > 0:
            nearDot = min(candidates, key=lambda dot: abs(angle - dot.angle))
            self.applySlot(nearDot, value)
            return nearDot

        raise Exception("can not allocate all values (Value: %s)" % value)

    def applySlot(self, slot, value):
        slot.value = value
        slot.index = len(self.dots)
        self.dots.append(slot)
        self.slotsByY[slot.y].remove(slot)

        # create slots for row above..
        self.generateRowSlots(slot.y + 1)

    def add(self, value):
        """ add a dot to the plot"""
        # print(".", value)
        assert round(value) in range(0, 101), value

        y = self.innery
        angle = self.getAngleByX(value)
        return self.getFreeSlot(angle, value)


# compass = Compass()

# add a dot into the middle
# compass.add(50)
# compass.add(40)
# compass.add(40)
# compass.add(40)
# compass.dots


# pip install matplotlib seaborn

def compassplot():

    compass = Compass(config={"innery": 5, "outery": 30, "forceJustification": True})

    # add a dot into the middle
    try:
        compass.add(50)
        compass.add(40)
        compass.add(40)
        compass.add(40)
        # Capacity: uniform: 500
        for i in np.random.rand(500):
            # print(i, "ll")
            compass.add(round(i*100))

    except Exception as e:
        print("Plot is full: Cannot place more dots meaningfully. The rest is skipped. (Make sure, the data is in random order.)")
        pass

    # %%
    # SVG

    # Should fasten the svg . not sure if this works
    mplstyle.use('fast')

    # Figure
    fig = plt.figure(frameon=False)
    fig.set_figwidth(9)
    fig.set_figheight(7)

    
    # fig.set_tight_layout(True)
    
    # canvas
    ax = fig.add_subplot(projection='polar')
    # size and axis length
    ax.set_aspect(1)
    ax.set_xlim(0, math.radians(compass.chartAngle))
    ax.set_ylim(compass.innery-0.5, compass.outery+0.5)
    # Reset origin
    ax.set_rorigin(-compass.innery)

    # AXIS
    # Remove grid lines
    # ax.grid(False)
    # ax.axis('off') # hide frame?
    # ax.get_yaxis().set_visible(False)

    # x axis ticks
    x = [0, np.pi/2, np.pi]
    labels = ['Zustimmung', 'Teils/Teils', 'Ablehnen']
    plt.xticks(x, labels)

    # Dots (radius?)
    dotSize = fig.dpi / 5
    # , 
    # Compute areas and colors
    xpos = list(map(lambda dot: math.radians(dot.angle), compass.dots))
    ypos = list(map(lambda dot: dot.y, compass.dots))
    # , c=colors cmap='hsv',
    ax.scatter(xpos, ypos, gid='scatgrid',
                         s=dotSize, alpha=0.75)

    
    # Create patches to which tooltips will be assigned.
    # rect1 = plt.Rectangle((10, -20), 10, 5, fc='blue')
    # rect2 = plt.Rectangle((-20, 15), 10, 5, fc='green')
    # shapes = [rect1, rect2]
    # labels = ['This is a blue rectangle.', 'This is a green rectangle']

    # for i, (item, label) in enumerate(zip(shapes, labels)):
    #     patch = ax.add_patch(item)
    #     annotate = ax.annotate(labels[i], xy=item.get_xy(), xytext=(0, 0),
    #                         textcoords='offset points', color='w', ha='center',
    #                         fontsize=8, bbox=dict(boxstyle='round, pad=.5',
    #                                                 fc=(.1, .1, .1, .92),
    #                                                 ec=(1., 1., 1.), lw=1,
    #                                                 zorder=1))

    #     ax.add_patch(patch)
    #     patch.set_gid('mypatch_{:03d}'.format(i))
    #     annotate.set_gid('mytooltip_{:03d}'.format(i))
    f = BytesIO()
    fig.savefig(f, format='svg', transparent=True)

    # XML MODIFICATIONS
    # Add dot ids
    root = ET.fromstring(f.getvalue())
    # set 100% size
    root.attrib['width'] = '100%'
    root.attrib['height'] = '100%'

    # root.xpath('//*')
    # TODO: do more efficient xpath...
    scatgrid = root.find('.//*[@id="scatgrid"]')
    nodes = scatgrid.findall('.//*[@clip-path]/*')
    for i in range(len(nodes)):
        node = nodes[i]
        node.attrib['id'] = "dot%s" % i
        # onmouseoverdot
        node.attrib['onmouseover'] = "dotclick(this, %s);" % i

    # add script    
    # script = getSvgScript()
    # Insert the script at the top of the file and save it.
    # root.insert(0, ET.XML(script))

    # # tree.set('onload', 'init(evt)')
    # # tooltip = xmlid['mytooltip_{:03d}'.format(index)]
    # onechild.set('id', 'dot1')
    content = ET.tostring(root,  xml_declaration=True)
    # content = f.getvalue()
    # f.truncate(0)  # empty again
    return content


compassplot()
