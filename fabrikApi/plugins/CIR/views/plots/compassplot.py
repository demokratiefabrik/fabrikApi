# %%

"""
Polar projection, but in a rectangular box.
"""
import matplotlib.pyplot as plt
import math
from io import BytesIO
import matplotlib.style as mplstyle
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
    config = None

    def __init__(self, value, x, y, angle, angleWidth, config):
        self.value = value
        self.x = x
        self.y = y
        self.angle = angle
        self.angleWidth = angleWidth
        self.config = config

    def overlapping(self, angle, tara=False):
        """ does current slot overlapps with given angle...
        # if tara is true: also check if angle overlapps with gap besides dot.
        """
        # TODO <=
        # corrected also for row intent at boundary dots (with no direct overlapp)
        upperlimit = angle <= self.angle+self.angleWidth/2 or self.isUpperBoundary
        lowerlimit = angle > self.angle-self.angleWidth/2 or self.isLowerBoundary
        return (lowerlimit and upperlimit)

    def overlappingWithTolerance(self, angle):
        """ does current slot overlapps with given angle...
        toleranceAngle """
        return (angle > self.angle-self.config['toleranceAngle'] and angle <= self.angle+self.config['toleranceAngle'])



class Row:
    """ Where should the dots be places on each row? """

    y = None  # value on 1:100 scale

    innerMargin = None   # angle (position) number (on X-axis)
    angleWidth = None
    chartAngle = None
    dotList = None
    config = None

    # calculated
    nofRowSlots = None
    slotAngleWidth = None # angleWidth of the dots on this row
    gapAngleWidth = None # angleWidth of the gap between the dots

    def __init__(self, y, config):
        self.config = config
        self.y = y
        self.slotNumbers()


    def slotNumbers(self):
        """ how many dots can be aligned on this y (radius)"""
        yhalf = self.y + (self.config['innery']) # add space in the inner circle
        rowSlotsUnrounded = yhalf*2 * np.pi / 2
        self.nofRowSlots = math.floor(rowSlotsUnrounded)
        gapSum = rowSlotsUnrounded - self.nofRowSlots

        # What is the angle spread for a dot (depending on y). (how big is the piece of cake)

        # calculate gap and slot angles
        if not self.config['forceJustification']:
            # dont leave space between the dots
            self.slotAngleWidth = self.config['chartAngle'] / self.nofRowSlots
            self.gapAngleWidth = 0

        if self.config['forceJustification']:
            # leave space between the dots
            nofRowGaps = self.nofRowSlots - 1
            slotGap = gapSum /  self.nofRowSlots        
            # calculated by: gapAngleWidth = slotAngleWidth * slotGap
            self.slotAngleWidth = self.config['chartAngle'] / (self.nofRowSlots + nofRowGaps*slotGap)
            self.gapAngleWidth = self.slotAngleWidth*slotGap

        # Check: gapAngleWidth * nofRowGaps + slotAngleWidth * nofRowSlots


    def getXByAngle(self, angle):
        return 1/180*angle * self.config['xAxisMax']

    def getDotList(self):
        self.dotList = []

        if self.config['forceJustification']:
            start = self.slotAngleWidth/2

        if not self.config['forceJustification']:
            # Center dot-row on the x-axis
            maxAlignGap = ((self.config['chartAngle']) - (self.slotAngleWidth*(self.nofRowSlots)))
            alignGap = maxAlignGap * (self.y % 2)  # maxAlignGap*np.random.random()
            start = self.slotAngleWidth/2 + alignGap

        slotList = list(
            np.arange(
                start=start,
                stop=self.config['chartAngle'],
                step=self.slotAngleWidth+self.gapAngleWidth))[:self.nofRowSlots]
        dotList = list(map(lambda angle: Dot(
            value=None, 
            x=self.getXByAngle(angle), 
            y=self.y, 
            angle=angle,
            angleWidth=self.slotAngleWidth, 
            config=self.config), slotList))
        # dotList = list(map(lambda angle: angle, slotAngleWidth), slotList))
        # self.getXByAngle(slotList[1]) - self.getXByAngle(slotList[0])
        dotList[0].isLowerBoundary = True
        dotList[-1].isUpperBoundary = True
        return dotList



class Compass:
    config = None
    ceilingy = None
    freeSlotsByY = None
    dots = None

    def __init__(self, config={}):

        self.dots = []
        self.freeSlotsByY = {}  # free slots...
        self.ceilingy = 0

        self.config = {
            "innery" : 5, # lowest y-value shown
            "outery" : 20, # highest y-value shown
            "chartAngle" : 180, # angle of the polar chart (180 = half-circle) 
            "forceJustification": False, # force left/rigth justifications of dots on each y-line
            "xAxisMax" : 100,  # scale from 0 to 100
            "toleranceAngle" : 10
        }

        
        # update runtime config
        self.config.update(config)

        # assert configuration
        assert self.config['innery'] > 0
        assert self.config['outery'] > self.config['innery']
        assert self.config['chartAngle'] > 0
        assert self.config['forceJustification'] in [True, False]
        assert self.config['toleranceAngle'] <= 180

        # generate angles for baseline (=> innery)
        self.generateRowSlots(self.config['innery'])

    def generateRowSlots(self, y):
        """generate empty slots for new y row"""

        if y > self.config['outery']:
            # maximal y value reached...
            return None

        if y <= self.ceilingy:
            # slots for this row are already defined...
            return None

        assert y > self.ceilingy, (y, self.ceilingy)
        assert y >= self.config['innery']


        row = Row(y, self.config)
        dotList = row.getDotList()
        self.freeSlotsByY[y] = dotList
        self.ceilingy = y

    def getAngleByX(self, x):
        return 1/self.config['xAxisMax']*x * self.config['chartAngle']


    def getFreeSlot(self, angle, value):
        """ get lowest free slot (on this position). """

        # print("getFreeSlot %s %s" % (value, angle))

        for y in range(self.config['innery'], self.ceilingy+1):
            if y not in self.freeSlotsByY.keys():
                print("SLOT NOT READY %s %s %s" % (value, angle, y))
                break
            for freeslot in self.freeSlotsByY[y]:
                # only apply perfect matching slots
                # TODO: make sure, that there is not a close empty slot on lower line...
                if freeslot.overlapping(angle):
                    self.applySlot(freeslot, value)
                    return freeslot

        # No slot found:-(
        # Tolerance:
        # - 40 Grad
        # - no overlapping with other left over...
        # - minimal angle gap
        candidates = []
        # print("no slot found: take nearest slot")
        for y in range(self.config['innery'], self.ceilingy+1):
            assert y in self.freeSlotsByY
            # if not y in self.freeSlotsByY:
            #     break
            for freeSlot in self.freeSlotsByY[y]:
                if not freeSlot.overlappingWithTolerance(angle):
                    # too far away from ideal point
                    continue

                # slot cannot be built on a free slots (ie.e. free slot is based on another free slot already inside the candidates list.)
                if not any(candidate.y < freeSlot.y and candidate.overlapping(freeSlot.angle) for candidate in candidates):
                    candidates.append(freeSlot)

        # find candidate with lowest angle discrepancy.
        if len(candidates) > 0:
            # discriminate higher-y dots over lower y => (dot.y/dot.angle)
            # discriminate higher x-axis discrepancy over exact matches => abs(angle - dot.angle)
            # TODO: test second component: dot.angleWidth
            # - dot.angleWidth
            nearDot = min(candidates, key=lambda dot: abs(angle - dot.angle))
            self.applySlot(nearDot, value, exactPlacement=False)
            return nearDot

        raise Exception("can not allocate all values (Value: %s)" % value)

    def applySlot(self, slot, value, exactPlacement=True):
        slot.value = value
        slot.exactPlacement = exactPlacement
        slot.index = len(self.dots)
        self.dots.append(slot)
        self.freeSlotsByY[slot.y].remove(slot)

        # create slots for row above..
        self.generateRowSlots(slot.y + 1)

    def add(self, value):
        """ add a dot to the plot"""
        # print(".", value)
        assert round(value) in range(0, 101), value

        y = self.config['innery']
        angle = self.getAngleByX(value)
        return self.getFreeSlot(angle, value)



    def plot(self):
        # %%
        # SVG


        # Should fasten the svg . not sure if this works
        mplstyle.use('fast')
        # plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['figure.constrained_layout.use'] = True

        # Figure DEFAULT
        fig = plt.figure(frameon=False)

        # why? earlier 9 and 7
        fig.set_figwidth(10)
        fig.set_figheight(10)   

        # removes padding between figure and subplots. (makes also spaces larger between dots)
        # fig.set_tight_layout(True)

        # canvas
        ax = fig.add_subplot(projection='polar')
        ax.set_aspect(1) # no effect, i believe
        ax.set_xlim(0, math.radians(self.config['chartAngle']))
        ax.set_ylim(self.config['innery']-0.5, self.config['outery']+0.5)
        ax.set_rorigin(-self.config['innery'])


        # x axis ticks
        x = [0, np.pi/2, np.pi]
        labels = ['Zustimmung', 'Teils/Teils', 'Ablehnen']
        plt.xticks(x, labels)

        # markers
        # SET DEFAULT VALUE: rcParams['lines.markersize'] ** 2
        dotSize = self._matplotlibMarkerSize(ax)
        xpos = list(map(lambda dot: math.radians(dot.angle), self.dots))
        ypos = list(map(lambda dot: dot.y, self.dots))

        # , c=colors cmap='hsv',
        alpha = None # remove alpha value (e.g. 'none' or 0.75)
        edgecolors = None # remove edge patches...
        ax.scatter(xpos, ypos, gid='scatgrid', s=dotSize, alpha=alpha, edgecolors=edgecolors)
        ax.set_axisbelow(True) # put grid behind dots
        # ax.grid(color='lightgrey', linestyle='dashed') # overwrites local css

        # supplement shades
        # ax.ayhline(y=10)

        # Convert to svg file stream
        f = BytesIO()
        fig.savefig(f, format='svg', transparent=True)
        root = ET.fromstring(f.getvalue()) # Convert to XML Element Templat
        f.truncate(0)  # empty stream again

        # XML POST-MODIFICATIONS
        # set 100% size
        root.attrib['width'] = '100%'
        root.attrib['height'] = '100%'

        # Add ids to dot-nodes
        # TODO: do more efficient xpath...
        scatgrid = root.find('.//*[@id="scatgrid"]')
        nodes = scatgrid.findall('.//*[@clip-path]/*')
        for i in range(len(nodes)):
            node = nodes[i]
            node.attrib['id'] = "dot%s" % i
            # onmouseoverdot
            node.attrib['onclick'] = "dotclick(this, %s);" % i
            # node.attrib['cursor'] = "pointer"
            node.attrib['pointer-events'] = "all"
            # ="all"
        
        # export XML
        content = ET.tostring(root,  xml_declaration=True)
        return content

        # TODO: 
        # add script    
        # script = getSvgScript()
        # Insert the script at the top of the file and save it.
        # root.insert(0, ET.XML(script))
        # # tree.set('onload', 'init(evt)')
        # # tooltip = xmlid['mytooltip_{:03d}'.format(index)]
        # onechild.set('id', 'dot1')
        # content = f.getvalue()


    # PLOTTER DEFS
    def _matplotlibMarkerSize(self, ax):

        start = ax.viewLim.min[1]
        posMin = ax.transData.transform((0, start))
        posMax = ax.transData.transform((0, start+1))
        ax.transData.get_affine().transform((0, start))
        
        # where is center-point
        # centerMax = ax.figure.transFigure.transform((0, start))
        # centerMin = ax.figure.transFigure.transform((0, start))
        # centerMax = ax.figure.transFigure.transform((0, start+1))

        # centerMin = ax.figure.dpi_scale_trans.inverted().transform((0, start))
        # centerMax = ax.figure.dpi_scale_trans.transform((0, start+1))

        # centerX = (centerMax[0] - centerMin[0]) / 2
        ax.transData.transform([(0, 1)]) - ax.transData.transform((0, 0))

        # pythagoras for distance in pixel
        a = posMax[0] - posMin[0]
        b = posMax[1] - posMin[1]
        c = math.sqrt(a**2+b**2)

        # ax.figure.dpi

        # print("centerX %s" % centerX)


        # convert between pixel and points (scatter requires point marker size)
        # assuming default ppi value of 72
        UNEXPLAINED_FACTOR = 1.1 
        points = c / 0.72 * UNEXPLAINED_FACTOR


        # return area: r2*
        return ((points/2) ** 2)


