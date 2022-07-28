import math, pymunk
from pymunk.constraints import DampedSpring
from goal_post import GoalPost, GoalPostLogic
from net_segment import NetSegment, NetSegmentLogic

"""
Goal class for handling PyGame sprite and 
PyMunk physics
"""
class Goal:
    def __init__(self, size: tuple[int, int], positionCenter: tuple[int, int], angle: int, postRadius: int, netThickness: int, segmentCounts: tuple[int, int], noCollisionLayers: tuple[int, int, int, int], crossbarPinSides: tuple[bool, bool, bool, bool], postCollisionType: int):
        self.size = self.width, self.height = size
        self.center = self.centerX, self.centerY = positionCenter
        self.angle = angle
        self.postRadius = postRadius
        self.netThickness = netThickness
        self.segmentCounts = self.segmentCountX, self.segmentCountY = segmentCounts
        self.noCollisionLayersLeft, self.noCollisionLayersTop, self.noCollisionLayersRight, self.noCollisionLayersBottom = noCollisionLayers
        self.angleX, self.angleY = 0, math.pi / 2
        
        self.stiffnessGap = 0.1 * self.width
        self.segmentLengthX = (self.width - self.stiffnessGap - 4 * self.postRadius) / self.segmentCountX
        self.segmentLengthY = (self.height - 2 * self.stiffnessGap - 4 * self.postRadius) / self.segmentCountY
        
        self.topLeft = self.centerX - self.width / 2, self.centerY - self.height / 2
        self.topRight = self.centerX + self.width / 2, self.centerY - self.height / 2
        self.bottomLeft = self.centerX - self.width / 2, self.centerY + self.height / 2
        self.bottomRight = self.centerX + self.width / 2, self.centerY + self.height / 2
        
        self.postSprites = [
            GoalPost((self.topLeft[0] + self.postRadius, self.topLeft[1] + self.postRadius), self.postRadius),
            GoalPost((self.topRight[0] - self.postRadius, self.topRight[1] + self.postRadius), self.postRadius),
            GoalPost((self.bottomLeft[0] + self.postRadius, self.bottomLeft[1] - self.postRadius), self.postRadius),
            GoalPost((self.bottomRight[0] - self.postRadius, self.bottomRight[1] - self.postRadius), self.postRadius)
        ]
        
        self.postLogics = [
            GoalPostLogic((self.topLeft[0] + self.postRadius, self.topLeft[1] + self.postRadius), self.postRadius, postCollisionType),
            GoalPostLogic((self.topRight[0] - self.postRadius, self.topRight[1] + self.postRadius), self.postRadius, postCollisionType),
            GoalPostLogic((self.bottomLeft[0] + self.postRadius, self.bottomLeft[1] - self.postRadius), self.postRadius, postCollisionType),
            GoalPostLogic((self.bottomRight[0] - self.postRadius, self.bottomRight[1] - self.postRadius), self.postRadius, postCollisionType)
        ]
        
        self.netSegmentSprites = []
        self.netSegmentLogics = []
        self.netJoints = []
        
        segmentRestLength = 0.0
        segmentStiffness = 300
        segmentDamping = 0.7
        
        netLeft = self.topLeft[0] + self.stiffnessGap + 2 * self.postRadius + self.segmentLengthX / 2
        netTop = self.topLeft[1] + self.postRadius - self.netThickness / 2
        segmentGap = self.segmentLengthY + 2 * self.netThickness
        
        netSegmentSpritesX = []
        netSegmentLogicsX = []
        
        netSegmentSpritesY = []
        netSegmentLogicsY = []
        
        # Horizontal segments
        for i in range(self.segmentCountY + 1):
            segmentTop = netTop + i * segmentGap
            segmentStartBase = (netLeft, segmentTop)
            segmentEndBase = (netLeft + self.segmentLengthX, segmentTop)
            
            segmentSprites = []
            segmentLogics = []
            for j in range(self.segmentCountX):
                segmentStart = segmentStartBase[0] + j * self.segmentLengthX, segmentStartBase[1]
                segmentEnd = segmentEndBase[0] + j * self.segmentLengthX, segmentEndBase[1]
                
                netSegmentLogic = NetSegmentLogic(segmentStart, segmentEnd, self.netThickness, self.angleX)
                netSegmentSprite = NetSegment(netSegmentLogic.body.position, netSegmentLogic.size, netSegmentLogic.body.angle)
                if i > 0 and i < self.segmentCountY and (j < self.noCollisionLayersLeft or j > self.segmentCountX - self.noCollisionLayersRight):
                    netSegmentLogic.shape.filter = pymunk.ShapeFilter(mask = 0)
                segmentLogics.append(netSegmentLogic)
                segmentSprites.append(netSegmentSprite)
                
                # Connect adjacent segments
                if j > 0:
                    self.netJoints.append(DampedSpring(segmentLogics[j - 1].body, segmentLogics[j].body, (self.segmentLengthX / 2, 0), (-self.segmentLengthX / 2, 0), segmentRestLength, segmentStiffness, segmentDamping))
           
            netSegmentSpritesX += segmentSprites
            netSegmentLogicsX += segmentLogics
            
        netLeft -= self.segmentLengthX / 2
        netTop += self.postRadius + self.segmentLengthY / 2
        
        # Vertical segments
        for i in range(self.segmentCountY):
            segmentTop = netTop + i * segmentGap
            segmentStartBase = (netLeft, segmentTop)
            segmentEndBase = (netLeft + self.segmentLengthY, segmentTop)
            
            segmentSprites = []
            segmentLogics = []
            for j in range(self.segmentCountX + 1):
                segmentStart = segmentStartBase[0] + j * self.segmentLengthX, segmentStartBase[1]
                segmentEnd = segmentEndBase[0] + j * self.segmentLengthX, segmentEndBase[1]
                
                netSegmentLogic = NetSegmentLogic(segmentStart, segmentEnd, self.netThickness, self.angleY)
                netSegmentSprite = NetSegment(netSegmentLogic.body.position, netSegmentLogic.size, netSegmentLogic.body.angle)
                if j < self.noCollisionLayersLeft or j > self.segmentCountX - self.noCollisionLayersRight:
                    netSegmentLogic.shape.filter = pymunk.ShapeFilter(mask = 0)
                
                segmentLogics.append(netSegmentLogic)
                segmentSprites.append(netSegmentSprite)
                
            netSegmentSpritesY += segmentSprites
            netSegmentLogicsY += segmentLogics
            
            segmentsLength = len(segmentLogics)
            for j in range(segmentsLength):
                if j == segmentsLength - 1:
                    self.netJoints.append(DampedSpring(segmentLogics[j].body, netSegmentLogicsX[i * self.segmentCountX + j - 1].body, (-self.segmentLengthY / 2, 0), (self.segmentLengthX / 2, 0), segmentRestLength, segmentStiffness, segmentDamping))
                    self.netJoints.append(DampedSpring(segmentLogics[j].body, netSegmentLogicsX[(i + 1) * self.segmentCountX + j - 1].body, (self.segmentLengthY / 2, 0), (self.segmentLengthX / 2, 0), segmentRestLength, segmentStiffness, segmentDamping))
                else:
                    self.netJoints.append(DampedSpring(segmentLogics[j].body, netSegmentLogicsX[i * self.segmentCountX + j].body, (-self.segmentLengthY / 2, 0), (-self.segmentLengthX / 2, 0), segmentRestLength, segmentStiffness, segmentDamping))
                    self.netJoints.append(DampedSpring(segmentLogics[j].body, netSegmentLogicsX[(i + 1) * self.segmentCountX + j].body, (self.segmentLengthY / 2, 0), (-self.segmentLengthX / 2, 0), segmentRestLength, segmentStiffness, segmentDamping))
                    
        # Top joints
        self.netJoints.append(DampedSpring(self.postLogics[0].body, netSegmentLogicsX[0].body, self.postSprites[0].rect.midright, (-self.segmentLengthX / 2, 0), segmentRestLength, segmentStiffness, segmentDamping))
        self.netJoints.append(DampedSpring(netSegmentLogicsX[self.segmentCountX - 1].body, self.postLogics[1].body, (self.segmentLengthX / 2, 0), self.postSprites[1].rect.midleft, segmentRestLength, segmentStiffness, segmentDamping))
        
        # Bottom joints
        self.netJoints.append(DampedSpring(self.postLogics[2].body, netSegmentLogicsX[len(netSegmentLogicsX) - self.segmentCountX].body, self.postSprites[2].rect.midright, (-self.segmentLengthX / 2, 0), segmentRestLength, segmentStiffness, segmentDamping))
        self.netJoints.append(DampedSpring(netSegmentLogicsX[len(netSegmentLogicsX) - 1].body, self.postLogics[3].body, (self.segmentLengthX / 2, 0), self.postSprites[3].rect.midleft, segmentRestLength, segmentStiffness, segmentDamping))
        
        # Left joints
        self.netJoints.append(DampedSpring(self.postLogics[0].body, netSegmentLogicsY[0].body, self.postSprites[0].rect.midright, (-self.segmentLengthY / 2, 0), segmentRestLength, segmentStiffness, segmentDamping))
        self.netJoints.append(DampedSpring(netSegmentLogicsY[len(netSegmentLogicsY) - self.segmentCountX - 1].body, self.postLogics[2].body, (self.segmentLengthY / 2, 0), self.postSprites[2].rect.midleft, segmentRestLength, segmentStiffness, segmentDamping))
        
        # Right joints
        self.netJoints.append(DampedSpring(self.postLogics[1].body, netSegmentLogicsY[self.segmentCountX].body, self.postSprites[1].rect.midright, (-self.segmentLengthY / 2, 0), segmentRestLength, segmentStiffness, segmentDamping))
        self.netJoints.append(DampedSpring(netSegmentLogicsY[len(netSegmentLogicsY) - 1].body, self.postLogics[3].body, (self.segmentLengthY / 2, 0), self.postSprites[3].rect.midleft, segmentRestLength, segmentStiffness, segmentDamping))
        
        self.netSegmentSprites += netSegmentSpritesX + netSegmentSpritesY
        self.netSegmentLogics += netSegmentLogicsX + netSegmentLogicsY
        
        self.logics = self.postLogics + self.netSegmentLogics
        self.sprites = self.postSprites + self.netSegmentSprites
        self.bodies = [ x.body for x in self.logics ]
        self.shapes = [ x.shape for x in self.logics ]
        self.spaceObjects = self.bodies + self.shapes + self.netJoints