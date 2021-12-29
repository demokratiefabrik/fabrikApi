import numpy as np
import math

class Dot:
    value = None  # value on 1:100 scale
    x = None  # position in on x-axis (can differ from value...)
    y = None # row number
    angle = None   # angle (position) number (on X-axis)
    angleWidth = None # how wide is the angle used for this dot. (depending on y position)

    def __init__(self, value, x, y, angle, angleWidth):
        self.value = value
        self.x = x 
        self.y = y
        self.angle = angle
        self.angleWidth = angleWidth

    def overlapping(self, angle):
        """ does current slot overlapps with given angle..."""
        # TODO <=
        return (angle > self.angle-self.angleWidth/2 and angle <= self.angle+self.angleWidth/2)


    def overlappingWithTolerance(self, angle):
        """ does current slot overlapps with given angle...
        Tolerance: 40 degree """
        # TODO 
        toleranceAngle = 5
        return (angle > self.angle-toleranceAngle and angle <= self.angle+toleranceAngle)


class Compass:

    innery = 5
    outery = 20
    # baseline_size = 40
    xAxisMax = 100 # scale from 0 to 100
    # xAxisPixel = 10000 # ridiculus high to enable integer values for all
    maxAngle = 180
    # helper
    ceilingy = 0
    # slots = []  # free slots...
    dots = []
    slotsByY = {} # free slots...
    dots = []


    def __init__(self):

        # generate angles for baseline (=> innery)
        self.generateRowSlots(self.innery)


    def generateRowSlots(self, y):
        """generate empty slots for new y row"""

        if y > self.outery:
            # maximal y value reached...
            return None

        if y == self.ceilingy:
            # slots for this row are already defined...
            return None

        assert y > self.ceilingy
        assert y >= self.innery

        rowSlots = self.rowSlots(y)
        slotAngleWidth = self.slotAngleWidth(rowSlots)
        
        # TODO: center angles between 0 and 180
        alignGap = (self.maxAngle % rowSlots) / 2  + slotAngleWidth/2
        slotList = list(np.arange(alignGap, self.maxAngle, slotAngleWidth))[:rowSlots]
        dotList = list(map(lambda angle: Dot(None, self.getXByAngle(angle), y, angle, slotAngleWidth), slotList))
        # self.slots.extend(dotList)
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
        return math.floor(self.maxAngle / rowSlots)
    
    def rowSlots(self, y):
        """ how many dots can be aligned on this y (radius)"""
        return math.floor(y**2 * np.pi / 2)

    def getFreeSlot(self, angle, value):
        """ get lowest free slot (on this position). """

        for y in range (self.innery, self.ceilingy+1):
            if y not in self.slotsByY.keys():
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

        raise Warning("cannto allocate all values (Value: %s)" % value)


    def applySlot(self, slot, value):
        slot.value = value
        self.dots.append(slot)
        self.slotsByY[slot.y].remove(slot)
        
        # create slots for row above..
        self.generateRowSlots(slot.y + 1)


    def add(self, value):
        """ add a dot to the plot"""
        assert value in range(0,100)

        y = self.innery
        angle = self.getAngleByX(value)
        return self.getFreeSlot(angle, value)



compass = Compass()

# add a dot into the middle
# compass.add(50)
# compass.add(40)
# compass.add(40)
# compass.add(40)
# compass.dots