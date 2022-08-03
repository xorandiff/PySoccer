from math import floor
import threading, numpy
import pygame, pymunk, pymunk.pygame_util, pygame_gui
from queue import Queue
from multiprocessing import Pipe
from numpy import array
from pymunk.vec2d import Vec2d

from constants import *
from client import ClientProcess
from sound import Sound
from player import Player, PlayerLogic
from ball import Ball, BallLogic
from soccer_field import SoccerField, SoccerFieldLogic
from goal import Goal

class Receiver:
    def __init__(self, conn, queue: Queue):
        self.conn = conn
        self.serverMessages = []
        self.queue = queue

    def _loop(self, queue: Queue):
        while True:
            message = self.conn.recv()
            self.queue.put_nowait(message)

    def start_loop(self):
        threading.Thread(target=self._loop, args=(self.queue,), daemon=True).start()

class Logic:
    def __init__(self, conn, screenSize, fps):
        self.clock = pygame.time.Clock()
        self.conn = conn
        self.timeDelta = 0.0
        self._size = screenSize
        self._fps = fps
        self._playerDirection = array([0, 0])
        self._sound = Sound()
        self._playerWalkingDirections = [False, False, False, False]
        self._opponentWalkingDirections = [False, False, False, False]
        
        self.fps = fps
        self.isNetworkGame = False
        self.playerPosition = array(self._size) / 2 - UNIT_X * FIELD_CIRCLE_RADIUS
        self.opponentPosition = array(self._size) / 2 + UNIT_X * FIELD_CIRCLE_RADIUS
        self.goalkeeperPosition = self._size[0] - GK_STARTPOS_GAP, self._size[1] / 2
        self.events = []
        self.opponentEvents = []
        
        self.soccerField = SoccerFieldLogic(self._size, WALL_THICKNESS)
        self.player = PlayerLogic(self.playerPosition, PLAYER_RADIUS, PLAYER_WALKING_SPEED, PLAYER_SPRINT_FACTOR, PLAYER_SPRINT_MAX_ENERGY, PLAYER_SPRINT_ENERGY_DROP)
        self.opponent = PlayerLogic(self.opponentPosition, PLAYER_RADIUS, PLAYER_WALKING_SPEED, PLAYER_SPRINT_FACTOR, PLAYER_SPRINT_MAX_ENERGY, PLAYER_SPRINT_ENERGY_DROP)
        self.goalkeeper = PlayerLogic(self.goalkeeperPosition, PLAYER_RADIUS, PLAYER_WALKING_SPEED, PLAYER_SPRINT_FACTOR, PLAYER_SPRINT_MAX_ENERGY, PLAYER_SPRINT_ENERGY_DROP)
        self.ball = BallLogic(array(self._size) / 2, BALL_RADIUS, COLLISION_TYPE_BALL)
        self.leftGoal = Goal(GOAL_SIZE, (GOAL_POST_BORDER_GAP + GOAL_WIDTH / 2, SCREEN_HEIGHT / 2), 0, GOAL_POST_RADIUS, GOAL_NET_THICKNESS, GOAL_NET_DENSITY, (0, 0, GOAL_NET_NONCOLLISION_LAYERS, 0), (False, False, True, False), COLLISION_TYPE_GOAL_POST)
        self.rightGoal = Goal(GOAL_SIZE, (SCREEN_WIDTH - GOAL_POST_BORDER_GAP - GOAL_WIDTH / 2, SCREEN_HEIGHT / 2), 0, GOAL_POST_RADIUS, GOAL_NET_THICKNESS, GOAL_NET_DENSITY, (GOAL_NET_NONCOLLISION_LAYERS, 0, 0, 0), (True, False, False, False), COLLISION_TYPE_GOAL_POST)
        self.goals = [ self.leftGoal, self.rightGoal ]
        self.goalSpaceObjects = self.leftGoal.spaceObjects + self.rightGoal.spaceObjects
        
        self.space = pymunk.Space(threaded=True)
        self.space.damping = SPACE_DAMPING
        self.space.collision_slop = SPACE_COLLISION_SLOP
        
        # Add PyMunk shapes and bodies into space
        self.space.add(self.player.body, self.player.shape, self.opponent.body, self.opponent.shape, self.goalkeeper.body, self.goalkeeper.shape, self.ball.body, self.ball.shape, *self.soccerField.walls, *self.goalSpaceObjects)
        
        postCollisionHandler = self.space.add_collision_handler(COLLISION_TYPE_BALL, COLLISION_TYPE_GOAL_POST)
        postCollisionHandler.begin = self.goal_post_hit
        
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
            v = v.scale_to_length(1.0)
            
            player.sprint = False
            if playerBallDistance <= GK_MIN_APPROACH_DISTANCE + PLAYER_RADIUS + BALL_RADIUS:
                player.sprint = True

            player.walk(v.int_tuple)
        else:
            baseDistance = Vec2d.get_distance(player.body.position, Vec2d(*GK_RIGHT_STARTPOS))
            if (baseDistance > 10):
                v = Vec2d(*GK_RIGHT_STARTPOS) - Vec2d(*player.body.position)
                v = v.scale_to_length(1.0)
                player.walk(v.int_tuple)
    
    def _loop(self):
        while True:
            if len(self.events):
                with self.lock:
                    event = self.events.pop(0)
                
                if event.type in [pygame.KEYDOWN, pygame.KEYUP]:
                    key = event.key
                    
                    if self.isNetworkGame:
                        self.conn.send(f"{event.type}_{event.key} ")
                    
                    if key in [pygame.K_LEFT, pygame.K_a]:
                        self._playerWalkingDirections[0] = event.type == pygame.KEYDOWN
                    if key in [pygame.K_RIGHT, pygame.K_d]:
                        self._playerWalkingDirections[1] = event.type == pygame.KEYDOWN
                    if key in [pygame.K_UP, pygame.K_w]:
                        self._playerWalkingDirections[2] = event.type == pygame.KEYDOWN
                    if key in [pygame.K_DOWN, pygame.K_s]:
                        self._playerWalkingDirections[3] = event.type == pygame.KEYDOWN
                        
                    # Set player sprint movement if left shift is pressed
                    if key == pygame.K_LSHIFT:
                        self.player.sprint = event.type == pygame.KEYDOWN
                
                    if event.type == pygame.KEYDOWN:
                        if key == pygame.K_m:
                            self._sound.toggleMute()
                        
                        # Kick the ball if SPACE is pressed
                        if key == pygame.K_SPACE:
                            self.ballKick(self.player)
            
            if self._playerWalkingDirections[0]:
                self.player.walk(-UNIT_X)
            if self._playerWalkingDirections[1]:
                self.player.walk(UNIT_X)
            if self._playerWalkingDirections[2]:
                self.player.walk(-UNIT_Y)
            if self._playerWalkingDirections[3]:
                self.player.walk(UNIT_Y)
                
            if self.isNetworkGame:
                if len(self.opponentEvents):
                    with self.lock:
                        event = self.opponentEvents.pop(0)
                    eventList = event.split("_")
                    eventType = int(eventList[0])
                    key = int(eventList[1])
                    
                    if key == pygame.K_SPACE and eventType == pygame.KEYDOWN:
                        self.ballKick(self.opponent)
                    
                    if key in [pygame.K_LEFT, pygame.K_a]:
                        self._opponentWalkingDirections[0] = eventType == pygame.KEYDOWN
                    if key in [pygame.K_RIGHT, pygame.K_d]:
                        self._opponentWalkingDirections[1] = eventType == pygame.KEYDOWN
                    if key in [pygame.K_UP, pygame.K_w]:
                        self._opponentWalkingDirections[2] = eventType == pygame.KEYDOWN
                    if key in [pygame.K_DOWN, pygame.K_s]:
                        self._opponentWalkingDirections[3] = eventType == pygame.KEYDOWN
                
                if self._opponentWalkingDirections[0]:
                    self.opponent.walk(-UNIT_X)
                if self._opponentWalkingDirections[1]:
                    self.opponent.walk(UNIT_X)
                if self._opponentWalkingDirections[2]:
                    self.opponent.walk(-UNIT_Y)
                if self._opponentWalkingDirections[3]:
                    self.opponent.walk(UNIT_Y)
            
            self.player.update()
            self.opponent.update()
            self.goalkeeper.update()
            self.goalkeeperAi(self.goalkeeper, self.rightGoal)
            
            self.space.step(1 / self._fps)
            self.timeDelta = self.clock.tick(self._fps) / 1000.0
            self.fps = self.clock.get_fps()
            
    def start_loop(self):
        threading.Thread(target=self._loop, daemon=True).start()

class Game:
    def __init__(self, conn):
        pygame.display.set_caption(WINDOW_TITLE)
        
        self.conn = conn
        self.serverMessagesQueue = Queue()
        self.receiver = Receiver(conn, self.serverMessagesQueue)
        self.isNetworkGame = False
        self.isConnected = False
        
        self.ping = 0
        self.pingTimeMark = 0
        
        self.logic = Logic(conn, SCREEN_SIZE, FPS)
        self.running = True
        self.gameInProgress = False
        self.screen = pygame.display.set_mode(SCREEN_SIZE, pygame.SCALED)
        self.manager = pygame_gui.UIManager(SCREEN_SIZE, 'theme.json')
        self.area = pygame.display.get_surface().get_rect()
        self.clock = pygame.time.Clock()
        self.isTeamLeft = True

        self.vs_ai_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((UI_BUTTON_LEFT, UI_BUTTON_TOP), UI_BUTTON_SIZE), text='Play against computer', manager=self.manager)
        self.vs_human_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((UI_BUTTON_LEFT, UI_BUTTON_TOP + UI_BUTTON_GAP), UI_BUTTON_SIZE), text='Play against human', manager=self.manager)
        self.vs_human_button.disable()

        self.menu = [self.vs_ai_button, self.vs_human_button]
        
        self.debugPanel = pygame_gui.elements.UIPanel(relative_rect=pygame.Rect((0, 0), (SCREEN_WIDTH, 50)), starting_layer_height=1, manager=self.manager)
        self.debugText = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((0, 0), (SCREEN_WIDTH, 50)), text="", container=self.debugPanel, parent_element=self.debugPanel, manager=self.manager)
        self.debugPanel.hide()
        
        # Initialize game objects
        self.soccer_field = SoccerField(GRASS_TILE_SIZE, FIELD_CIRCLE_RADIUS, FIELD_LINE_WIDTH)
        self.leftGoal = Goal(GOAL_SIZE, tuple(self.area.midleft + UNIT_X * GOAL_CENTER_GAP), 0, GOAL_POST_RADIUS, GOAL_NET_THICKNESS, GOAL_NET_DENSITY, (0, 0, GOAL_NET_NONCOLLISION_LAYERS, 0), (False, False, True, False), COLLISION_TYPE_GOAL_POST)
        self.rightGoal = Goal(GOAL_SIZE, tuple(self.area.midright - UNIT_X * GOAL_CENTER_GAP), 0, GOAL_POST_RADIUS, GOAL_NET_THICKNESS, GOAL_NET_DENSITY, (GOAL_NET_NONCOLLISION_LAYERS, 0, 0, 0), (True, False, False, False), COLLISION_TYPE_GOAL_POST)
        self.goals = [ self.leftGoal, self.rightGoal ]
        self.goalSprites = [ goal.sprites for goal in self.goals ]
        
        self.players = [
            Player(self.area.center - UNIT_X * FIELD_CIRCLE_RADIUS, PLAYER_RADIUS),
            Player(self.area.midright - UNIT_X * GK_STARTPOS_GAP, PLAYER_RADIUS),
            Player(self.area.center + UNIT_X * FIELD_CIRCLE_RADIUS, PLAYER_RADIUS)
        ]
        self.ball = Ball(self.area.center, BALL_RADIUS)
        self.player = self.players[0]
        self.goalkeeper = self.players[1]
        self.opponent = self.players[2]

        # Create sprite group containing all game sprites
        self.allSprites = pygame.sprite.RenderPlain(self.soccer_field, self.ball, *self.players, *self.goalSprites)

    def hideMenu(self):
        for item in self.menu:
            item.hide()
            
    def showMenu(self):
        for item in self.menu:
            item.show()
            
    def toggleDebugInfo(self):
        if self.debugPanel.visible:
            self.debugPanel.hide()
        else:
            self.debugPanel.show()
            
    def newGame(self):
        self.gameInProgress = True
        self.hideMenu()
        
    def endGame(self):
        self.isNetworkGame = False
        with self.logic.lock:
            self.logic.isNetworkGame = False
        self.gameInProgress = False
        self.showMenu()
    
    def start(self):
        self.logic.start_loop()
        self.receiver.start_loop()
        
        timer = 0
        
        # Game loop
        while self.running:
            # Get server messages stored in queue
            if not self.serverMessagesQueue.empty():
                serverMessage = self.serverMessagesQueue.get()
                
                if serverMessage in ["JOINED_1", "JOINED_2"]:
                    if serverMessage == "JOINED_2":
                        self.isTeamLeft = False
                        self.player = self.opponent
                        self.opponent = self.players[0]
                        with self.logic.lock:
                            t = self.logic.player
                            self.logic.player = self.logic.opponent
                            self.logic.opponent = t
                    self.isNetworkGame = True
                    with self.logic.lock:
                        self.logic.isNetworkGame = True
                    self.newGame()
                elif serverMessage == "LEFT":
                    self.endGame()
                elif serverMessage == "PONG":
                    self.ping = pygame.time.get_ticks() - self.pingTimeMark
                elif "_" in serverMessage:
                    for event in serverMessage.split(" "):
                        if "_" in event:
                            with self.logic.lock:
                                self.logic.opponentEvents.append(event)
                elif serverMessage == "CONNECTED":
                    self.isConnected = True
                    self.vs_human_button.enable()
                elif serverMessage == "DISCONNECTED":
                    self.isConnected = False
                    self.vs_human_button.disable()
                
                self.serverMessagesQueue.task_done()
            
            for event in pygame.event.get():
                # Send information about event to pymunk thread
                if self.gameInProgress:
                    with self.logic.lock:
                        self.logic.events.append(event)
                
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    key = event.key
                    # Toogle fullscreen is CTRL+F is pressed
                    if key == pygame.K_f and (pygame.key.get_mods() & pygame.KMOD_LCTRL):
                        pygame.display.toggle_fullscreen()
                    
                    # Toggle debug information
                    if key == pygame.K_F1:
                        self.toggleDebugInfo()
                elif event.type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.vs_ai_button:
                        self.newGame()
                    elif event.ui_element == self.vs_human_button:
                        self.vs_human_button.set_text("Finding player...")
                        self.vs_human_button.disable()
                        
                        self.conn.send("JOIN")
                
                self.manager.process_events(event)
                
            with self.logic.lock:
                logicFPS = floor(self.logic.fps)
            
            # Adjust rendering graphics to logic render time
            timeDelta = self.clock.tick(logicFPS) / 1000.0
            
            timer += timeDelta
            
            if timer >= 1:
                self.pingTimeMark = pygame.time.get_ticks()
                self.conn.send("PING")
                timer = 0
                                    
            # Read sprite new positions computed by pymunk from physics thread
            with self.logic.lock:
                self.player.centerPosition = self.logic.player.body.position
                self.opponent.centerPosition = self.logic.opponent.body.position
                self.goalkeeper.centerPosition = self.logic.goalkeeper.body.position
                
                self.ball.centerPosition = self.logic.ball.body.position
                self.ball.angle = -numpy.degrees(self.logic.ball.body.angle)
                
                for sprite, body in zip(self.leftGoal.sprites + self.rightGoal.sprites, self.logic.leftGoal.bodies + self.logic.rightGoal.bodies):
                    sprite.positionCenter = body.position
                    sprite.angle = -numpy.degrees(body.angle)
                
            self.allSprites.update()
            self.manager.update(timeDelta)
            
            self.allSprites.draw(self.screen)
            self.manager.draw_ui(self.screen)
            
            self.debugText.set_text(f"Current FPS/Default FPS: {logicFPS} / {FPS}, Ping {self.ping}ms")
            
            """ # Draw debug images
            options = pymunk.pygame_util.DrawOptions(self.screen)
            with self.logic.lock:
                self.logic.space.debug_draw(options) """

            pygame.display.flip()
        
        pygame.time.wait(int(1000 / FPS))
        pygame.quit()
        quit()

if __name__ == "__main__":
    gameConn, clientConn = Pipe()
    
    game = Game(gameConn)
    client = ClientProcess(clientConn)
    
    client.start()
    game.start()