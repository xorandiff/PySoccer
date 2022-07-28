import pygame, pymunk
from pymunk.vec2d import Vec2d

class PlayerLogic:
    # Sprint boolean
    sprint = False
    
    def __init__(self, position: tuple[float, float], radius: float, walkingSpeed: int, sprintFactor: float, sprintEnergy: float, sprintEnergyDrop: float):
        self.radius = radius
        self.speed = walkingSpeed
        self.sprintFactor = float(sprintFactor)
        self.sideLength = radius * 2
        self.sprintMaxEnergy = sprintEnergy
        self.sprintEnergy = sprintEnergy
        self.sprintEnergyDrop = sprintEnergyDrop
        
        # Create a body for the player with position matching its sprite
        self.body = pymunk.Body()
        self.body.position = position
        
        # Custom velocity function to amend body damping to lower value, 
        # which results in sharper turns while walking
        self.body.velocity_func = lambda body, gravity, damping, dt : pymunk.Body.update_velocity(body, gravity, 0.9, dt)
        
        # Create a circle shape for the player
        self.shape = pymunk.Circle(self.body, self.radius)
        self.shape.friction = 1.0
        self.shape.mass = 2

    def update(self):
        if self.sprintEnergy > 0 and self.sprint:
            self.sprintEnergy -= self.sprintEnergyDrop
            if self.sprintEnergy < 0:
                self.sprintEnergy = 0
        elif self.sprintEnergy < self.sprintMaxEnergy and not self.sprint:
            self.sprintEnergy += self.sprintEnergyDrop
            if self.sprintEnergy > self.sprintMaxEnergy:
                self.sprintEnergy = self.sprintMaxEnergy
        
        # Prevent player from rotating during the game
        self.body.angle = 0

    # Method used for moving the player
    def walk(self, direction: tuple[float, float]):
        v = Vec2d(*direction)
        
        # Set player speed for walk/sprint
        speed = self.speed * self.sprintFactor if self.sprint and self.sprintEnergy > 0 else self.speed
        
        v = Vec2d.scale_to_length(v, speed) 
        
        # Apply impulse to move the player in desired direction
        self.body.apply_impulse_at_local_point(v)


class Player(pygame.sprite.Sprite):
    def __init__(self, centerPosition: tuple[float, float], radius: float):
        pygame.sprite.Sprite.__init__(self)
        
        self.centerPosition = centerPosition
        self.radius = radius
        self.sideLength = radius * 2
        
        # Create player image
        self.image = pygame.transform.scale(pygame.image.load("img/player.png"), (self.sideLength, self.sideLength))
        
        # Set initial player position
        self.rect = self.image.get_rect()
        self.rect.center = centerPosition

    def update(self):
        self.rect.center = self.centerPosition

