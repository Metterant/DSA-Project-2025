import random

import pygame
from settings import *

# types list
# "." -> unknown
# "X" -> mine
# "C" -> clue
# "/" -> empty


class Tile:
    def __init__(self, x, y, image, type, revealed=False, flagged=False):
        self.x, self.y = x * TILESIZE, y * TILESIZE
        self.image = image
        self.type = type
        self.revealed = revealed
        self.flagged = flagged

    def draw(self, board_surface):
        if not self.flagged and self.revealed:
            board_surface.blit(self.image, (self.x, self.y))
        elif self.flagged and not self.revealed:
            board_surface.blit(tile_flag, (self.x, self.y))
        elif not self.revealed:
            board_surface.blit(tile_unknown, (self.x, self.y))

    def __repr__(self):
        return self.type


class Board:
    def __init__(self):
        self.board_surface = pygame.Surface((WIDTH, HEIGHT))
        self.board_list = [
            [Tile(col, row, tile_empty, ".") for col in range(COLS)]
            for row in range(ROWS)
        ]
        self.place_mines()
        self.place_clues()
        self.dug = []

    def place_mines(self):
        for _ in range(AMOUNT_MINES):
            while True:
                row = random.randint(0, ROWS - 1)
                col = random.randint(0, COLS - 1)

                if self.board_list[row][col].type == ".":
                    self.board_list[row][col].image = tile_mine
                    self.board_list[row][col].type = "X"
                    break

    def place_clues(self):
        for row in range(ROWS):
            for col in range(COLS):
                if self.board_list[row][col].type != "X":
                    total_mines = self.check_neighbours(row, col)
                    if total_mines > 0:
                        self.board_list[row][col].image = tile_numbers[total_mines - 1]
                        self.board_list[row][col].type = "C"


    @staticmethod
    def is_inside(row, col):
        return 0 <= row < ROWS and 0 <= col < COLS

    def check_neighbours(self, row, col):
        total_mines = 0
        for row_offset in range(-1, 2):
            for col_offset in range(-1, 2):
                neighbour_row = row + row_offset
                neighbour_col = col + col_offset
                if self.is_inside(neighbour_row, neighbour_col) and self.board_list[neighbour_row][neighbour_col].type == "X":
                    total_mines += 1

        return total_mines

    def draw(self, screen):
        for row_tiles in self.board_list:
            for tile in row_tiles:
                tile.draw(self.board_surface)
        screen.blit(self.board_surface, (0, 0))

    def dig(self, row, col):
        self.dug.append((row, col))
        tile = self.board_list[row][col]
        if tile.type == "X":
            tile.revealed = True
            tile.image = tile_exploded
            return False
        elif tile.type == "C":
            tile.revealed = True
            return True

        tile.revealed = True

        # Recursive call
        for next_row in range(max(0, row - 1), min(ROWS - 1, row + 1) + 1):
            for next_col in range(max(0, col - 1), min(COLS - 1, col + 1) + 1):
                if (next_row, next_col) not in self.dug:
                    self.dig(next_row, next_col)
        return True

    def has_dugged(self, row, col) -> bool:
        return self.board_list[row][col].revealed

    # Return if the selected Tile is a mine
    def reveal(self, row, col) -> bool:
        tile = self.board_list[row][col]
        if tile.type == "X":
            tile.revealed = True
            tile.flagged = False
            return True
        return False

    def display_board(self):
        for row in self.board_list:
            print(row)




