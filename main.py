import pygame
import settings          # <-- sửa: import nguyên module
from s_logic import *
from collections import Counter

class Game:
    def __init__(self):
        pygame.font.init()
        
        self.detector = False
        self.detector_count = settings.DETECT_AVAILABLE

        self.screen = pygame.display.set_mode((settings.WIDTH, settings.HEIGHT + 80))
        pygame.display.set_caption(settings.TITLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(settings.font_path, 30)
        
        self.undo_button = pygame.Rect(settings.UNDO_BUTTON_X, settings.UNDO_BUTTON_Y,
                                      settings.UNDO_BUTTON_WIDTH, settings.UNDO_BUTTON_HEIGHT)
        self.button_hover = False

    def new(self):
        print("Difficulty:", settings.DIFFICULTY)
        print("Mines:", settings.get_mine_amount())  # Debug confirm
        self.board = Board()
        self.undo_stack = []
        self.win = False

    def run(self):
        self.playing = True
        while self.playing:
            self.clock.tick(settings.FPS)
            self.events()
            self.draw()
        else:
            self.end_screen()

    def draw(self):
        self.screen.fill(settings.BGCOLOUR)
        self.board.draw(self.screen)
        
        button_colour = settings.BUTTON_HOVER if self.button_hover else settings.BUTTON_COLOUR
        pygame.draw.rect(self.screen, button_colour, self.undo_button, border_radius=8)
        pygame.draw.rect(self.screen, settings.WHITE, self.undo_button, 2, border_radius=8)
        
        undo_text = self.font.render("UNDO", True, settings.BUTTON_TEXT)
        text_rect = undo_text.get_rect(center=self.undo_button.center)
        self.screen.blit(undo_text, text_rect)
        
        undo_count = len(self.undo_stack)
        count_text = self.font.render(f"Undo: {undo_count}", True, settings.YELLOW)
        self.screen.blit(count_text, (10, settings.HEIGHT + 10))

        if self.detector:
            color = settings.GREEN
            status = "Active"
        else:
            color = settings.RED
            status = "Inactive"

        detector_text = self.font.render(
            f"Detector: {status} ({self.detector_count})", True, color)
        self.screen.blit(detector_text,
                         (settings.WIDTH - detector_text.get_width() - 10, settings.HEIGHT + 10))

        pygame.display.flip()

    def main_menu(self):
        menu_running = True
        title_font = pygame.font.SysFont("Arial", 48, bold=True)
        button_font = pygame.font.SysFont("Arial", 32)

        play_button = pygame.Rect(settings.WIDTH//2 - 100, settings.HEIGHT//2 - 20, 200, 60)
        settings_button = pygame.Rect(settings.WIDTH//2 - 100, settings.HEIGHT//2 + 70, 200, 60)
        quit_button = pygame.Rect(settings.WIDTH//2 - 100, settings.HEIGHT//2 + 160, 200, 60)

        while menu_running:
            self.screen.fill((30, 30, 30))

            title_text = title_font.render("MINESWEEPER CLONE", True, (255, 255, 0))
            self.screen.blit(title_text, title_text.get_rect(center=(settings.WIDTH//2, settings.HEIGHT//2 - 120)))

            for btn in [play_button, settings_button, quit_button]:
                pygame.draw.rect(self.screen, (70, 70, 70), btn, border_radius=8)
                pygame.draw.rect(self.screen, (200, 200, 200), btn, 3, border_radius=8)

            self.screen.blit(button_font.render("PLAY GAME", True, settings.WHITE), button_font.render("PLAY GAME", True, settings.WHITE).get_rect(center=play_button.center))
            self.screen.blit(button_font.render("SETTING", True, settings.WHITE), button_font.render("SETTING", True, settings.WHITE).get_rect(center=settings_button.center))
            self.screen.blit(button_font.render("QUIT", True, settings.WHITE), button_font.render("QUIT", True, settings.WHITE).get_rect(center=quit_button.center))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if play_button.collidepoint(event.pos):
                        return
                    if settings_button.collidepoint(event.pos):
                        self.settings_menu()
                    if quit_button.collidepoint(event.pos):
                        pygame.quit()
                        quit()

            pygame.display.flip()

    def settings_menu(self):
        running = True
        font = pygame.font.SysFont("Arial", 32)

        easy_button = pygame.Rect(settings.WIDTH//2 - 100, settings.HEIGHT//2 - 40, 200, 50)
        medium_button = pygame.Rect(settings.WIDTH//2 - 100, settings.HEIGHT//2 + 20, 200, 50)
        hard_button = pygame.Rect(settings.WIDTH//2 - 100, settings.HEIGHT//2 + 80, 200, 50)
        back_button = pygame.Rect(settings.WIDTH//2 - 100, settings.HEIGHT//2 + 160, 200, 50)

        # danh sách nút (để tránh dùng Rect làm key)
        buttons = [
            (easy_button, "EASY"),
            (medium_button, "MEDIUM"),
            (hard_button, "HARD"),
            (back_button, "BACK")
        ]

        while running:
            self.screen.fill((30, 30, 30))

            title = font.render("SETTINGS: DIFFICULTY", True, settings.YELLOW)
            self.screen.blit(title, title.get_rect(center=(settings.WIDTH//2, settings.HEIGHT//2 - 120)))

            # vẽ toàn bộ nút + chữ
            for btn, text in buttons:
                pygame.draw.rect(self.screen, settings.BUTTON_COLOUR, btn, border_radius=8)
                pygame.draw.rect(self.screen, settings.WHITE, btn, 2, border_radius=8)

                t = font.render(text, True, settings.WHITE)
                self.screen.blit(t, t.get_rect(center=btn.center))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos

                    if easy_button.collidepoint(pos):
                        settings.DIFFICULTY = "EASY"
                        return

                    if medium_button.collidepoint(pos):
                        settings.DIFFICULTY = "MEDIUM"
                        return

                    if hard_button.collidepoint(pos):
                        settings.DIFFICULTY = "HARD"
                        return

                    if back_button.collidepoint(pos):
                        return  # quay về main menu

            pygame.display.flip()


    def check_win(self):
        for row in self.board.board_list:
            for tile in row:
                if tile.type != "X" and not tile.revealed:
                    return False
        return True

    def save_state(self):
        state = []
        for row in range(settings.ROWS):
            row_state = []
            for col in range(settings.COLS):
                tile = self.board.board_list[row][col]
                row_state.append({
                    'revealed': tile.revealed,
                    'flagged': tile.flagged,
                    'type': tile.type
                })
            state.append(row_state)
        return state

    def load_state(self, state):
        for row in range(settings.ROWS):
            for col in range(settings.COLS):
                data = state[row][col]
                tile = self.board.board_list[row][col]

                tile.revealed = data['revealed']
                tile.flagged = data['flagged']
                tile.type = data['type']

                if tile.type == "X":
                    tile.image = settings.tile_mine
                elif tile.type == "C":
                    total_mines = self.board.check_neighbours(row, col)
                    if total_mines > 0:
                        tile.image = settings.tile_numbers[total_mines - 1]
                elif tile.type == ".":
                    tile.image = settings.tile_empty

    def undo(self):
        if self.undo_stack:
            self.load_state(self.undo_stack.pop())
            self.board.dug = []
            for r in range(settings.ROWS):
                for c in range(settings.COLS):
                    if self.board.board_list[r][c].revealed:
                        self.board.dug.append((r, c))

    def push_state(self):
        current = self.save_state()
        if not self.undo_stack or current != self.undo_stack[-1]:
            self.undo_stack.append(current)

    def events(self):
        mouse_pos = pygame.mouse.get_pos()
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

                if self.undo_button.collidepoint(mx, my) and event.button == 1:
                    self.undo()
                    continue

                if self.detector:
                    if my < settings.HEIGHT:
                        col = mx // settings.TILESIZE
                        row = my // settings.TILESIZE
                        if 0 <= col < settings.COLS and 0 <= row < settings.ROWS:
                            if event.button == 1:
                                self.push_state()
                                if self.detector_count > 0:
                                    self.detector_count -= 1
                                    self.board.reveal(row, col)
                else:
                    if my < settings.HEIGHT:
                        col = mx // settings.TILESIZE
                        row = my // settings.TILESIZE
                        if 0 <= col < settings.COLS and 0 <= row < settings.ROWS:

                            tile = self.board.board_list[row][col]

                            if event.button == 1:
                                self.push_state()
                                if not tile.flagged:
                                    if not self.board.dig(row, col):
                                        for r in self.board.board_list:
                                            for t in r:
                                                if t.flagged and t.type != "X":
                                                    t.flagged = False
                                                    t.revealed = True
                                                    t.image = settings.tile_not_mine
                                                elif t.type == "X":
                                                    t.revealed = True
                                        self.playing = False

                            if event.button == 3:
                                self.push_state()
                                if not tile.revealed:
                                    tile.flagged = not tile.flagged

                if self.check_win():
                    self.win = True
                    self.playing = False
                    for r in self.board.board_list:
                        for t in r:
                            if not t.revealed:
                                t.flagged = True

    def end_screen(self):
        font = pygame.font.SysFont('Arial', 50)
        text = font.render("YOU WIN!" if self.win else "GAME OVER!", True,
                           settings.GREEN if self.win else settings.RED)

        text_rect = text.get_rect(center=(settings.WIDTH//2, settings.HEIGHT//2))
        restart_button = pygame.Rect(settings.WIDTH//2 - 80, settings.HEIGHT//2 + 50, 160, 50)
        menu_button = pygame.Rect(settings.WIDTH//2 - 80, settings.HEIGHT//2 + 120, 160, 50)
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit(0)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if restart_button.collidepoint(event.pos):
                        return
                    if menu_button.collidepoint(event.pos):
                        self.main_menu()       
                        return         

            self.screen.fill(settings.BGCOLOUR)
            self.board.draw(self.screen)

            overlay = pygame.Surface((settings.WIDTH, settings.HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))

            self.screen.blit(text, text_rect)

            pygame.draw.rect(self.screen, settings.BUTTON_COLOUR, restart_button, border_radius=8)
            pygame.draw.rect(self.screen, settings.WHITE, restart_button, 2, border_radius=8)

            restart_font = pygame.font.SysFont('Arial', 30)
            restart_text = restart_font.render("PLAY AGAIN", True, settings.BUTTON_TEXT)
            restart_rect = restart_text.get_rect(center=restart_button.center)
            self.screen.blit(restart_text, restart_rect)
            
            pygame.draw.rect(self.screen, settings.BUTTON_COLOUR, menu_button, border_radius=8)
            pygame.draw.rect(self.screen, settings.WHITE, menu_button, 2, border_radius=8)

            menu_text = restart_font.render("MAIN MENU", True, settings.BUTTON_TEXT)
            menu_rect = menu_text.get_rect(center=menu_button.center)
            self.screen.blit(menu_text, menu_rect)

            pygame.display.flip()


if __name__ == "__main__":
    game = Game()
    game.main_menu()

    while True:
        game.new()
        game.run()
