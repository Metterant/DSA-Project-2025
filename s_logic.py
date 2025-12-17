import random
import math
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

        self.percentage = [
            [Tile(col, row, settings.tile_empty, 0.0) for col in range(settings.COLS)]
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

    def iter_neighbours(self, row, col, include_self=False):
        for ro in range(-1, 2):
            for co in range(-1, 2):
                if not include_self and ro == 0 and co == 0:
                    continue
                nr, nc = row + ro, col + co
                if self.is_inside(nr, nc):
                    yield nr, nc

    def get_revealed_number(self, row, col) -> int:
        """Return the visible number for a revealed safe tile.

        In this codebase, a safe tile is either:
        - type "C" (clue) => number is 1..8
        - type "." (empty) => number is 0

        The number isn't stored directly, so we derive it using the same mine
        counting used to assign clue images.
        """
        t = self.board_list[row][col]
        if t.type == "C":
            return self.check_neighbours(row, col)
        return 0

    def probability_grid(self, *, max_frontier_exact=25, max_solutions_cap=5000):
        """Compute a ROWS x COLS grid with P(tile is a mine) from revealed clues.

        Core idea: each revealed safe tile gives a constraint:
            sum(unknown neighbour mines) == (visible_number - flagged_neighbours)

        Solve constraints on the *frontier* (unknown tiles adjacent to revealed
        safe tiles) by enumerating consistent mine/no-mine assignments.

        To respect the global mine count, each frontier assignment is weighted by
        the number of ways to place the remaining mines in the unconstrained
        outside region.

        - Revealed safe tiles return 0.0
        - Flagged tiles return 1.0 (treated as mines during inference)
        """

        flagged = set()
        revealed_mines = 0
        for r in range(settings.ROWS):
            for c in range(settings.COLS):
                t = self.board_list[r][c]
                if t.flagged:
                    flagged.add((r, c))
                if t.revealed and t.type == "X":
                    revealed_mines += 1


        total_mines = settings.get_mine_amount()
        remaining_mines = total_mines - len(flagged) - revealed_mines
        if remaining_mines < 0:
            remaining_mines = 0

        unknown = [(r, c) for r in range(settings.ROWS) for c in range(settings.COLS)
                   if not self.board_list[r][c].revealed and (r, c) not in flagged]

        # Build constraints from revealed safe tiles.
        frontier_set = set()
        raw_constraints = []  # (list[(r,c)], required)
        for r in range(settings.ROWS):
            for c in range(settings.COLS):
                t = self.board_list[r][c]
                if not t.revealed or t.type == "X":
                    continue

                number = self.get_revealed_number(r, c)
                flagged_nei = 0
                unknown_nei = []
                for nr, nc in self.iter_neighbours(r, c):
                    if (nr, nc) in flagged:
                        flagged_nei += 1
                    else:
                        nt = self.board_list[nr][nc]
                        if not nt.revealed:
                            unknown_nei.append((nr, nc))

                required = number - flagged_nei
                if required < 0:
                    # Flags contradict the visible number.
                    return [[0.0 for _ in range(settings.COLS)] for _ in range(settings.ROWS)]

                if not unknown_nei:
                    if required != 0:
                        return [[0.0 for _ in range(settings.COLS)] for _ in range(settings.ROWS)]
                    continue

                for pos in unknown_nei:
                    frontier_set.add(pos)
                raw_constraints.append((unknown_nei, required))

        # Start probability grid.
        probs = [[0.0 for _ in range(settings.COLS)] for _ in range(settings.ROWS)]
        for (r, c) in flagged:
            probs[r][c] = 1.0

        # No visible constraints: every unknown tile has the same base rate.
        if not raw_constraints:
            base = (remaining_mines / len(unknown)) if unknown else 0.0
            for (r, c) in unknown:
                probs[r][c] = base
            return probs

        frontier = sorted(frontier_set)
        frontier_index = {pos: i for i, pos in enumerate(frontier)}
        outside = [pos for pos in unknown if pos not in frontier_set]
        outside_count = len(outside)

        # Convert constraints to index form.
        constraints = []  # (idxs, required)
        for tiles, req in raw_constraints:
            idxs = [frontier_index[pos] for pos in tiles if pos in frontier_index]
            if idxs:
                constraints.append((idxs, req))

        n = len(frontier)
        if n == 0:
            # Everything unknown is outside; just base rate with global mine count.
            base = (remaining_mines / len(unknown)) if unknown else 0.0
            for (r, c) in unknown:
                probs[r][c] = base
            return probs

        var_to_constraints = [[] for _ in range(n)]
        cons_required = []
        cons_sum = []
        cons_unassigned = []
        for ci, (idxs, req) in enumerate(constraints):
            cons_required.append(req)
            cons_sum.append(0)
            cons_unassigned.append(len(idxs))
            for v in idxs:
                var_to_constraints[v].append(ci)

        assignment = [0] * n
        mine_weight = [0] * n
        total_weight = 0
        outside_mines_weighted_sum = 0
        solutions_found = 0

        def feasible(ci):
            req = cons_required[ci]
            s = cons_sum[ci]
            u = cons_unassigned[ci]
            return s <= req <= s + u

        cap = None if n <= max_frontier_exact else max_solutions_cap

        def recurse(i):
            nonlocal total_weight, outside_mines_weighted_sum, solutions_found
            if cap is not None and solutions_found >= cap:
                return

            if i == n:
                frontier_mines = sum(assignment)
                outside_mines = remaining_mines - frontier_mines
                if outside_mines < 0 or outside_mines > outside_count:
                    return

                if outside_count == 0:
                    weight = 1 if outside_mines == 0 else 0
                else:
                    weight = math.comb(outside_count, outside_mines)
                if weight == 0:
                    return

                total_weight += weight
                outside_mines_weighted_sum += weight * outside_mines
                for vi, val in enumerate(assignment):
                    if val:
                        mine_weight[vi] += weight
                solutions_found += 1
                return

            for val in (0, 1):
                touched = []
                for ci in var_to_constraints[i]:
                    cons_unassigned[ci] -= 1
                    if val:
                        cons_sum[ci] += 1
                    touched.append(ci)

                ok = True
                for ci in touched:
                    if not feasible(ci):
                        ok = False
                        break

                if ok:
                    assignment[i] = val
                    recurse(i + 1)
                    assignment[i] = 0

                for ci in touched:
                    if val:
                        cons_sum[ci] -= 1
                    cons_unassigned[ci] += 1

                if cap is not None and solutions_found >= cap:
                    return

        recurse(0)

        if total_weight == 0:
            # No consistent assignments (usually due to incorrect flags). Fall back.
            base = (remaining_mines / len(unknown)) if unknown else 0.0
            for (r, c) in unknown:
                probs[r][c] = base
            return probs

        for idx, (r, c) in enumerate(frontier):
            probs[r][c] = mine_weight[idx] / total_weight

        if outside_count > 0:
            outside_prob = outside_mines_weighted_sum / (outside_count * total_weight)
            for (r, c) in outside:
                probs[r][c] = outside_prob

        return probs

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
