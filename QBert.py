# Import the pygame library
import pygame
import sys
import math
import random # Needed for enemy logic
import time # Needed for timing enemy movement

# --- Constants ---
# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700

# Colors (RGB) - CGA Palette 1 (Black, Cyan, Magenta, White)
CGA_BLACK = (0, 0, 0)
CGA_CYAN = (0, 255, 255)
CGA_MAGENTA = (255, 0, 255)
CGA_WHITE = (255, 255, 255)

# Game Colors using CGA Palette
COLOR_BACKGROUND = CGA_BLACK
COLOR_CUBE_INITIAL = CGA_CYAN
COLOR_CUBE_TARGET = CGA_MAGENTA # Target color for cubes
COLOR_PLAYER = CGA_WHITE
COLOR_TEXT = CGA_WHITE
COLOR_OUTLINE = CGA_BLACK

# Enemy Colors (Using CGA Palette)
COLOR_COILY_BALL = CGA_MAGENTA # Ball form (Kept for potential future use)
COLOR_COILY_SNAKE = CGA_WHITE  # Snake form

# Pyramid structure
PYRAMID_ROWS = 7
CUBES_PER_ROW = [i + 1 for i in range(PYRAMID_ROWS)]
TOTAL_CUBES = sum(CUBES_PER_ROW)

# Cube visual properties
CUBE_WIDTH = 60
CUBE_HEIGHT_STEP = 45
CUBE_TOP_FACE_HEIGHT = 30
CUBE_SIDE_FACE_HEIGHT = 30

# Pyramid positioning
PYRAMID_TOP_X = SCREEN_WIDTH // 2
PYRAMID_TOP_Y = 100

# Player properties
PLAYER_WIDTH = 20
PLAYER_HEIGHT = 25
PLAYER_FEET_HEIGHT = 5
PLAYER_FEET_WIDTH = 6
PLAYER_NOSE_SIZE = 4
PLAYER_START_LIVES = 3 # Define starting lives as a constant

# Enemy properties
COILY_BALL_RADIUS = 10 # Kept for potential future use
COILY_SNAKE_WIDTH = 18 # Slightly smaller than player
COILY_SNAKE_HEIGHT = 22
COILY_MOVE_INTERVAL_BALL = 700 # Kept for potential future use
COILY_MOVE_INTERVAL_SNAKE = 600 # Milliseconds between snake hops

# Game states
STATE_PLAYING = 1
STATE_GAME_OVER = 2
STATE_LEVEL_COMPLETE = 3
STATE_PLAYER_DIED = 4 # Intermediate state after collision/fall

# --- Sound Placeholders ---
def play_sound(sound_name):
    """Placeholder function to indicate sound playback."""
    print(f"SOUND: Playing '{sound_name}'")
    # Add actual sound playing logic here if you have sound files

# --- Helper Functions ---
def get_cube_screen_pos(grid_row, grid_col):
    """Calculates the center screen coordinates (x, y) for a cube based on its grid position."""
    if not (0 <= grid_row < PYRAMID_ROWS and 0 <= grid_col < CUBES_PER_ROW[grid_row]):
        return None
    screen_y = PYRAMID_TOP_Y + grid_row * CUBE_HEIGHT_STEP
    row_center_offset = (grid_col - grid_row / 2.0) * CUBE_WIDTH
    screen_x = PYRAMID_TOP_X + row_center_offset
    return int(screen_x), int(screen_y)

def draw_iso_cube(surface, center_x, center_y, color):
    """Draws a simple isometric cube representation using CGA colors."""
    top_point = (center_x, center_y - CUBE_TOP_FACE_HEIGHT // 2)
    left_point = (center_x - CUBE_WIDTH // 2, center_y)
    bottom_point = (center_x, center_y + CUBE_TOP_FACE_HEIGHT // 2)
    right_point = (center_x + CUBE_WIDTH // 2, center_y)
    bottom_left = (left_point[0], left_point[1] + CUBE_SIDE_FACE_HEIGHT)
    bottom_center = (bottom_point[0], bottom_point[1] + CUBE_SIDE_FACE_HEIGHT)
    bottom_right = (right_point[0], right_point[1] + CUBE_SIDE_FACE_HEIGHT)
    side_color_left = COLOR_OUTLINE
    side_color_right = COLOR_OUTLINE
    pygame.draw.polygon(surface, color, [top_point, left_point, bottom_point, right_point])
    pygame.draw.polygon(surface, side_color_left, [left_point, bottom_point, bottom_center, bottom_left])
    pygame.draw.polygon(surface, side_color_right, [right_point, bottom_point, bottom_center, bottom_right])
    pygame.draw.polygon(surface, COLOR_OUTLINE, [top_point, left_point, bottom_point, right_point], 1)
    pygame.draw.polygon(surface, COLOR_OUTLINE, [left_point, bottom_point, bottom_center, bottom_left], 1)
    pygame.draw.polygon(surface, COLOR_OUTLINE, [right_point, bottom_point, bottom_center, bottom_right], 1)

# --- Classes ---
class Cube:
    """Represents a single cube in the pyramid."""
    def __init__(self, grid_row, grid_col, initial_color=COLOR_CUBE_INITIAL, target_color=COLOR_CUBE_TARGET):
        self.grid_row = grid_row
        self.grid_col = grid_col
        self.initial_color = initial_color
        self.target_color = target_color
        self.current_color = initial_color
        self.screen_pos = get_cube_screen_pos(grid_row, grid_col)
        self.is_target_color = False

    def change_color(self):
        """Changes the cube's color towards the target color."""
        if self.current_color == self.initial_color:
            self.current_color = self.target_color
            self.is_target_color = True
            play_sound("change_color")
            return True
        return False

    def reset_color(self):
        """Resets the cube to its initial color."""
        self.current_color = self.initial_color
        self.is_target_color = False

    def draw(self, surface):
        """Draws the cube on the screen."""
        if self.screen_pos:
            draw_iso_cube(surface, self.screen_pos[0], self.screen_pos[1], self.current_color)

class Player:
    """Represents the player character (Q*bert)."""
    def __init__(self, start_row=0, start_col=0):
        self.start_row = start_row # Store initial position
        self.start_col = start_col
        self.grid_row = start_row
        self.grid_col = start_col
        self.update_screen_pos()
        self.color = COLOR_PLAYER
        self.lives = PLAYER_START_LIVES
        self.is_active = True # Flag to control player input/drawing during death animation

    def update_screen_pos(self):
        """Updates the player's screen position based on grid position."""
        pos = get_cube_screen_pos(self.grid_row, self.grid_col)
        if pos:
            self.screen_x = pos[0]
            self.screen_y = pos[1] - CUBE_TOP_FACE_HEIGHT // 2 - PLAYER_HEIGHT // 2
        else:
             self.screen_x = -100 # Off screen
             self.screen_y = -100
             return False
        return True

    def move(self, dr, dc):
        """Attempts to move the player by delta row (dr) and delta column (dc)."""
        if not self.is_active: return False # Don't move if inactive

        play_sound("jump")
        new_row = self.grid_row + dr
        new_col = self.grid_col + dc

        if 0 <= new_row < PYRAMID_ROWS and 0 <= new_col < CUBES_PER_ROW[new_row]:
            self.grid_row = new_row
            self.grid_col = new_col
            if not self.update_screen_pos():
                play_sound("fall")
                return False # Fell off (should be handled by caller)
            play_sound("land")
            return True
        else:
            # Player attempted move off edge - this is a fall
            self.grid_row = new_row # Update position to visually fall off
            self.grid_col = new_col
            self.update_screen_pos()
            play_sound("fall")
            return False # Failed move (fell)

    def reset_position(self):
        """Resets player to the starting cube."""
        self.grid_row = self.start_row
        self.grid_col = self.start_col
        self.update_screen_pos()
        self.is_active = True

    def reset_lives(self):
        """ Resets player lives to the starting amount. """
        self.lives = PLAYER_START_LIVES

    def die(self):
        """Handles player death."""
        self.lives -= 1
        self.is_active = False # Disable input during death pause
        play_sound("player_die") # Specific sound for player death
        print(f"Player died! Lives left: {self.lives}")

    def draw(self, surface):
        """Draws the player as a simple blocky shape."""
        if self.screen_x > 0 and self.is_active: # Only draw if on screen and active
            body_rect = pygame.Rect(self.screen_x - PLAYER_WIDTH // 2, self.screen_y - PLAYER_HEIGHT // 2, PLAYER_WIDTH, PLAYER_HEIGHT)
            pygame.draw.rect(surface, self.color, body_rect)
            foot_y = body_rect.bottom
            foot_left_x = body_rect.centerx - PLAYER_FEET_WIDTH * 1.5
            foot_right_x = body_rect.centerx + PLAYER_FEET_WIDTH * 0.5
            foot_left_rect = pygame.Rect(foot_left_x, foot_y, PLAYER_FEET_WIDTH, PLAYER_FEET_HEIGHT)
            foot_right_rect = pygame.Rect(foot_right_x, foot_y, PLAYER_FEET_WIDTH, PLAYER_FEET_HEIGHT)
            pygame.draw.rect(surface, self.color, foot_left_rect)
            pygame.draw.rect(surface, self.color, foot_right_rect)
            nose_x = body_rect.centerx - PLAYER_NOSE_SIZE // 2
            nose_y = body_rect.centery + PLAYER_HEIGHT // 4
            nose_rect = pygame.Rect(nose_x, nose_y, PLAYER_NOSE_SIZE, PLAYER_NOSE_SIZE)
            pygame.draw.rect(surface, COLOR_BACKGROUND, nose_rect)
            pygame.draw.rect(surface, COLOR_OUTLINE, body_rect, 1)
            pygame.draw.rect(surface, COLOR_OUTLINE, foot_left_rect, 1)
            pygame.draw.rect(surface, COLOR_OUTLINE, foot_right_rect, 1)

    def get_current_cube_index(self):
         """Calculates the flat index of the cube the player is on."""
         if not self.is_active: return -1 # Don't interact if dead
         index = 0
         for r in range(self.grid_row):
             index += CUBES_PER_ROW[r]
         index += self.grid_col
         if not (0 <= self.grid_row < PYRAMID_ROWS and 0 <= self.grid_col < CUBES_PER_ROW[self.grid_row]):
             return -1
         return index

class Enemy:
    """Represents the Coily enemy."""
    def __init__(self):
        self.reset()
        self.last_move_time = pygame.time.get_ticks() # For timing movement

    def reset(self):
        """Resets Coily to the starting state (snake at bottom)."""
        self.grid_row = PYRAMID_ROWS - 1 # Start at the bottom row
        self.grid_col = random.randint(0, CUBES_PER_ROW[self.grid_row] - 1)
        self.is_snake = True # Start as a snake immediately
        self.is_active = True # Make active
        self.update_screen_pos()
        self.last_move_time = pygame.time.get_ticks() # Reset move timer
        print(f"Coily reset as snake at ({self.grid_row}, {self.grid_col})")

    def update_screen_pos(self):
        """Updates the enemy's screen position based on grid position."""
        pos = get_cube_screen_pos(self.grid_row, self.grid_col)
        if pos:
            if self.is_snake:
                self.screen_x = pos[0]
                self.screen_y = pos[1] - CUBE_TOP_FACE_HEIGHT // 2 - COILY_SNAKE_HEIGHT // 2
            else: # Ball logic
                self.screen_x = pos[0]
                self.screen_y = pos[1] - CUBE_TOP_FACE_HEIGHT // 2 - COILY_BALL_RADIUS // 2
        else:
             # Enemy fell off or invalid position
             if self.is_active:
                 print(f"Coily position invalid ({self.grid_row}, {self.grid_col}) - Deactivating")
             self.is_active = False
             self.screen_x = -100
             self.screen_y = -100
             return False
        return True

    def move(self, player_pos):
        """Moves Coily (always as snake now) based on player position."""
        if not self.is_active: return

        current_time = pygame.time.get_ticks()
        move_interval = COILY_MOVE_INTERVAL_SNAKE

        if current_time - self.last_move_time > move_interval:
            self.last_move_time = current_time

            dr, dc = 0, 0 # Delta row, delta column
            player_row, player_col = player_pos
            play_sound("enemy_hop") # Snake hops

            # --- Determine Vertical Direction ---
            if player_row > self.grid_row: dr = 1
            elif player_row < self.grid_row: dr = -1
            else: dr = 0

            # --- Determine Horizontal Direction (dc) based on dr ---
            if dr > 0: # Moving Down
                new_row = self.grid_row + 1
                c1 = self.grid_col; c2 = self.grid_col + 1
                valid_c1 = 0 <= c1 < CUBES_PER_ROW[new_row]
                valid_c2 = 0 <= c2 < CUBES_PER_ROW[new_row]
                if valid_c1 and valid_c2:
                    proj_p_col = player_col - (player_row - new_row)
                    dist1 = abs(proj_p_col - c1); dist2 = abs(proj_p_col - c2)
                    if dist1 < dist2: dc = 0
                    elif dist2 < dist1: dc = 1
                    else: dc = random.choice([0, 1])
                elif valid_c1: dc = 0
                elif valid_c2: dc = 1
                else: dr, dc = 0, 0
            elif dr < 0: # Moving Up
                new_row = self.grid_row - 1
                c1 = self.grid_col - 1; c2 = self.grid_col
                valid_c1 = 0 <= new_row < PYRAMID_ROWS and 0 <= c1 < CUBES_PER_ROW[new_row] # Check row validity too
                valid_c2 = 0 <= new_row < PYRAMID_ROWS and 0 <= c2 < CUBES_PER_ROW[new_row] # Check row validity too
                if valid_c1 and valid_c2:
                    proj_p_col = player_col - (player_row - new_row)
                    dist1 = abs(proj_p_col - c1); dist2 = abs(proj_p_col - c2)
                    if dist1 < dist2: dc = -1
                    elif dist2 < dist1: dc = 0
                    else: dc = random.choice([-1, 0])
                elif valid_c1: dc = -1
                elif valid_c2: dc = 0
                else: dr, dc = 0, 0
            else: # dr == 0 (Same Row)
                if player_col > self.grid_col: # Player is right
                    if abs((player_row - (self.grid_row + 1))) <= abs((player_row - (self.grid_row - 1))): dr, dc = 1, 1
                    else: dr, dc = -1, 0
                elif player_col < self.grid_col: # Player is left
                    if abs((player_row - (self.grid_row + 1))) <= abs((player_row - (self.grid_row - 1))): dr, dc = 1, 0
                    else: dr, dc = -1, -1
                else: dr, dc = 0, 0 # Same cube

            # --- Execute Move ---
            final_new_row = self.grid_row + dr
            final_new_col = self.grid_col + dc

            if 0 <= final_new_row < PYRAMID_ROWS and 0 <= final_new_col < CUBES_PER_ROW[final_new_row]:
                self.grid_row = final_new_row
                self.grid_col = final_new_col
                self.update_screen_pos()
            else:
                if self.is_active:
                    print(f"Coily attempted invalid move from ({self.grid_row},{self.grid_col}) to ({final_new_row},{final_new_col}). Deactivating.")
                self.is_active = False
                self.screen_x = -100

    def draw(self, surface):
        """Draws Coily (should always be snake in this version)."""
        if self.screen_x > 0 and self.is_active:
            if self.is_snake:
                body_rect = pygame.Rect(self.screen_x - COILY_SNAKE_WIDTH // 2, self.screen_y - COILY_SNAKE_HEIGHT // 2, COILY_SNAKE_WIDTH, COILY_SNAKE_HEIGHT)
                pygame.draw.rect(surface, COLOR_COILY_SNAKE, body_rect)
                pygame.draw.rect(surface, COLOR_OUTLINE, body_rect, 1)
                eye_size = 2
                eye_y = body_rect.centery - COILY_SNAKE_HEIGHT // 4
                eye_left_x = body_rect.centerx - COILY_SNAKE_WIDTH // 4
                eye_right_x = body_rect.centerx + COILY_SNAKE_WIDTH // 4
                pygame.draw.rect(surface, COLOR_BACKGROUND, (eye_left_x - eye_size//2, eye_y - eye_size//2, eye_size, eye_size))
                pygame.draw.rect(surface, COLOR_BACKGROUND, (eye_right_x - eye_size//2, eye_y - eye_size//2, eye_size, eye_size))

# --- Game Reset Function ---
def reset_game():
    """Resets the game state for a new game."""
    global score, game_state, player, coily, pyramid_cubes
    print("Resetting game...")
    score = 0
    player.reset_lives()
    player.reset_position()
    coily.reset()

    # Reset all cubes to initial color
    for cube in pyramid_cubes:
        cube.reset_color()

    # Recolor the starting cube for the player
    start_cube_index = player.get_current_cube_index()
    if 0 <= start_cube_index < len(pyramid_cubes):
        pyramid_cubes[start_cube_index].change_color() # Initial color change doesn't score

    game_state = STATE_PLAYING


# --- Game Setup ---
pygame.init()
pygame.mixer.init()
pygame.font.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Q*bert Clone - Restart/Exit Added") # Updated caption
clock = pygame.time.Clock()

# Load Fonts
try:
    game_font = pygame.font.SysFont('Consolas', 30)
    small_font = pygame.font.SysFont('Consolas', 20) # Smaller font for prompts
except pygame.error:
    game_font = pygame.font.Font(None, 35) # Fallback
    small_font = pygame.font.Font(None, 25) # Fallback

# --- Game Objects ---
pyramid_cubes = []
for r in range(PYRAMID_ROWS):
    for c in range(CUBES_PER_ROW[r]):
        pyramid_cubes.append(Cube(r, c))

player = Player(0, 0)
coily = Enemy()

# Initial game state setup
score = 0
game_state = STATE_PLAYING
player_death_timer = 0
PLAYER_DEATH_PAUSE = 1500

# Initial player landing color change
start_cube_index = player.get_current_cube_index()
if 0 <= start_cube_index < len(pyramid_cubes):
    pyramid_cubes[start_cube_index].change_color()

running = True

# --- Main Game Loop ---
while running:
    current_time_ticks = pygame.time.get_ticks()

    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False # Allow closing window
        if event.type == pygame.KEYDOWN:
            # --- Global Key Checks (Exit) ---
            if event.key == pygame.K_ESCAPE:
                running = False # Exit game immediately

            # --- Game Over State Key Checks (Restart) ---
            elif game_state == STATE_GAME_OVER:
                if event.key == pygame.K_r:
                    reset_game() # Call the reset function

            # --- Playing State Key Checks (Movement) ---
            elif game_state == STATE_PLAYING and player.is_active:
                moved = False
                fell = False

                if event.key == pygame.K_q: moved = player.move(-1, -1) # Up-Left
                elif event.key == pygame.K_w: moved = player.move(-1, 0)  # Up-Right
                elif event.key == pygame.K_a: moved = player.move(1, 0)   # Down-Left
                elif event.key == pygame.K_s: moved = player.move(1, 1)   # Down-Right

                if player.screen_x < 0: fell = True

                if fell:
                    player.die()
                    game_state = STATE_PLAYER_DIED
                    player_death_timer = current_time_ticks
                elif moved:
                    current_cube_index = player.get_current_cube_index()
                    if 0 <= current_cube_index < len(pyramid_cubes):
                        landed_cube = pyramid_cubes[current_cube_index]
                        if landed_cube.change_color():
                            score += 25
                            all_cubes_target = all(c.is_target_color for c in pyramid_cubes)
                            if all_cubes_target:
                                game_state = STATE_LEVEL_COMPLETE
                                score += 1000
                                play_sound("level_complete")
                                coily.is_active = False
                    else:
                        print(f"Error: Moved successfully but landed on invalid index: {current_cube_index}")
                        player.die()
                        game_state = STATE_PLAYER_DIED
                        player_death_timer = current_time_ticks

    # --- Game Logic Update ---
    if game_state == STATE_PLAYER_DIED:
        if current_time_ticks - player_death_timer > PLAYER_DEATH_PAUSE:
            if player.lives <= 0:
                game_state = STATE_GAME_OVER
                play_sound("game_over")
            else:
                player.reset_position()
                coily.reset()
                start_cube_index = player.get_current_cube_index()
                if 0 <= start_cube_index < len(pyramid_cubes):
                    if not pyramid_cubes[start_cube_index].is_target_color:
                        pyramid_cubes[start_cube_index].change_color()
                game_state = STATE_PLAYING

    if game_state == STATE_PLAYING:
        if coily.is_active:
            coily.move((player.grid_row, player.grid_col))
            if player.is_active and coily.is_active and \
               player.grid_row == coily.grid_row and \
               player.grid_col == coily.grid_col:
                print("Collision with Coily!")
                player.die()
                game_state = STATE_PLAYER_DIED
                player_death_timer = current_time_ticks

    # --- Drawing ---
    screen.fill(COLOR_BACKGROUND)
    for cube in pyramid_cubes: cube.draw(screen)
    coily.draw(screen)
    player.draw(screen)

    score_text = game_font.render(f"Score: {score}", True, COLOR_TEXT)
    lives_text = game_font.render(f"Lives: {player.lives}", True, COLOR_TEXT)
    screen.blit(score_text, (10, 10))
    screen.blit(lives_text, (SCREEN_WIDTH - lives_text.get_width() - 10, 10))

    # --- Draw Game State Messages ---
    if game_state == STATE_GAME_OVER:
        # Game Over Text
        go_text = game_font.render("GAME OVER", True, COLOR_PLAYER)
        go_rect = go_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20)) # Move up slightly
        screen.blit(go_text, go_rect)
        # Restart/Exit Prompt Text
        prompt_text = small_font.render("Press 'R' to Restart or 'ESC' to Exit", True, COLOR_TEXT)
        prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20)) # Position below GAME OVER
        screen.blit(prompt_text, prompt_rect)

    elif game_state == STATE_LEVEL_COMPLETE:
        lc_text = game_font.render("LEVEL COMPLETE!", True, COLOR_CUBE_TARGET)
        lc_rect = lc_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(lc_text, lc_rect)
        # Add logic here later to proceed to the next level after a pause

    pygame.display.flip()
    clock.tick(30)

# --- Cleanup ---
pygame.quit()
sys.exit()


