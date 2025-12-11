import random
import pygame
import settings   # MUST import module, not values

class Tile:
    def __init__(self, x, y, image, type, revealed=False, flagged=False):
        self.x, self.y = x * settings.TILESIZE, y * settings.TILESIZE
        self.image = image
        self.type = type
        self.revealed = revealed
        self.flagged = flagged

    def draw(self, board_surface):
        if not self.flagged and self.revealed:
            board_surface.blit(self.image, (self.x, self.y))
        elif self.flagged and not self.revealed:
            board_surface.blit(settings.tile_flag, (self.x, self.y))
        elif not self.revealed:
            board_surface.blit(settings.tile_unknown, (self.x, self.y))

    def __repr__(self):
        return self.type


class Board:
    def __init__(self):
        self.board_surface = pygame.Surface((settings.WIDTH, settings.HEIGHT))
        self.board_list = [
            [Tile(col, row, settings.tile_empty, ".") for col in range(settings.COLS)]
            for row in range(settings.ROWS)
        ]

        self.place_mines()
        self.place_clues()
        self.dug = []

    def place_mines(self):
        mines_to_place = settings.get_mine_amount()
        print("Placing mines:", mines_to_place)  # DEBUG

        placed = 0
        while placed < mines_to_place:
            row = random.randint(0, settings.ROWS - 1)
            col = random.randint(0, settings.COLS - 1)

            if self.board_list[row][col].type == ".":
                self.board_list[row][col].image = settings.tile_mine
                self.board_list[row][col].type = "X"
                placed += 1

    def place_clues(self):
        for row in range(settings.ROWS):
            for col in range(settings.COLS):
                if self.board_list[row][col].type != "X":
                    total_mines = self.check_neighbours(row, col)
                    if total_mines > 0:
                        self.board_list[row][col].image = settings.tile_numbers[total_mines - 1]
                        self.board_list[row][col].type = "C"

    @staticmethod
    def is_inside(row, col):
        return 0 <= row < settings.ROWS and 0 <= col < settings.COLS

    def check_neighbours(self, row, col):
        total_mines = 0
        for ro in range(-1, 2):
            for co in range(-1, 2):
                nr, nc = row + ro, col + co
                if self.is_inside(nr, nc) and self.board_list[nr][nc].type == "X":
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
            tile.image = settings.tile_exploded
            return False

        tile.revealed = True
        if tile.type == "C":
            return True

        # Flood fill for empty tiles
        for r in range(max(0, row - 1), min(settings.ROWS - 1, row + 1) + 1):
            for c in range(max(0, col - 1), min(settings.COLS - 1, col + 1) + 1):
                if (r, c) not in self.dug:
                    self.dig(r, c)

        return True

    def has_dugged(self, row, col):
        return self.board_list[row][col].revealed

    def reveal(self, row, col):
        tile = self.board_list[row][col]
        if tile.type == "X":
            tile.revealed = True
            tile.flagged = False
            return True
        return False

    def display_board(self):
        for row in self.board_list:
            print(row)
