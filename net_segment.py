import pygame, pymunk
from pygame.rect import Rect
from pymunk.vec2d import Vec2d

class NetSegmentLogic:
    def __init__(self, start: tuple[float, float], end: tuple[float, float], thickness, angle = 0.):
        self.start, self.end = start, end
        self.size = self.width, self.height = Vec2d.get_distance(Vec2d(*start), Vec2d(*end)), thickness * 2
        
        self.body = pymunk.Body(moment=3.0)
        self.body.position = self.start
        self.body.angle = angle
        
        self.shape = pymunk.Segment(self.body, (-self.width / 2, 0), (self.width / 2, 0), thickness)
        self.shape.friction = 1.0
        self.shape.mass = 0.3
        self.shape.elasticity = 0.8
        self.shape.filter = pymunk.ShapeFilter(categories=0b1, mask=pymunk.ShapeFilter.ALL_MASKS() ^ 0b1)

"""
Net segment class for handling PyGame sprite and 
PyMunk physics. NetSegment objects may impact heavily 
on performance, if goal nets are very dense.
"""
class NetSegment(pygame.sprite.Sprite):
    def __init__(self, positionCenter: tuple[float, float], size: tuple[float, float], angle = 0):
        pygame.sprite.Sprite.__init__(self)
        
        self.positionCenter = positionCenter
        self.angle = angle
        self.size = self.width, self.height = size
                
        self.image = pygame.Surface((self.width, self.height))
        self.image.set_colorkey((0, 0, 0))
        self.image.fill((255, 255, 255))
        
        self.image_copy = self.image.copy()
        self.image_copy.set_colorkey((0, 0, 0))
        self.image_copy.fill((255, 255, 255))
        
        self.rect: Rect = self.image.get_rect()
        self.rect.center = tuple(map(int, self.positionCenter))
        
    def update(self):
        self.rect.center = tuple(map(int, self.positionCenter))
        center = self.rect.center
        self.image = pygame.transform.rotate(self.image_copy, self.angle)
        self.rect = self.image.get_rect()
        self.rect.center = center