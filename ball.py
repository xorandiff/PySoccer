import pygame, pymunk

class BallLogic:
    def __init__(self, centerPosition, radius: int, collisionType: int):
        # Create a body for the ball with position matching its sprite
        self.body = pymunk.Body(moment=2.0)
        self.body.position = tuple(centerPosition)
        
        # Create a circle shape for the ball
        self.shape = pymunk.Circle(self.body, radius)
        self.shape.friction = 1.0
        self.shape.mass = 1
        self.shape.collision_type = collisionType
        
        # Ball will loose 50% of kinetic energy during collision
        self.shape.elasticity = 0.5

class Ball(pygame.sprite.Sprite):    
    def __init__(self, centerPosition: tuple[int, int], radius: int):
        pygame.sprite.Sprite.__init__(self)
        
        self.centerPosition = centerPosition
        self.radius = radius
        self.angle = 0
        self.sideLength = self.radius * 2
        
        # Create ball image
        self.image = pygame.transform.scale(pygame.image.load("img/ball.png"), (self.sideLength, self.sideLength))
        self.image_copy = self.image.copy()
        
        self.rect = self.image.get_rect()
        self.rect.center = self.centerPosition
    
    def update(self):
        self.rect.center = self.centerPosition
        center = self.rect.center
        self.image = pygame.transform.rotate(self.image_copy, self.angle)
        self.rect = self.image.get_rect()
        self.rect.center = center
        
