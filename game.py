import threading, time, numpy
import pygame, pymunk, pymunk.pygame_util, pygame_gui
from numpy import array
from pymunk.vec2d import Vec2d

from constants import *
from client import ClientProcess
from sound import Sound
from player import Player, PlayerLogic
from ball import Ball, BallLogic
from soccer_field import SoccerField, SoccerFieldLogic
from goal import Goal

class Logic:
    def __init__(self, screenSize, fps):
        self._size = screenSize
        self._fps = fps
        self._playerDirection = array([0, 0])
        self._sound = Sound()
        self._walkingDirections = [False, False, False, False]
        
        self.playerPosition = array(self._size) / 2 - UNIT_X * FIELD_CIRCLE_RADIUS
        self.goalkeeperPosition = self._size[0] - GK_STARTPOS_GAP, self._size[1] / 2
        self.events = []
        
        self.soccerField = SoccerFieldLogic(self._size, WALL_THICKNESS)
        self.player = PlayerLogic(self.playerPosition, PLAYER_RADIUS, PLAYER_WALKING_SPEED, PLAYER_SPRINT_FACTOR, PLAYER_SPRINT_MAX_ENERGY, PLAYER_SPRINT_ENERGY_DROP)
        self.goalkeeper = PlayerLogic(self.goalkeeperPosition, PLAYER_RADIUS, PLAYER_WALKING_SPEED, PLAYER_SPRINT_FACTOR, PLAYER_SPRINT_MAX_ENERGY, PLAYER_SPRINT_ENERGY_DROP)
        self.ball = BallLogic(array(self._size) / 2, BALL_RADIUS, COLLISION_TYPE_BALL)
        self.leftGoal = Goal(GOAL_SIZE, (GOAL_POST_BORDER_GAP + GOAL_WIDTH / 2, SCREEN_HEIGHT / 2), 0, GOAL_POST_RADIUS, GOAL_NET_THICKNESS, GOAL_NET_DENSITY, (0, 0, GOAL_NET_NONCOLLISION_LAYERS, 0), (False, False, True, False), COLLISION_TYPE_GOAL_POST)
        self.rightGoal = Goal(GOAL_SIZE, (SCREEN_WIDTH - GOAL_POST_BORDER_GAP - GOAL_WIDTH / 2, SCREEN_HEIGHT / 2), 0, GOAL_POST_RADIUS, GOAL_NET_THICKNESS, GOAL_NET_DENSITY, (GOAL_NET_NONCOLLISION_LAYERS, 0, 0, 0), (True, False, False, False), COLLISION_TYPE_GOAL_POST)
        self.goals = [ self.leftGoal, self.rightGoal ]
        self.goalSpaceObjects = self.leftGoal.spaceObjects + self.rightGoal.spaceObjects
        
        self.space = pymunk.Space()
        self.space.damping = SPACE_DAMPING
        self.space.collision_slop = SPACE_COLLISION_SLOP
        
        # Add PyMunk shapes and bodies into space
        self.space.add(self.player.body, self.player.shape, self.goalkeeper.body, self.goalkeeper.shape, self.ball.body, self.ball.shape, *self.soccerField.walls, *self.goalSpaceObjects)
        
        self.lock = threading.Lock()
        
    def ballKick(self, player: PlayerLogic):
        # Get distance between center points of player and ball
        playerBallDistance = Vec2d.get_distance(player.body.position, self.ball.body.position)
        
        # Check if player is in required minimum distance from the ball
        if playerBallDistance < KICK_MIN_DISTANCE:
            # Reset ball angle before the kick, so that ball angle does not 
            # interfere with kick force vector
            self.ball.body.angle = 0
            
            # Compute approximate ratio of player current speed to maximal
            forceScalingFactor = player.body.velocity.length / PLAYER_APPROX_MAX_SPEED
            
            # Ensure that force factor is at least as MIN_KICK_FORCE_FACTOR
            forceScalingFactor = KICK_MIN_FORCE_FACTOR if forceScalingFactor < KICK_MIN_FORCE_FACTOR else forceScalingFactor
            
            # Set kick force in direct proportion with player speed, 
            # so that the higher playert speed is, the stronger is kick
            kickForce = KICK_MAX_FORCE * forceScalingFactor
            
            # Get kick force vector and scale it to kickForce value
            kickForceVector = Vec2d.scale_to_length(self.ball.body.position - player.body.position, kickForce)
            
            self.ball.body.apply_impulse_at_local_point(kickForceVector)
            self.ball.body.angular_velocity += 10
            self._sound.kick()
    
    def goal_post_hit(self, arbiter, space, data):
        if self.ball.body.velocity.length > 300:
            self._sound.goalPostHit()
        return True
    
    def goalkeeperAi(self, player: PlayerLogic, goal: Goal):
        playerBallDistance = Vec2d.get_distance(player.body.position, self.ball.body.position)
        playerGoalDistance = Vec2d.get_distance(player.body.position, goal.rect.center)
        
        # Kick the ball away if it's close enough
        self.ballKick(player)
        
        if playerGoalDistance < GK_MAX_GOAL_DISTANCE and playerBallDistance <= GK_MIN_APPROACH_DISTANCE + GK_MAX_GOAL_DISTANCE:
            v = Vec2d(*self.ball.body.position) - Vec2d(*player.body.position)
            
            player.sprint = False
            if playerBallDistance <= GK_MIN_APPROACH_DISTANCE + PLAYER_RADIUS + BALL_RADIUS:
                player.sprint = True

            player.walk(v.int_tuple)
        else:
            baseDistance = Vec2d.get_distance(player.body.position, Vec2d(*GK_RIGHT_STARTPOS))
            if (baseDistance > 10):
                v = Vec2d(*GK_RIGHT_STARTPOS) - Vec2d(*player.body.position)
                player.walk(v.int_tuple)
    
    def _loop(self):
        while True:
            if len(self.events):
                with self.lock:
                    event = self.events.pop(0)
                
                if event.type in [pygame.KEYDOWN, pygame.KEYUP]:
                    key = event.key
                    
                    if key in [pygame.K_LEFT, pygame.K_a]:
                        self._walkingDirections[0] = event.type == pygame.KEYDOWN
                    if key in [pygame.K_RIGHT, pygame.K_d]:
                        self._walkingDirections[1] = event.type == pygame.KEYDOWN
                    if key in [pygame.K_UP, pygame.K_w]:
                        self._walkingDirections[2] = event.type == pygame.KEYDOWN
                    if key in [pygame.K_DOWN, pygame.K_s]:
                        self._walkingDirections[3] = event.type == pygame.KEYDOWN
                        
                    # Set player sprint movement if left shift is pressed
                    if key == pygame.K_LSHIFT:
                        self.player.sprint = event.type == pygame.KEYDOWN
                
                    if event.type == pygame.KEYDOWN:
                        if key == pygame.K_m:
                            self._sound.toggleMute()
                        
                        # Kick the ball if SPACE is pressed
                        if key == pygame.K_SPACE:
                            self.ballKick(self.player)
            
            if self._walkingDirections[0]:
                self.player.walk(-UNIT_X)
            if self._walkingDirections[1]:
                self.player.walk(UNIT_X)
            if self._walkingDirections[2]:
                self.player.walk(-UNIT_Y)
            if self._walkingDirections[3]:
                self.player.walk(UNIT_Y)
            
            self.player.update()
            self.goalkeeperAi(self.goalkeeper, self.rightGoal)
            
            self.space.step(1 / self._fps)
            time.sleep(1 / self._fps)
            
    def start_loop(self):
        threading.Thread(target=self._loop, daemon=True).start()

class Game:
    def __init__(self):
        pygame.display.set_caption(WINDOW_TITLE)
        
        self.logic = Logic(SCREEN_SIZE, FPS)
        self.running = True        
        self.screen = pygame.display.set_mode(SCREEN_SIZE, pygame.SCALED)
        self.manager = pygame_gui.UIManager(SCREEN_SIZE, 'theme.json')
        self.area = pygame.display.get_surface().get_rect()
        self.clock = pygame.time.Clock()

        self.vs_ai_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((UI_BUTTON_LEFT, UI_BUTTON_TOP), UI_BUTTON_SIZE), text='Play against computer', manager=self.manager)
        self.vs_human_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((UI_BUTTON_LEFT, UI_BUTTON_TOP + UI_BUTTON_GAP), UI_BUTTON_SIZE), text='Play against human', manager=self.manager)

        self.menu = [self.vs_ai_button, self.vs_human_button]

        # Initialize game objects
        self.soccer_field = SoccerField(GRASS_TILE_SIZE, FIELD_CIRCLE_RADIUS, FIELD_LINE_WIDTH)
        self.leftGoal = Goal(GOAL_SIZE, self.area.midleft + UNIT_X * GOAL_CENTER_GAP, 0, GOAL_POST_RADIUS, GOAL_NET_THICKNESS, GOAL_NET_DENSITY, (0, 0, GOAL_NET_NONCOLLISION_LAYERS, 0), (False, False, True, False), COLLISION_TYPE_GOAL_POST)
        self.rightGoal = Goal(GOAL_SIZE, self.area.midright - UNIT_X * GOAL_CENTER_GAP, 0, GOAL_POST_RADIUS, GOAL_NET_THICKNESS, GOAL_NET_DENSITY, (GOAL_NET_NONCOLLISION_LAYERS, 0, 0, 0), (True, False, False, False), COLLISION_TYPE_GOAL_POST)
        self.goals = [ self.leftGoal, self.rightGoal ]
        self.goalSprites = [ goal.sprites for goal in self.goals ]
        
        self.players = [
            Player(self.area.center - UNIT_X * FIELD_CIRCLE_RADIUS, PLAYER_RADIUS),
            Player(self.area.midright - UNIT_X * GK_STARTPOS_GAP, PLAYER_RADIUS)
        ]
        self.ball = Ball(self.area.center, BALL_RADIUS)
        self.player = self.players[0]
        self.goalkeeper = self.players[1]

        # Create sprite group containing all game sprites
        self.allSprites = pygame.sprite.RenderPlain((self.soccer_field, self.ball, *self.players, *self.goalSprites))

    def hideMenu(self):
        for item in self.menu:
            item.hide()
            
    def showMenu(self):
        for item in self.menu:
            item.show()
    
    def start(self):
        #time.sleep(0.5)
        self.logic.start_loop()
        # Game loop
        while self.running:            
            for event in pygame.event.get():
                # Send information about event to pymunk thread
                with self.logic.lock:
                    self.logic.events.append(event)
                
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    key = event.key
                    
                    # Toogle fullscreen is CTRL+F is pressed
                    if key == pygame.K_f and (pygame.key.get_mods() & pygame.KMOD_LCTRL):
                        pygame.display.toggle_fullscreen()
                elif event.type == pygame.KEYUP:
                    # Send information about keydown event to pymunk thread
                    with self.logic.lock:
                        self.logic.events.append(event)
                elif event.type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.vs_ai_button:
                        self.hideMenu()
                    elif event.ui_element == self.vs_human_button:
                        self.vs_human_button.set_text("Finding player...")
                        self.vs_human_button.disable()
                
                self.manager.process_events(event)
            
            time_delta = self.clock.tick(FPS) / 1000.0
            
            # Read sprite new positions computed by pymunk from physics thread
            with self.logic.lock:
                self.player.centerPosition = self.logic.player.body.position
                self.goalkeeper.centerPosition = self.logic.goalkeeper.body.position
                
                self.ball.centerPosition = self.logic.ball.body.position
                self.ball.angle = -numpy.degrees(self.logic.ball.body.angle)
                
                for sprite, body in zip(self.leftGoal.sprites + self.rightGoal.sprites, self.logic.leftGoal.bodies + self.logic.rightGoal.bodies):
                    sprite.positionCenter = body.position
                    sprite.angle = -numpy.degrees(body.angle)
                
            self.allSprites.update()
            self.manager.update(time_delta)
            
            self.allSprites.draw(self.screen)
            self.manager.draw_ui(self.screen)
            
            # Draw debug images
            options = pymunk.pygame_util.DrawOptions(self.screen)
            """ with self.logic.lock: """
            """     self.logic.space.debug_draw(options) """

            pygame.display.flip()
        
        pygame.time.wait(int(1000 / FPS))
        pygame.quit()
        quit()

if __name__ == "__main__":
    game = Game()
    client = ClientProcess()
    
    client.start()
    game.start()