# COLORS (r, g, b)
import pygame
import os

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARKGREY = (40, 40, 40)
LIGHTGREY = (100, 100, 100)
GREEN = (0, 255, 0)
DARKGREEN = (0, 200, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BGCOLOUR = DARKGREY

# game settings
TILESIZE = 32
ROWS = 15
COLS = 25
WIDTH = TILESIZE * COLS
HEIGHT = TILESIZE * ROWS
FPS = 60
TITLE = "Minesweeper Clone"

# Abilities
DETECT_AVAILABLE = 3

tile_numbers = []
for i in range(1, 9):
    tile_numbers.append(pygame.transform.scale(pygame.image.load(os.path.join("assets", f"Tile{i}.png")), (TILESIZE, TILESIZE)))

font_path = os.path.join("assets", "RobotoRemix.ttf")
tile_empty = pygame.transform.scale(pygame.image.load(os.path.join("assets", "TileEmpty.png")), (TILESIZE, TILESIZE))
tile_exploded = pygame.transform.scale(pygame.image.load(os.path.join("assets", "TileExploded.png")), (TILESIZE, TILESIZE))
tile_flag = pygame.transform.scale(pygame.image.load(os.path.join("assets", "TileFlag.png")), (TILESIZE, TILESIZE))
tile_mine = pygame.transform.scale(pygame.image.load(os.path.join("assets", "TileMine.png")), (TILESIZE, TILESIZE))
tile_unknown = pygame.transform.scale(pygame.image.load(os.path.join("assets", "TileUnknown.png")), (TILESIZE, TILESIZE))
tile_not_mine = pygame.transform.scale(pygame.image.load(os.path.join("assets", "TileNotMine.png")), (TILESIZE, TILESIZE))

# Button styling
BUTTON_COLOUR = (70, 70, 70)
BUTTON_HOVER = (100, 100, 100)
BUTTON_TEXT = WHITE
UNDO_BUTTON_WIDTH = 100
UNDO_BUTTON_HEIGHT = 40
UNDO_BUTTON_X = WIDTH // 2 - UNDO_BUTTON_WIDTH // 2
UNDO_BUTTON_Y = HEIGHT + 20


# Difficulty 
DIFFICULTY = "MEDIUM"   # default

DIFFICULTY_MINES = {
    "EASY": 20,
    "MEDIUM": 50,
    "HARD": 100,
}

def get_mine_amount():
    return DIFFICULTY_MINES.get(DIFFICULTY, 50)
