import pygame, pymunk
import numpy as np
from numpy.typing import ArrayLike
from pygame.rect import Rect
class PlayerLogic:
    # Sprint boolean
    sprint = False
    
    def __init__(self, position: ArrayLike, radius: float, walkingSpeed: float, sprintFactor: float, sprintEnergy: float, sprintEnergyDrop: float):
        self.radius = radius
        self.speed = walkingSpeed
        self.sprintFactor = float(sprintFactor)
        self.sideLength = radius * 2
        self.sprintMaxEnergy = sprintEnergy
        self.sprintEnergy = sprintEnergy
        self.sprintEnergyDrop = sprintEnergyDrop
        
        # Create a body for the player with position matching its sprite
        self.body = pymunk.Body()
        self.body.position = tuple(np.array(position))
        
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
    def walk(self, direction: ArrayLike):        
        # Set player speed for walk/sprint
        speed = self.speed * self.sprintFactor if self.sprint and self.sprintEnergy > 0 else self.speed
        # Apply impulse to move the player in desired direction
        self.body.apply_impulse_at_local_point(tuple(np.array(direction) * speed))


class Player(pygame.sprite.Sprite):
    def __init__(self, centerPosition: ArrayLike, radius: float):
        pygame.sprite.Sprite.__init__(self)
        
        self.centerPosition = centerPosition
        self.radius = radius
        self.sideLength = radius * 2
        
        # Create player image
        self.image = pygame.transform.scale(pygame.image.load("img/player.png"), (self.sideLength, self.sideLength))
        
        # Set initial player position
        self.rect: Rect = self.image.get_rect()
        self.rect.center = tuple(np.array(centerPosition))

    def update(self):
        self.rect.center = tuple(np.array(self.centerPosition))

