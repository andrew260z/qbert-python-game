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

# Colors (RGB) - VGA-like Palette
VGA_BLACK = (0, 0, 0)
VGA_DARK_BLUE = (0, 0, 170)         # Standard VGA Blue
VGA_MEDIUM_BLUE = (0, 0, 100)       # Darker for sides
VGA_LIGHT_BLUE = (85, 85, 255)      # Bright/Light Blue

VGA_YELLOW = (255, 255, 85)
VGA_ORANGE = (255, 165, 0)
VGA_DARK_ORANGE = (200, 100, 0)     # Darker for sides
VGA_BROWN = (170, 85, 0)            # For sides

VGA_PURPLE = (170, 0, 170)
VGA_RED = (170, 0, 0)
VGA_WHITE = (255, 255, 255)
VGA_TEXT_YELLOW = (255, 255, 85) # For UI text

# Game Colors using VGA Palette
COLOR_BACKGROUND = VGA_BLACK
COLOR_OUTLINE = VGA_BLACK # Outlines for cubes and characters

# Cube color schemes (top, left_side, right_side)
# Based on typical Q*bert level 1: Blue top, brownish/orange sides
INITIAL_CUBE_COLORS = (VGA_LIGHT_BLUE, VGA_ORANGE, VGA_BROWN)
# Changed state: Yellow top, bluish sides
TARGET_CUBE_COLORS = (VGA_YELLOW, VGA_MEDIUM_BLUE, VGA_DARK_BLUE)

COLOR_PLAYER_BODY = VGA_ORANGE
COLOR_PLAYER_FEET = VGA_RED
COLOR_PLAYER_NOSE_BG = VGA_BLACK # Nose is drawn as a hole

COLOR_COILY_SNAKE = VGA_PURPLE
COLOR_COILY_EYES = VGA_WHITE


# Pyramid structure
PYRAMID_ROWS = 7
CUBES_PER_ROW = [i + 1 for i in range(PYRAMID_ROWS)]
TOTAL_CUBES = sum(CUBES_PER_ROW)

# Cube visual properties for drawing
ISO_CUBE_WIDTH = 80          # Width of the top rhombus face
ISO_CUBE_TOP_H = 50          # Height of the top rhombus face
ISO_CUBE_SIDE_V_H = 50       # Vertical height of the side faces

# Cube grid positioning properties
GRID_COL_SPACING = ISO_CUBE_WIDTH      # Horizontal distance between cube centers in a row
GRID_ROW_SPACING = ISO_CUBE_TOP_H * 0.75 # Vertical distance between cube centers in adjacent rows (for overlap)

# Pyramid positioning
PYRAMID_TOP_X = SCREEN_WIDTH // 2
PYRAMID_TOP_Y = 100 # Y-coordinate for the center of the top-most cube's top face

# Player properties
PLAYER_WIDTH = 20
PLAYER_HEIGHT = 25
PLAYER_FEET_HEIGHT = 5
PLAYER_FEET_WIDTH = 6
PLAYER_NOSE_SIZE = 4
PLAYER_START_LIVES = 3

# Enemy properties
COILY_SNAKE_WIDTH = 18
COILY_SNAKE_HEIGHT = 22
# COILY_MOVE_INTERVAL_SNAKE = 600 # Milliseconds between snake hops (REMOVED/COMMENTED)
COILY_INTERVAL_LEVEL_1 = 1500  # Milliseconds for Coily's speed at level 1
COILY_INTERVAL_LEVEL_10 = 500   # Milliseconds for Coily's speed at level 10 (max speed)
MAX_LEVEL_FOR_SPEED_SCALING = 10

# Game states
STATE_PLAYING = 1
STATE_GAME_OVER = 2
STATE_LEVEL_COMPLETE = 3
STATE_PLAYER_DIED = 4

# --- Sound System ---
sound_files = {
    "jump": "jump.mp3",
    "land": "land.mp3",
    "fall": "fall.mp3",
    "change_color": "change_color.mp3",
    "level_complete": "level_complete.mp3",
    "player_die": "player_die.mp3",
    "enemy_hop": "enemy_hop.mp3",
    "game_over": "game_over.mp3"
}
loaded_sounds = {}

def play_sound(sound_name):
    """Plays a sound effect, loading it if necessary."""
    if sound_name not in sound_files:
        print(f"Warning: Sound '{sound_name}' not defined.")
        return

    if sound_name in loaded_sounds:
        try:
            loaded_sounds[sound_name].play()
        except pygame.error as e:
            print(f"Error playing sound {sound_name}: {e}")
        return

    file_path = sound_files[sound_name]
    try:
        sound = pygame.mixer.Sound(file_path)
        loaded_sounds[sound_name] = sound
        sound.play()
    except pygame.error as e:
        print(f"Error loading/playing sound {sound_name} from {file_path}: {e}")

# --- Helper Functions ---
def get_cube_screen_center_pos(grid_row, grid_col):
    """Calculates the screen coordinates (x, y) for the CENTER of a cube's TOP FACE."""
    if not (0 <= grid_row < PYRAMID_ROWS and 0 <= grid_col < CUBES_PER_ROW[grid_row]):
        return None
    # Horizontal position: Start at pyramid top X, adjust based on column and row
    # Each step in grid_col shifts by GRID_COL_SPACING
    # Each step in grid_row shifts the row's horizontal center by -GRID_COL_SPACING / 2
    screen_x = PYRAMID_TOP_X + (grid_col - grid_row / 2.0) * GRID_COL_SPACING
    # Vertical position: Start at pyramid top Y, adjust based on row
    screen_y = PYRAMID_TOP_Y + grid_row * GRID_ROW_SPACING
    return int(screen_x), int(screen_y)

def draw_iso_cube_detailed(surface, center_x, center_y, width, top_h, side_v_h,
                           color_top, color_left_side, color_right_side, color_outline):
    """Draws an isometric cube with distinct top, left, and right faces."""
    half_width = width // 2
    half_top_h = top_h // 2

    # Vertices of the top face (rhombus)
    # center_x, center_y is the center of this top face
    p_top_tip = (center_x, center_y - half_top_h)
    p_top_left = (center_x - half_width, center_y)
    p_top_bottom = (center_x, center_y + half_top_h)
    p_top_right = (center_x + half_width, center_y)

    # Vertices for the bottom of the side faces
    p_side_bottom_left = (p_top_left[0], p_top_left[1] + side_v_h)
    p_side_bottom_mid = (p_top_bottom[0], p_top_bottom[1] + side_v_h) # Front-bottom vertex
    p_side_bottom_right = (p_top_right[0], p_top_right[1] + side_v_h)

    # Draw order: draw farther faces first if overlap is an issue,
    # but for distinct non-overlapping faces, order is less critical than cube-to-cube order.
    # For standard Q*bert look, usually left and right sides, then top.

    # Left side face polygon
    # Points: top-left of top face, bottom-of-top-face, bottom-front-of-cube, bottom-left-of-side
    left_face_points = [p_top_left, p_top_bottom, p_side_bottom_mid, p_side_bottom_left]
    pygame.draw.polygon(surface, color_left_side, left_face_points)
    pygame.draw.polygon(surface, color_outline, left_face_points, 1)

    # Right side face polygon
    # Points: top-right-of-top-face, bottom-of-top-face, bottom-front-of-cube, bottom-right-of-side
    right_face_points = [p_top_right, p_top_bottom, p_side_bottom_mid, p_side_bottom_right]
    pygame.draw.polygon(surface, color_right_side, right_face_points)
    pygame.draw.polygon(surface, color_outline, right_face_points, 1)

    # Top face polygon (drawn last to be on top)
    top_face_points = [p_top_tip, p_top_left, p_top_bottom, p_top_right]
    pygame.draw.polygon(surface, color_top, top_face_points)
    pygame.draw.polygon(surface, color_outline, top_face_points, 1)


# --- Classes ---
class Cube:
    """Represents a single cube in the pyramid."""
    def __init__(self, grid_row, grid_col,
                 initial_colors=INITIAL_CUBE_COLORS,
                 target_colors=TARGET_CUBE_COLORS):
        self.grid_row = grid_row
        self.grid_col = grid_col
        self.initial_colors = initial_colors # Tuple: (top, left, right)
        self.target_colors = target_colors   # Tuple: (top, left, right)
        self.current_colors = initial_colors
        self.screen_center_pos = get_cube_screen_center_pos(grid_row, grid_col)
        self.is_target_color = False # Based on the top face's color state

    def change_color(self):
        """Changes the cube's color set to the target color set."""
        if self.current_colors[0] == self.initial_colors[0]: # Check based on top color
            self.current_colors = self.target_colors
            self.is_target_color = True
            play_sound("change_color")
            return True
        return False

    def reset_color(self):
        """Resets the cube to its initial color set."""
        self.current_colors = self.initial_colors
        self.is_target_color = False

    def draw(self, surface):
        """Draws the cube on the screen."""
        if self.screen_center_pos:
            draw_iso_cube_detailed(surface,
                                   self.screen_center_pos[0], self.screen_center_pos[1],
                                   ISO_CUBE_WIDTH, ISO_CUBE_TOP_H, ISO_CUBE_SIDE_V_H,
                                   self.current_colors[0], self.current_colors[1], self.current_colors[2],
                                   COLOR_OUTLINE)

class Player:
    """Represents the player character (Q*bert)."""
    def __init__(self, start_row=0, start_col=0):
        self.start_row = start_row
        self.start_col = start_col
        self.grid_row = start_row
        self.grid_col = start_col
        self.update_screen_pos()
        self.lives = PLAYER_START_LIVES
        self.is_active = True

    def update_screen_pos(self):
        """Updates the player's screen position based on grid position."""
        pos = get_cube_screen_center_pos(self.grid_row, self.grid_col)
        if pos:
            # Player's center Y should be slightly above the center of the cube's top face
            self.screen_x = pos[0]
            self.screen_y = pos[1] - PLAYER_HEIGHT // 2 # Center player on top face center
            return True
        else:
            self.screen_x = -100 # Off screen
            self.screen_y = -100
            return False

    def move(self, dr, dc):
        """Attempts to move the player by delta row (dr) and delta column (dc)."""
        if not self.is_active: return False

        play_sound("jump")
        new_row = self.grid_row + dr
        new_col = self.grid_col + dc

        if 0 <= new_row < PYRAMID_ROWS and 0 <= new_col < CUBES_PER_ROW[new_row]:
            self.grid_row = new_row
            self.grid_col = new_col
            if not self.update_screen_pos(): # Should not fail if grid pos is valid
                play_sound("fall") # Should be rare here
                return False
            play_sound("land")
            return True
        else:
            self.grid_row = new_row # Update position to visually fall off
            self.grid_col = new_col
            self.update_screen_pos() # Will set screen_x/y to off-screen
            play_sound("fall")
            return False # Failed move (fell)

    def reset_position(self):
        self.grid_row = self.start_row
        self.grid_col = self.start_col
        self.update_screen_pos()
        self.is_active = True

    def reset_lives(self):
        self.lives = PLAYER_START_LIVES

    def die(self):
        self.lives -= 1
        self.is_active = False
        play_sound("player_die")
        print(f"Player died! Lives left: {self.lives}")

    def draw(self, surface):
        if self.screen_x > 0 and self.is_active:
            # Simple blocky player
            body_rect = pygame.Rect(
                self.screen_x - PLAYER_WIDTH // 2,
                self.screen_y - PLAYER_HEIGHT // 2,
                PLAYER_WIDTH, PLAYER_HEIGHT
            )
            pygame.draw.rect(surface, COLOR_PLAYER_BODY, body_rect)

            # Feet
            foot_y = body_rect.bottom
            foot_left_x = body_rect.centerx - PLAYER_FEET_WIDTH * 1.5
            foot_right_x = body_rect.centerx + PLAYER_FEET_WIDTH * 0.5
            foot_left_rect = pygame.Rect(foot_left_x, foot_y, PLAYER_FEET_WIDTH, PLAYER_FEET_HEIGHT)
            foot_right_rect = pygame.Rect(foot_right_x, foot_y, PLAYER_FEET_WIDTH, PLAYER_FEET_HEIGHT)
            pygame.draw.rect(surface, COLOR_PLAYER_FEET, foot_left_rect)
            pygame.draw.rect(surface, COLOR_PLAYER_FEET, foot_right_rect)

            # Nose (simple black square for now)
            nose_x = body_rect.centerx - PLAYER_NOSE_SIZE // 2
            nose_y = body_rect.centery # Adjusted for better placement
            nose_rect = pygame.Rect(nose_x, nose_y, PLAYER_NOSE_SIZE, PLAYER_NOSE_SIZE)
            pygame.draw.rect(surface, COLOR_PLAYER_NOSE_BG, nose_rect)

            # Outlines
            pygame.draw.rect(surface, COLOR_OUTLINE, body_rect, 1)
            pygame.draw.rect(surface, COLOR_OUTLINE, foot_left_rect, 1)
            pygame.draw.rect(surface, COLOR_OUTLINE, foot_right_rect, 1)


    def get_current_cube_index(self):
        if not self.is_active: return -1
        if not (0 <= self.grid_row < PYRAMID_ROWS and 0 <= self.grid_col < CUBES_PER_ROW[self.grid_row]):
            return -1 # Player is off the valid grid
        index = 0
        for r in range(self.grid_row):
            index += CUBES_PER_ROW[r]
        index += self.grid_col
        return index

class Enemy:
    """Represents the Coily enemy."""
    def __init__(self):
        self.reset()
        self.last_move_time = pygame.time.get_ticks()

    def reset(self):
        self.grid_row = PYRAMID_ROWS - 1
        self.grid_col = random.randint(0, CUBES_PER_ROW[self.grid_row] - 1)
        self.is_snake = True # Always starts as snake
        self.is_active = True
        self.update_screen_pos()
        self.last_move_time = pygame.time.get_ticks()
        print(f"Coily reset as snake at ({self.grid_row}, {self.grid_col})")

    def update_screen_pos(self):
        pos = get_cube_screen_center_pos(self.grid_row, self.grid_col)
        if pos:
            self.screen_x = pos[0]
            self.screen_y = pos[1] - COILY_SNAKE_HEIGHT // 2 # Center snake on top face center
            return True
        else:
            if self.is_active:
                print(f"Coily position invalid ({self.grid_row}, {self.grid_col}) - Deactivating")
            self.is_active = False
            self.screen_x = -100
            self.screen_y = -100
            return False

    def move(self, player_pos):
        global current_level # Make sure we're using the global variable

        if not self.is_active: return

        current_time = pygame.time.get_ticks()

        # Dynamically calculate Coily's move interval based on current_level
        level_for_calc = min(current_level, MAX_LEVEL_FOR_SPEED_SCALING)

        if level_for_calc <= 1:
            current_coily_interval = COILY_INTERVAL_LEVEL_1
        elif level_for_calc >= MAX_LEVEL_FOR_SPEED_SCALING:
            current_coily_interval = COILY_INTERVAL_LEVEL_10
        else:
            scale_factor = (level_for_calc - 1) / (MAX_LEVEL_FOR_SPEED_SCALING - 1)
            current_coily_interval = COILY_INTERVAL_LEVEL_1 - (COILY_INTERVAL_LEVEL_1 - COILY_INTERVAL_LEVEL_10) * scale_factor
        
        current_coily_interval = int(current_coily_interval)


        if current_time - self.last_move_time > current_coily_interval:
            self.last_move_time = current_time
            play_sound("enemy_hop")

            dr, dc = 0, 0
            player_row, player_col = player_pos

            # Simplified Coily AI: Try to move towards player's current level or below.
            # Prioritize getting on the same row or moving down towards the player.
            # If player is above, Coily might try to move towards one of the two spots on the row below.
            # If player is below, Coily will try to move towards one of the two spots on the row below.
            # This is a common Q*bert AI pattern for Coily.

            possible_moves = []
            # Potential moves down-left and down-right from current position
            # (relative to Coily's current grid position)
            # For Coily, moving "down" the pyramid means increasing row index
            if self.grid_row + 1 < PYRAMID_ROWS:
                # Down-left from Coily's perspective on the grid
                if self.grid_col < CUBES_PER_ROW[self.grid_row + 1]:
                    possible_moves.append((1, 0)) # dr=1 (down), dc=0 (left relative to next row start)
                # Down-right from Coily's perspective on the grid
                if self.grid_col + 1 < CUBES_PER_ROW[self.grid_row + 1]:
                     possible_moves.append((1, 1)) # dr=1 (down), dc=1 (right relative to next row start)

            # Potential moves up-left and up-right
            # For Coily, moving "up" the pyramid means decreasing row index
            if self.grid_row - 1 >= 0:
                # Up-left
                if self.grid_col -1 >= 0 and self.grid_col -1 < CUBES_PER_ROW[self.grid_row -1]:
                     possible_moves.append((-1, -1)) # dr=-1 (up), dc=-1 (left relative to current col)
                # Up-right
                if self.grid_col >=0 and self.grid_col < CUBES_PER_ROW[self.grid_row-1]:
                     possible_moves.append((-1, 0)) # dr=-1 (up), dc=0 (right relative to current col)


            if not possible_moves: # No valid moves (e.g., stuck at top)
                if self.is_active: print(f"Coily has no valid moves from ({self.grid_row}, {self.grid_col})")
                # self.is_active = False # Or Coily just stays put
                return


            # Choose the best move towards the player
            best_move = None
            min_dist_sq = float('inf')

            for move_dr, move_dc in possible_moves:
                next_row, next_col = self.grid_row + move_dr, self.grid_col + move_dc
                # Ensure the calculated next_col is valid for next_row
                if not (0 <= next_row < PYRAMID_ROWS and 0 <= next_col < CUBES_PER_ROW[next_row]):
                    continue

                dist_sq = (next_row - player_row)**2 + (next_col - player_col)**2
                if dist_sq < min_dist_sq:
                    min_dist_sq = dist_sq
                    best_move = (move_dr, move_dc)
                elif dist_sq == min_dist_sq: # If distances are equal, randomly pick one
                    if random.choice([True, False]):
                        best_move = (move_dr, move_dc)
            
            if best_move:
                dr, dc = best_move
            elif possible_moves: # If no best move towards player, pick a random valid one
                dr, dc = random.choice(possible_moves)
            else: # Should not happen if initial possible_moves check is done
                return


            final_new_row = self.grid_row + dr
            final_new_col = self.grid_col + dc

            # Final check, though the loop should ensure this
            if 0 <= final_new_row < PYRAMID_ROWS and 0 <= final_new_col < CUBES_PER_ROW[final_new_row]:
                self.grid_row = final_new_row
                self.grid_col = final_new_col
                self.update_screen_pos()
            else:
                if self.is_active:
                    print(f"Coily attempted invalid final move from ({self.grid_row-dr},{self.grid_col-dc}) to ({final_new_row},{final_new_col}). Deactivating.")
                self.is_active = False # Fell off
                self.screen_x = -100


    def draw(self, surface):
        if self.screen_x > 0 and self.is_active:
            body_rect = pygame.Rect(
                self.screen_x - COILY_SNAKE_WIDTH // 2,
                self.screen_y - COILY_SNAKE_HEIGHT // 2,
                COILY_SNAKE_WIDTH, COILY_SNAKE_HEIGHT
            )
            pygame.draw.rect(surface, COLOR_COILY_SNAKE, body_rect)
            pygame.draw.rect(surface, COLOR_OUTLINE, body_rect, 1)

            # Eyes
            eye_size = 3
            eye_y_offset = COILY_SNAKE_HEIGHT // 4
            eye_x_offset = COILY_SNAKE_WIDTH // 4
            pygame.draw.circle(surface, COLOR_COILY_EYES, (body_rect.centerx - eye_x_offset, body_rect.centery - eye_y_offset), eye_size // 2)
            pygame.draw.circle(surface, COLOR_COILY_EYES, (body_rect.centerx + eye_x_offset, body_rect.centery - eye_y_offset), eye_size // 2)


# --- Game Reset Function ---
def reset_game():
    global score, game_state, player, coily, pyramid_cubes, player_death_timer, current_level
    print("Resetting game...")
    score = 0
    current_level = 1 # Reset level to 1
    player.reset_lives()
    player.reset_position()
    coily.reset() # Coily will now also reset its position and become active

    for cube in pyramid_cubes:
        cube.reset_color()

    start_cube_index = player.get_current_cube_index()
    if 0 <= start_cube_index < len(pyramid_cubes):
        pyramid_cubes[start_cube_index].change_color() # Initial landing

    game_state = STATE_PLAYING
    player_death_timer = 0 # Reset death timer


def start_next_level():
    global game_state, player, coily, pyramid_cubes, player_death_timer, current_level # Ensure current_level is global if used for print
    print(f"Starting next level: {current_level}")

    # Reset player to starting position for the new level
    player.reset_position()
    # Make sure player is active for the new level
    player.is_active = True 

    # Reset Coily for the new level (he should become active and reposition)
    coily.reset()
    coily.is_active = True


    # Reset all cubes to their initial colors
    for cube in pyramid_cubes:
        cube.reset_color()

    # Player lands on the first cube of the new level
    start_cube_index = player.get_current_cube_index()
    if 0 <= start_cube_index < len(pyramid_cubes):
        pyramid_cubes[start_cube_index].change_color() # No score for this initial landing

    # Set game state to playing
    game_state = STATE_PLAYING
    player_death_timer = 0 # Reset any death timer


# --- Game Setup ---
pygame.init()
pygame.mixer.init() # If you add sounds later
pygame.font.init()

try:
    pygame.mixer.music.load('background_music.mp3')
    pygame.mixer.music.play(-1)
except pygame.error as e:
    print(f"Error loading background music: {e}")

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Q*bert VGA Style")
clock = pygame.time.Clock()

try:
    game_font = pygame.font.SysFont('Consolas', 30) # Or "Arial"
    small_font = pygame.font.SysFont('Consolas', 20)
except pygame.error:
    game_font = pygame.font.Font(None, 35) # Fallback
    small_font = pygame.font.Font(None, 25)

pyramid_cubes = []
for r in range(PYRAMID_ROWS):
    for c in range(CUBES_PER_ROW[r]):
        pyramid_cubes.append(Cube(r, c))

player = Player(0, 0) # Start player at the top cube (0,0)
coily = Enemy()

score = 0
current_level = 1  # Initialize current level
game_state = STATE_PLAYING
player_death_timer = 0
PLAYER_DEATH_PAUSE = 1500 # Milliseconds for player death pause

# Initial landing on the first cube
start_cube_idx = player.get_current_cube_index()
if 0 <= start_cube_idx < len(pyramid_cubes):
    pyramid_cubes[start_cube_idx].change_color() # No score for initial landing

running = True

# --- Main Game Loop ---
while running:
    current_time_ticks = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            
            if game_state == STATE_GAME_OVER:
                if event.key == pygame.K_r:
                    reset_game()
            elif game_state == STATE_LEVEL_COMPLETE:
                if event.key == pygame.K_n:
                    start_next_level()
            
            elif game_state == STATE_PLAYING and player.is_active:
                moved_successfully = False # True if player lands on a valid cube
                fell_off_pyramid = False

                if event.key == pygame.K_LEFT:  # Up-Left
                    moved_successfully = player.move(-1, -1)
                elif event.key == pygame.K_UP: # Up-Right
                    moved_successfully = player.move(-1, 0)
                elif event.key == pygame.K_DOWN: # Down-Left
                    moved_successfully = player.move(1, 0)
                elif event.key == pygame.K_RIGHT: # Down-Right
                    moved_successfully = player.move(1, 1)

                # Check if player fell after attempting a move
                # player.move returns False if the target grid coordinates are off-pyramid
                if not moved_successfully and player.screen_x < 0 : # Check if off-screen (fell)
                    fell_off_pyramid = True

                if fell_off_pyramid:
                    player.die()
                    game_state = STATE_PLAYER_DIED
                    player_death_timer = current_time_ticks
                elif moved_successfully : # Player landed on a cube
                    current_cube_index = player.get_current_cube_index()
                    if 0 <= current_cube_index < len(pyramid_cubes):
                        landed_cube = pyramid_cubes[current_cube_index]
                        if landed_cube.change_color(): # True if color actually changed
                            score += 25
                        
                        # Check for level complete
                        all_cubes_target = all(c.is_target_color for c in pyramid_cubes)
                        if all_cubes_target:
                            game_state = STATE_LEVEL_COMPLETE
                            current_level += 1 # Increment level
                            score += 1000 # Bonus for level complete
                            play_sound("level_complete")
                            print(f"Level Complete! Advancing to level {current_level}")
                            coily.is_active = False # Coily might disappear or stop
                            # Consider adding a short delay or a "next level" screen here
                            # For now, it will just make Coily inactive and player can't move.
                            # A key press (e.g., in STATE_LEVEL_COMPLETE handler) could then call a function
                            # to reset cubes, player position, and reactivate Coily for the new level.
                    else:
                        # This case should ideally be covered by fell_off_pyramid
                        # but as a safeguard if player.move returned true but index is bad
                        print(f"Error: Player landed on invalid cube index: {current_cube_index} after move.")
                        player.die()
                        game_state = STATE_PLAYER_DIED
                        player_death_timer = current_time_ticks


    if game_state == STATE_PLAYER_DIED:
        if current_time_ticks - player_death_timer > PLAYER_DEATH_PAUSE:
            if player.lives <= 0:
                game_state = STATE_GAME_OVER
                play_sound("game_over")
            else:
                player.reset_position()
                coily.reset() # Reset Coily when player respawns
                # Recolor starting cube if it's not already target color
                start_cube_idx_respawn = player.get_current_cube_index()
                if 0 <= start_cube_idx_respawn < len(pyramid_cubes):
                    if not pyramid_cubes[start_cube_idx_respawn].is_target_color:
                         pyramid_cubes[start_cube_idx_respawn].change_color() # No score for respawn landing

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

    screen.fill(COLOR_BACKGROUND)
    for cube in pyramid_cubes:
        cube.draw(screen)
    
    if coily.is_active : coily.draw(screen) # Only draw Coily if active
    if player.is_active : player.draw(screen) # Only draw player if active (not during death pause)


    score_text = game_font.render(f"Score: {score}", True, VGA_TEXT_YELLOW)
    lives_text = game_font.render(f"Lives: {player.lives}", True, VGA_TEXT_YELLOW)
    screen.blit(score_text, (10, 10))
    screen.blit(lives_text, (SCREEN_WIDTH - lives_text.get_width() - 10, 10))

    if game_state == STATE_GAME_OVER:
        go_text = game_font.render("GAME OVER", True, VGA_RED)
        go_rect = go_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        screen.blit(go_text, go_rect)
        prompt_text = small_font.render("Press 'R' to Restart or 'ESC' to Exit", True, VGA_TEXT_YELLOW)
        prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        screen.blit(prompt_text, prompt_rect)

    elif game_state == STATE_LEVEL_COMPLETE:
        lc_text = game_font.render("LEVEL COMPLETE!", True, VGA_YELLOW)
        lc_rect = lc_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        screen.blit(lc_text, lc_rect)
        
        next_level_prompt_text = small_font.render(f"Press 'N' for Next Level ({current_level})", True, VGA_ORANGE)
        next_level_prompt_rect = next_level_prompt_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        screen.blit(next_level_prompt_text, next_level_prompt_rect)

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()
