# %%

"""
Polar projection, but in a rectangular box.
"""
import numpy as np

import matplotlib.pyplot as plt
from matplotlib.projections import PolarAxes
import math
from io import StringIO
# from .compass import Compass
# from fabrikApi.plugins.CIR.views.plots.compass import Compass

import xml.etree.ElementTree as ET

import numpy as np
import math

np.random.seed(5555)

class Dot:
    value = None  # value on 1:100 scale
    x = None  # position in on x-axis (can differ from value...)
    y = None # row number
    angle = None   # angle (position) number (on X-axis)
    angleWidth = None # how wide is the angle used for this dot. (depending on y position)
    isUpperBoundary = False
    isLowerBoundary = False

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


class Compass:

    innery = 1
    outery = 20
    maxAngle = 180
    
    # helper
    xAxisMax = 100 # scale from 0 to 100
    ceilingy = 0
    slotsByY = {} # free slots...
    dots = []

    UNEXPLAINED_RADIAL_CORRECTION = 0.2

    def __init__(self, config={}):

        if config:
            if 'innery' in config:
                assert config['innery'] > 0
                self.innery = config['innery']
            if 'outery' in config:
                assert config['outery'] > self.innery 
                self.outery = config['outery']
            if 'maxAngle' in config:
                assert config['maxAngle'] > 0
                self.maxAngle = config['maxAngle']

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

        rowSlotsUnrounded = self.rowSlots(y)
        slotAngleWidth = self.slotAngleWidth(rowSlotsUnrounded)
        # rowSlotsInt = math.ceil(rowSlotsUnrounded)
        rowSlotsInt = math.floor(rowSlotsUnrounded) #substact the boundary gap

        # TODO: center angles between 0 and 180
        maxAlignGap = ((self.maxAngle) - (slotAngleWidth*(rowSlotsInt)))
        alignGap = maxAlignGap * (y % 2) #maxAlignGap*np.random.random()
        #  + slotAngleWidth/2
        # alignGap, 
        # slotAngleWidth
        slotList = list(np.arange(start=slotAngleWidth/2+alignGap, stop=self.maxAngle, step=slotAngleWidth))[:rowSlotsInt+1]
        dotList = list(map(lambda angle: Dot(None, self.getXByAngle(angle), y, angle, slotAngleWidth), slotList))
        
        #debug
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
        return 1/self.xAxisMax*x * self.maxAngle

    # def getPixelByAngle(self, y, pixel):
    #     return 
        
    # def slotPixelWidth(self, y):
    #     """ What is the angle spread for a dot on this y. (how big is the piece of cake)"""
    #     units = int(math.floor(float(y**2)* np.pi / 2))
    #     return self.xAxisMax / units

    def slotAngleWidth(self, rowSlots):
        """ What is the angle spread for a dot (depending on y). (how big is the piece of cake)"""
        return self.maxAngle / rowSlots
    
    def rowSlots(self, y):
        """ how many dots can be aligned on this y (radius)"""
        yhalf = y  + 0.5 + self.UNEXPLAINED_RADIAL_CORRECTION
        return yhalf*2 * np.pi / 2

    def getFreeSlot(self, angle, value):
        """ get lowest free slot (on this position). """

        # print("getFreeSlot %s %s" % (value, angle))

        for y in range (self.innery, self.ceilingy+1):
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
        print ("no slot found: take nearest slot")        
        for y in range (self.innery, self.ceilingy+1):
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
            nearDot = min(candidates, key = lambda dot: abs(angle - dot.angle))
            self.applySlot(nearDot, value)
            return nearDot

        raise Exception("can not allocate all values (Value: %s)" % value)


    def applySlot(self, slot, value):
        slot.value = value
        self.dots.append(slot)
        self.slotsByY[slot.y].remove(slot)
        
        # create slots for row above..
        self.generateRowSlots(slot.y + 1)


    def add(self, value):
        """ add a dot to the plot"""
        # print(".", value)
        assert round(value) in range(0,101), value

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

    compass = Compass(config={"innery": 5, "outery": 30})

    # add a dot into the middle
    compass.add(50)
    compass.add(40)
    compass.add(40)
    compass.add(40)

    try:
        # Capacity: uniform: 500
        for i in np.random.rand(500):
            # print(i, "ll")
            compass.add(round(i*100))

    except Exception as e:
        print ("Plot is full: Cannot place more dots meaningfully. The rest is skipped. (Make sure, the data is in random order.)")
        pass



    # %%
    # SVG NAMESPACE

    ET.register_namespace("", "http://www.w3.org/2000/svg")

    # POLAR PLOT
    with plt.xkcd():


        # Figure
        fig = plt.figure(
            # figsize=(60, 20)
        )
        fig.set_figwidth(9) 
        fig.set_figheight(7) 

        # canvas
        ax = fig.add_subplot(projection='polar')        
        # size and axis length
        ax.set_aspect(1)
        ax.set_xlim(0, math.radians(compass.maxAngle))
        ax.set_ylim(compass.innery-0.5, compass.outery)
        # Reset origin
        ax.set_rorigin(-compass.innery)

        # AXIS
        # Remove grid lines
        ax.grid(False)
        # ax.set_axis_off()
        # ax.get_xaxis().set_visible(False)
        # ax.get_xaxis().set_ticks(['a','b','c'])
        # labels = [item.get_text() for item in ax.get_xticklabels()]
        # labels[1] = 'Testing'

        # ax.set_xticklabels(labels)
        ax.get_yaxis().set_visible(False)
        x = [0,np.pi/2,np.pi]
        labels = ['Zustimmung', 'Teils/Teils', 'Ablehnen']
        plt.xticks(x, labels) # 

        # Dots
        area = fig.dpi /4
        # , c=colors, 
        # Compute areas and colors
        xpos = list(map(lambda dot: math.radians(dot.angle), compass.dots))
        ypos = list(map(lambda dot: dot.y, compass.dots))
        # 60 * np.random.rand(N) + 40
        # colors = ypos
        scatter = ax.scatter(xpos, ypos, s=area, cmap='hsv', alpha=0.75)
        
        # plt.ylabel('hallo')
        # ax.xlabel('hallo')
        # ax

        # N Text
        N = len(compass.dots)
        tooltip = ax.text(
            compass.dots[0].x, 
            compass.dots[0].y, 
            "Chart Size - N: %s" % N, 
            ha='center',
            fontsize=12, 
            color='#DD4012',
            bbox=dict(boxstyle='round, pad=.5',
                fc=(.1, .1, .1, .92),
                ec=(1., 1., 1.), lw=1,
                zorder=1))


        # # TOOLTIP
        # N = len(compass.dots)
        # tooltip = ax.text(
        #     compass.dots[0].x, 
        #     compass.dots[0].y, 
        #     "Chart Ready", 
        #     ha='center',
        #     fontsize=12, 
        #     color='#DD4012',
        #     bbox=dict(boxstyle='round, pad=.5',
        #         fc=(.1, .1, .1, .92),
        #         ec=(1., 1., 1.), lw=1,
        #         zorder=1))
        # tooltip.set('visibility', 'hidden')

        # ax2.scatter(np.linspace(0, 90, 4), np.linspace(50, 100, 4), np.linspace(20, 10, 10))



        # %% OUTPUT
        # plt.show()# %%

        f = StringIO()
        fig.savefig(f, format='svg')
        content = f.getvalue()
        f.truncate(0)
        return content

compassplot()