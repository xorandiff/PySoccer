import pygame, pymunk

class SoccerFieldLogic:
    def __init__(self, screenSize: tuple[int, int], wallThickness: float):
        self.SCREEN_WIDTH, self.SCREEN_HEIGHT = screenSize
        wallBody = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.walls = [
            wallBody,
            
            # Bottom wall
            pymunk.Segment(wallBody, (0, self.SCREEN_HEIGHT), (self.SCREEN_WIDTH, self.SCREEN_HEIGHT), wallThickness),
            
            # Top wall
            pymunk.Segment(wallBody, (0, 0), (self.SCREEN_WIDTH, 0), wallThickness),
            
            # Left wall
            pymunk.Segment(wallBody, (0, 0), (0, self.SCREEN_HEIGHT), wallThickness),
            
            # Right wall
            pymunk.Segment(wallBody, (self.SCREEN_WIDTH, 0), (self.SCREEN_WIDTH, self.SCREEN_HEIGHT), wallThickness)
        ]

        for wall in self.walls:
            wall.elasticity = 1

class SoccerField(pygame.sprite.Sprite):
    def __init__(self, grassTileSize: tuple[int, int], circleRadius: float, lineWidth: float):
        pygame.sprite.Sprite.__init__(self)
        
        self.SCREEN_WIDTH, self.SCREEN_HEIGHT = pygame.display.get_surface().get_size()
        self.CIRCLE_RADIUS = circleRadius
        self.LINE_WIDTH = lineWidth
        
        self.grassTileSize = self.grassTileWidth, self.grassTileHeight = grassTileSize
                        
        # Compute horizontal and vertical amount of grass tiles to draw
        self.tiles_amount_x = int(self.SCREEN_WIDTH / 50) + 1
        self.tiles_amount_y = int(self.SCREEN_HEIGHT / 50) + 1
        
        # Set sprite surface as game surface
        self.image = pygame.display.get_surface()
                
        # Set sprite rect as game surface rect
        self.rect = self.image.get_rect()
        
        # Create scaled grass tile image
        self.grass_tile_image = pygame.transform.scale(pygame.image.load("img/grass.jpg"), self.grassTileSize)
        
    def update(self):
        # Draw positioned grass tile images to fill the screen size
        for i in range(self.tiles_amount_x):
            for j in range(self.tiles_amount_y):
                position = i * self.grassTileWidth, j * self.grassTileHeight
                self.image.blit(self.grass_tile_image, position)
        
        pygame.draw.circle(self.image, (255, 255, 255), (self.SCREEN_WIDTH / 2, self.SCREEN_HEIGHT / 2), 5)
        pygame.draw.rect(self.image, (255, 255, 255), pygame.Rect(self.SCREEN_WIDTH / 2 - self.LINE_WIDTH / 2, 0, self.LINE_WIDTH, self.SCREEN_HEIGHT))
        pygame.draw.circle(self.image, (255, 255, 255), (self.SCREEN_WIDTH / 2, self.SCREEN_HEIGHT / 2), self.CIRCLE_RADIUS, self.LINE_WIDTH)