from constants import *
import pygame
from player import Player, PlayerLogic

class Team:
    def __init__(self, playerCount: int, isLeftSide: bool, hasGoalkeeper: bool):
        self.area = pygame.display.get_surface().get_rect()
        self.players: list[Player] = []
        self.playerLogics: list[PlayerLogic] = []
        
        if playerCount == 1:
            playerPosition = self.area.center - UNIT_X * FIELD_CIRCLE_RADIUS if isLeftSide else self.area.center + UNIT_X * FIELD_CIRCLE_RADIUS
            self.players.append(Player(playerPosition, PLAYER_RADIUS))
            self.playerLogics.append(PlayerLogic(playerPosition, PLAYER_RADIUS, PLAYER_WALKING_SPEED, PLAYER_SPRINT_FACTOR, PLAYER_SPRINT_MAX_ENERGY, PLAYER_SPRINT_ENERGY_DROP))
        elif playerCount == 2:
            playerPosition = self.area.center - UNIT_X * FIELD_CIRCLE_RADIUS if isLeftSide else self.area.center + UNIT_X * FIELD_CIRCLE_RADIUS
            self.players.append(Player(playerPosition, PLAYER_RADIUS))
            self.playerLogics.append(PlayerLogic(playerPosition, PLAYER_RADIUS, PLAYER_WALKING_SPEED, PLAYER_SPRINT_FACTOR, PLAYER_SPRINT_MAX_ENERGY, PLAYER_SPRINT_ENERGY_DROP))
        
        if hasGoalkeeper:
            goalkeeperPosition = self.area.midright - UNIT_X * GK_STARTPOS_GAP if isLeftSide else 2
            self.players.append(Player(goalkeeperPosition, PLAYER_RADIUS))
            self.playerLogics.append(PlayerLogic(goalkeeperPosition, PLAYER_RADIUS, PLAYER_WALKING_SPEED, PLAYER_SPRINT_FACTOR, PLAYER_SPRINT_MAX_ENERGY, PLAYER_SPRINT_ENERGY_DROP))
    
    def setStartPosition(self):
        pass
     
    def update(self):
        for playerLogic in self.playerLogics:
            playerLogic.update()