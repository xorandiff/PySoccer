import pygame, pymunk, pymunk.pygame_util
from pygame.rect import Rect

class GoalPostLogic:
    def __init__(self, positionCenter: tuple[float, float], radius: float, collisionType: int):
        # Initialize the goal post rectangle at given position
        self.body = pymunk.Body(body_type=pymunk.Body.STATIC, moment=1.0)
        
        self.shape = pymunk.Circle(self.body, radius, positionCenter)
        self.shape.friction = 1.0
        self.shape.mass = 20
        self.shape.elasticity = 1
        self.shape.collision_type = collisionType
        self.shape.filter = pymunk.ShapeFilter(categories=0b1, mask=pymunk.ShapeFilter.ALL_MASKS() ^ 0b1)

class GoalPost(pygame.sprite.Sprite):    
    def __init__(self, positionCenter: tuple[float, float], radius: float):
        pygame.sprite.Sprite.__init__(self)
        
        self.positionCenter = positionCenter
        self.radius = radius
        self.sideLength = 2 * self.radius
        self.angle = 0
        
        # Initialize the goal post surface
        self.image = pygame.transform.scale(pygame.image.load("img/goal_post.png"), (self.sideLength, self.sideLength))
        
        self.rect: Rect = self.image.get_rect()
        self.rect.center = tuple(map(int, self.positionCenter))

    def update(self):
        pass