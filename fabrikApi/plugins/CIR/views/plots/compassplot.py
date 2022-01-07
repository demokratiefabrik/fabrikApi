"""
Polar projection, but in a rectangular box.
"""
from io import BytesIO
from matplotlib import cm
import matplotlib.pyplot as plt
import math
from matplotlib.text import Annotation
import matplotlib.textpath as textpath
import numpy as np
import math

from numpy.random.mtrand import f
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas


class Compass:
    config = None
    ceilingy = None
    outerY = None
    freeSlotsByY = None
    dots = None
    rowsByY = None
    fig = None # matplotlib figure

    # TODO: is ceilingy not same as outerY

    def __init__(self, data=None, config={}):

        self.dots = []
        self.rowsByY = {}
        self.freeSlotsByY = {}  # free slots...
        self.ceilingy = 0
        self.config = {
            "markerSizeFactor": 1,  # factor to scale the markers (default 1)
            "markerColorMap": 'winter',  # factor to scale the markers (default 1)
            "innery": 2,  # lowest y-value shown (center of the circle remains empty)
            "xAxisLabels": [], # e.g. [(radians(90), 'Middle')]
            "xAxisLabelsStyle": {"size": 28},
            "chartAngle": 180,  # angle of the polar chart (180 = half-circle)
            "forceJustification": False,  # force left/rigth justifications of dots on each y-line
            "xAxisMax": 100,  # scale from 0 to 100
            "yAxisOuterPadding": 1,  # append empty space at the end of the y-axis 
            "minOuterY": 20,  # polar plots are plotted with atleast ylim(,20)
            "zoomFactor": 3.6/10, # the chart is zoomed in (because only the on half of the polar plot is used)
            # "maxOuterY" : 100 # NOT YET IMPLEMENTED

        }

        # update runtime config
        self.config.update(config)

        # assert configuration
        assert self.config['innery'] > 0
        assert self.config['minOuterY'] >= 0
        assert self.config['chartAngle'] > 0
        assert self.config['forceJustification'] in [True, False]

        self.outerY = self.config['minOuterY']

        # generate angles for baseline (=> innery)
        
        self.generateBlankSlotRow(self.config['innery'])

        # Add Data
        if data:
            for i in data:
                self.addValue(i)

    def generateBlankSlotRow(self, y):
        """generate empty slots for new y row"""

        if y > self.outerY:
            # maximal y value reached...
            return None

        if y <= self.ceilingy:
            # slots for this row are already defined...
            return None

        assert y > self.ceilingy, (y, self.ceilingy)
        assert y >= self.config['innery']

        row = CompassRow(y, self)
        self.rowsByY[y] = row
        dotList = row.getDotList()
        self.freeSlotsByY[y] = dotList
        self.ceilingy = y

    def getAngleByX(self, x):
        # TODO: use transformation functions
        return 1/self.config['xAxisMax']*x * self.config['chartAngle']

    def addValue(self, value):
        """ assign a data observation to a slot in the dotplot"""
        assert round(value) in range(0, 101), value
        y = self.config['innery']
        angle = self.getAngleByX(value)
        self.assignValueToAFreeSlot(angle, value)

    def assignValueToAFreeSlot(self, angle, value, skipBelowY=0):
        """ Assign value to a free dot-slot at a near position. """

        # It is not always needed to start at first y-row. skipBelowY
        startY = max(skipBelowY, self.config['innery'])

        for y in range(startY, self.ceilingy+1):
            if y not in self.freeSlotsByY.keys():
                print("SLOT NOT READY %s %s %s" % (value, angle, y))
                break
            for freeslot in self.freeSlotsByY[y]:
                # only apply perfect matching slots
                # TODO: make sure, that there is not a close empty slot on lower line...
                if freeslot.overlapping(angle):
                    self.registerSlot(freeslot, value)
                    return freeslot

        # No perfect match found:-(
        candidates = []
        for y in range(startY, self.ceilingy+1):
            assert y in self.freeSlotsByY
            for freeSlot in self.freeSlotsByY[y]:
                if not freeSlot.overlappingWithTolerance(angle):
                    continue
                # check if slot can be choosen: free slot should not be based on another free slot already inside the candidates list.)
                if not any(candidate.y < freeSlot.y and candidate.overlapping(freeSlot.angle) for candidate in candidates):
                    candidates.append(freeSlot)

        # find candidate with lowest angle discrepancy.
        if len(candidates) > 0:
            # discriminate higher-y dots over lower y => (dot.y/dot.angle)
            # discriminate higher x-axis discrepancy over exact matches => abs(angle - dot.angle)
            nearDot = min(candidates, key=lambda dot: abs(angle - dot.angle))
            self.registerSlot(nearDot, value, exactPlacement=False)
            return nearDot

        # No free slot is found: => Extend the plot by another row.
        # add three new lines to the plot
        # for i in range(3):
        self.outerY += 1
        self.generateBlankSlotRow(self.outerY)

        # Run again, with this free slot.
        return self.assignValueToAFreeSlot(angle, value, skipBelowY=self.outerY)

    def registerSlot(self, slot, value, exactPlacement=True):
        slot.value = value
        slot.exactPlacement = exactPlacement
        slot.index = len(self.dots)
        self.dots.append(slot)
        self.freeSlotsByY[slot.y].remove(slot)

        # create slots for row above..
        self.generateBlankSlotRow(slot.y + 1)

    def plot(self):
        # Should fasten the svg . not sure if this works
        # mplstyle.use('fast')
        plt.rcParams['font.family'] = 'Roboto'
        plt.rcParams['font.weight'] = 'light'
        plt.rcParams['svg.fonttype'] = 'none'  # font installed on client

        self.fig = plt.figure(frameon=False, dpi=400, figsize=(10,10))

        # POLAR CHART CANVAS
        ax = self.fig.add_subplot(projection='polar', aspect=1)
        ax.set_xlim(0, math.radians(self.config['chartAngle']))
        ax.set_ylim(self.config['innery']-0.5, self.outerY+0.5+self.config['yAxisOuterPadding'])
        ax.set_rorigin(-self.config['innery'])
        ax.set_axisbelow(True)  # put grid behind dots
        plt.xticks([], [])
        ax.axes.yaxis.set_ticklabels([])
        # ax.axes.yaxis.set_ticks([10,11,12],['a','b','c'])

        # ADAPT FIGURE SIZE (zoom in to remove margins...)
        ext = self.fig.gca().get_window_extent()
        self.fig.set_figheight(ext.height/self.fig.dpi)
        self.fig.set_figwidth(ext.width/self.fig.dpi*2)
        self.config["zoomUnits"] = {"top": 1+self.config['zoomFactor'], "bottom": -self.config['zoomFactor'], "left": -self.config['zoomFactor'], "right": 1+self.config['zoomFactor']}
        self.fig.subplots_adjust(**self.config["zoomUnits"])

        # BACKGROUND SECTORS
        # ax.axvspan(0, np.pi/3*1, facecolor='g', alpha=0.1)
        # ax.axvspan(np.pi/3*1, np.pi/3*2, facecolor='b', alpha=0.1)
        # ax.axvspan(np.pi/3*2, np.pi/3*3, facecolor='r', alpha=0.1)


        # Draw Canvas before convert any pixel to font size etc...
        self.fig.canvas.draw()

        # x-Axis LABELS
        for pos, label in self.config['xAxisLabels']:
            self._matplotlib_curvedText(ax, radianX=pos, y=self.outerY+1+self.config['yAxisOuterPadding'], text=label, style=self.config['xAxisLabelsStyle'])

        # MARKERS
        dotParams = {"x":[], "y": [], "c": []}
        for dot in self.dots:
            dotParams["x"].append(math.radians(dot.angle))
            dotParams["y"].append(dot.y)
            dotParams["c"].append(dot.value)
        alpha = 0.75  # remove alpha value (e.g. 'none' or 0.75)
        points = self._matplotlibGetYUnitInPoints(ax)*self.config['markerSizeFactor']
        #  edgecolors=None
        ax.scatter(gid='scatgrid', s=points**2, alpha=alpha, cmap=self.config['markerColorMap'], **dotParams)
        # https://matplotlib.org/stable/tutorials/colors/colormaps.html

    def plotAsXml(self):
        
        self.plot()
        f = BytesIO()
        self.fig.savefig(f, format='svg', dpi=self.fig.dpi)
        xml = f.getvalue()
        f.truncate(0)  # empty stream again
        return xml

    def _matplotlibGetYUnitInPixel(self, ax):
        start = ax.viewLim.min[1]
        posMin = ax.transData.transform((np.pi/2, start))
        posMax = ax.transData.transform((np.pi/2, start+1))
        a = posMax[0] - posMin[0]
        b = posMax[1] - posMin[1]
        return math.sqrt(a**2+b**2)

    def _matplotlibGetYUnitInPoints(self, ax):
        return  self._matplotlibGetYUnitInPixel(ax)* (72./ax.figure.dpi)
    
    def _matplotlibGetPointsInPixel(self, size):
        return  size/(72./self.fig.dpi)

    def _matplotlib_get_window_extent(self):
            return self.fig.get_window_extent().width, \
                self.fig.get_window_extent().height

    def _matplotlib_get_polar_chart_position(self):
        fh, fw = self._matplotlib_get_window_extent()
        leftBottom = self.fig.gca().transData.transform((np.pi, self.outerY+0.5+self.config['yAxisOuterPadding']))
        centerTop = self.fig.gca().transData.transform((np.pi/2, self.outerY+0.5+self.config['yAxisOuterPadding']))
        x =  centerTop[0]
        r = centerTop[0]-leftBottom[0]
        y =  fh/2-leftBottom[1]
        return x, y, r

    def _matplotlib_curvedText(self, ax, radianX, y, text, style={}):

        transformation_rate = ax.figure.dpi/72


        curvedStyle =  {"rotation_mode": 'anchor', "transform_rotates_text": True,
                 "ha": 'left', "rotation": 180, "size": 8}
        curvedStyle.update(style)

        wordWdth = textpath.TextPath(
            (0, 0), text, size=curvedStyle['size']).get_extents().width * transformation_rate

        # identify pixel  per degree at this y-position
        pixelpos0 = ax.transData.transform((math.radians(0), y))
        pixelpos1 = ax.transData.transform((math.radians(0.001), y))
        a = pixelpos0[0] - pixelpos1[0]
        b = pixelpos0[1] - pixelpos1[1]
        pixelPerDegree = math.sqrt(a**2+b**2) * 1000
        degreePerPixel = 1/pixelPerDegree
        # set cursor to the beginning of the word (half-word distance from x)
        cursorPosition = radianX + math.radians(wordWdth*degreePerPixel/2)
        letterSpace = 2
        for char in text:
            ax.text(cursorPosition, y, char, **curvedStyle)
            # cursor position
            tempText = textpath.TextPath((0, 0), char, size=curvedStyle['size'])
            letterWidth = tempText.get_extents().width * transformation_rate
            cursorPosition -= math.radians((letterWidth + letterSpace)*degreePerPixel)

class CompassDot:
    value = None  # value on 1:100 scale
    x = None  # position in on x-axis (can differ from value...)
    y = None  # row number
    angle = None   # angle (position) number (on X-axis)
    # how wide is the angle used for this dot. (depending on y position)
    angleWidth = None
    isUpperBoundary = False
    isLowerBoundary = False
    index = None
    compass = None

    def __init__(self, value, x, y, angle, angleWidth, compass):
        self.value = value
        self.x = x
        self.y = y
        self.angle = angle
        self.angleWidth = angleWidth
        self.compass = compass

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
        """ does current slot overlapps with toleranceAngle...
        toleranceAngle: angle of dots at the innerY radius """
        # self.config['toleranceAngle']
        firstRow = self.compass.rowsByY[self.compass.config.get('innery')]
        toleranceAngle = firstRow.slotAngleWidth
        return (angle > self.angle-toleranceAngle and angle <= self.angle+toleranceAngle)


class CompassRow:
    """ Where should the dots be places on each row? """

    y = None  # value on 1:100 scale

    innerMargin = None   # angle (position) number (on X-axis)
    angleWidth = None
    chartAngle = None
    dotList = None
    compass = None

    # calculated
    nofRowSlots = None
    slotAngleWidth = None  # angleWidth of the dots on this row
    gapAngleWidth = None  # angleWidth of the gap between the dots

    def __init__(self, y, compass):
        self.compass = compass
        self.y = y
        self.slotNumbers()

    def slotNumbers(self):
        """ how many dots can be aligned on this y (radius)"""
        yhalf = self.y + (self.compass.config.get('innery')
                          )  # add space in the inner circle
        rowSlotsUnrounded = yhalf*2 * np.pi / 2
        self.nofRowSlots = math.floor(rowSlotsUnrounded)
        gapSum = rowSlotsUnrounded - self.nofRowSlots

        # What is the angle spread for a dot (depending on y). (how big is the piece of cake)

        # calculate gap and slot angles
        if not self.compass.config.get('forceJustification'):
            # dont leave space between the dots
            self.slotAngleWidth = self.compass.config.get(
                'chartAngle') / self.nofRowSlots
            self.gapAngleWidth = 0

        if self.compass.config.get('forceJustification'):
            # leave space between the dots
            nofRowGaps = self.nofRowSlots - 1
            slotGap = gapSum / self.nofRowSlots
            # calculated by: gapAngleWidth = slotAngleWidth * slotGap
            self.slotAngleWidth = self.compass.config.get(
                'chartAngle') / (self.nofRowSlots + nofRowGaps*slotGap)
            self.gapAngleWidth = self.slotAngleWidth*slotGap

        # Check: gapAngleWidth * nofRowGaps + slotAngleWidth * nofRowSlots

    def getXByAngle(self, angle):
        return 1/180*angle * self.compass.config.get('xAxisMax')

    def getDotList(self):
        self.dotList = []

        if self.compass.config['forceJustification']:
            start = self.slotAngleWidth/2

        if not self.compass.config['forceJustification']:
            # Center dot-row on the x-axis
            maxAlignGap = ((self.compass.config.get('chartAngle')) -
                           (self.slotAngleWidth*(self.nofRowSlots)))
            # maxAlignGap*np.random.random()
            alignGap = maxAlignGap * (self.y % 2)
            start = self.slotAngleWidth/2 + alignGap

        slotList = list(
            np.arange(
                start=start,
                stop=self.compass.config.get('chartAngle'),
                step=self.slotAngleWidth+self.gapAngleWidth))[:self.nofRowSlots]
        dotList = list(map(lambda angle: CompassDot(
            value=None,
            x=self.getXByAngle(angle),
            y=self.y,
            angle=angle,
            angleWidth=self.slotAngleWidth,
            compass=self.compass), slotList))
        # dotList = list(map(lambda angle: angle, slotAngleWidth), slotList))
        # self.getXByAngle(slotList[1]) - self.getXByAngle(slotList[0])
        dotList[0].isLowerBoundary = True
        dotList[-1].isUpperBoundary = True
        return dotList
