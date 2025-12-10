import pygame
from settings import *
from s_logic import *
from collections import Counter

class Game:
    def __init__(self):
        # Initialize pygame font module
        pygame.font.init()
        
        # Mine detector mode
        self.detector = False
        self.detector_count = DETECT_AVAILABLE

        # Increase window height to leave room for the controls
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT + 80))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(font_path, 30)  # Use 'Arial' font
        
        # Create undo button
        self.undo_button = pygame.Rect(UNDO_BUTTON_X, UNDO_BUTTON_Y, 
                                      UNDO_BUTTON_WIDTH, UNDO_BUTTON_HEIGHT)
        self.button_hover = False

    def new(self):
        self.board = Board()
        # self.board.display_board()
        # Stack storing board states for undo
        self.undo_stack = []
        self.win = False  # Track win/loss state

    def run(self):
        self.playing = True
        while self.playing:
            self.clock.tick(FPS)
            self.events()
            self.draw()
        else:
            self.end_screen()

    def draw(self):
        self.screen.fill(BGCOLOUR)
        self.board.draw(self.screen)
        
        # Draw undo button
        button_colour = BUTTON_HOVER if self.button_hover else BUTTON_COLOUR
        pygame.draw.rect(self.screen, button_colour, self.undo_button, border_radius=8)
        pygame.draw.rect(self.screen, WHITE, self.undo_button, 2, border_radius=8)
        
        # Draw button label
        undo_text = self.font.render("UNDO", True, BUTTON_TEXT)
        text_rect = undo_text.get_rect(center=self.undo_button.center)
        self.screen.blit(undo_text, text_rect)
        
        # Draw remaining undo count
        undo_count = len(self.undo_stack)
        count_text = self.font.render(f"Undo: {undo_count}", True, YELLOW)
        self.screen.blit(count_text, (10, HEIGHT + 10))

        # Draw Detector Mode
        if self.detector:
            detector_text_color = GREEN
            detector_mode_text = 'Active'
        else:
            detector_text_color = RED
            detector_mode_text = 'Inactive'

        detector_text = self.font.render(f"Detector: {detector_mode_text} ({self.detector_count})", True, detector_text_color)
        self.screen.blit(detector_text, (WIDTH - detector_text.get_width() - 10, HEIGHT + 10))

        pygame.display.flip()

    def check_win(self):
        for row in self.board.board_list:
            for tile in row:
                if tile.type != "X" and not tile.revealed:
                    return False
        return True

    def save_state(self):
        """Store current board state for undo"""
        state = []
        for row in range(ROWS):
            row_state = []
            for col in range(COLS):
                tile = self.board.board_list[row][col]
                row_state.append({
                    'revealed': tile.revealed,
                    'flagged': tile.flagged,
                    'type': tile.type
                })
            state.append(row_state)
        return state

    def load_state(self, state):
        """Restore board state from undo stack"""
        for row in range(ROWS):
            for col in range(COLS):
                tile_data = state[row][col]
                tile = self.board.board_list[row][col]
                tile.revealed = tile_data['revealed']
                tile.flagged = tile_data['flagged']
                tile.type = tile_data['type']
                
                # Update tile image based on type
                if tile.type == "X":
                    tile.image = tile_mine
                elif tile.type == "C":
                    # Recalculate neighbouring mine count
                    total_mines = self.board.check_neighbours(row, col)
                    if total_mines > 0:
                        tile.image = tile_numbers[total_mines-1]
                elif tile.type == ".":
                    tile.image = tile_empty

    def undo(self):
        """Perform Undo"""
        if self.undo_stack:
            last_state = self.undo_stack.pop()
            self.load_state(last_state)
            # Reset dug Tiles
            self.board.dug = []
            # Update dug list
            for row in range(ROWS):
                for col in range(COLS):
                    if self.board.board_list[row][col].revealed:
                        self.board.dug.append((row, col))

    def push_state(self):
        """
        Save the current state and push it to the undo_stack if the current state
        is different to the recent saved state
        
        :param self: Description
        """
        
        current_state = self.save_state()
        # Check if the current_state and most recent state are unidentical
        if not self.undo_stack or current_state != self.undo_stack[-1]:
            self.undo_stack.append(current_state)

    def events(self):
        mouse_pos = pygame.mouse.get_pos()
        
        # Update undo hover state
        self.button_hover = self.undo_button.collidepoint(mouse_pos)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit(0)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.detector = not self.detector

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                
                # Handle undo button click
                if self.undo_button.collidepoint(mx, my) and event.button == 1:
                    self.undo()
                    continue  # Use continue instead of return

                if self.detector:
                    # Handle board clicks (only within board area)
                    if my < HEIGHT:
                        grid_col = mx // TILESIZE
                        grid_row = my // TILESIZE

                        if not (0 <= grid_col < COLS and 0 <= grid_row < ROWS):
                            continue

                        if event.button == 1:
                            # Snapshot current state before any change
                            self.push_state()
                            
                            if self.detector_count > 0 and not self.board.has_dugged(grid_row, grid_col):
                                self.detector_count -= 1
                                self.board.reveal(grid_row, grid_col)
                else:          
                    # Handle board clicks (only within board area)
                    if my < HEIGHT:
                        grid_col = mx // TILESIZE
                        grid_row = my // TILESIZE

                        if not (0 <= grid_col < COLS and 0 <= grid_row < ROWS):
                            continue

                        if event.button == 1:
                            # Snapshot current state before any change
                            self.push_state()
                            
                            if not self.board.board_list[grid_row][grid_col].flagged:
                                if not self.board.dig(grid_row, grid_col):
                                    # explode
                                    for row in self.board.board_list:
                                        for tile in row:
                                            if tile.flagged and tile.type != "X":
                                                tile.flagged = False
                                                tile.revealed = True
                                                tile.image = tile_not_mine
                                            elif tile.type == "X":
                                                tile.revealed = True
                                    self.playing = False

                        if event.button == 3:
                            # Snapshot current state before toggling flag
                            self.push_state()
                            
                            if not self.board.board_list[grid_row][grid_col].revealed:
                                self.board.board_list[grid_row][grid_col].flagged = not self.board.board_list[grid_row][grid_col].flagged


                if self.check_win():
                    self.win = True
                    self.playing = False
                    for row in self.board.board_list:
                        for tile in row:
                            if not tile.revealed:
                                tile.flagged = True


    def end_screen(self):
        # Show win/lose message
        font = pygame.font.SysFont('Arial', 50)
        if self.win:
            message = "YOU WIN!"
            colour = GREEN
        else:
            message = "GAME OVER!"
            colour = RED
            
        text = font.render(message, True, colour)
        text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2))
        
        # Draw restart button
        restart_button = pygame.Rect(WIDTH//2 - 80, HEIGHT//2 + 50, 160, 50)
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit(0)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    if restart_button.collidepoint(mx, my):
                        return

            # Draw end screen
            self.screen.fill(BGCOLOUR)
            self.board.draw(self.screen)
            
            # Draw translucent overlay
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))
            
            # Draw message
            self.screen.blit(text, text_rect)
            
            # Draw restart button
            pygame.draw.rect(self.screen, BUTTON_COLOUR, restart_button, border_radius=8)
            pygame.draw.rect(self.screen, WHITE, restart_button, 2, border_radius=8)
            
            restart_font = pygame.font.SysFont('Arial', 30)
            restart_text = restart_font.render("PLAY AGAIN", True, BUTTON_TEXT)
            restart_rect = restart_text.get_rect(center=restart_button.center)
            self.screen.blit(restart_text, restart_rect)
            
            pygame.display.flip()


if __name__ == "__main__":
    game = Game()
    while True:
        game.new()
        game.run()