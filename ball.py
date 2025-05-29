import pygame
import random
from QBert import get_cube_screen_center_pos, PYRAMID_ROWS, CUBES_PER_ROW, play_sound

class Ball:
    """Represents a bouncing ball enemy."""
    def __init__(self, start_row, start_col, color, radius, move_interval):
        self.initial_start_row = start_row # Store initial for reset
        self.initial_start_col = start_col # Store initial for reset
        self.grid_row = start_row
        self.grid_col = start_col
        self.color = color
        self.radius = radius
        self.move_interval = move_interval
        self.last_move_time = pygame.time.get_ticks()
        self.is_active = False # Start inactive
        self.screen_x = -100 # Off-screen initially
        self.screen_y = -100 # Off-screen initially
        # self.update_screen_pos() # Don't call if starting inactive off-screen

    def update_screen_pos(self):
        """Updates the ball's screen position based on grid position."""
        pos = get_cube_screen_center_pos(self.grid_row, self.grid_col)
        if pos:
            # Ball's center Y should be slightly above the center of the cube's top face
            self.screen_x = pos[0]
            self.screen_y = pos[1] - self.radius # Center ball on top face center, adjusted by radius
            return True
        else:
            self.screen_x = -100 # Off screen
            self.screen_y = -100
            self.is_active = False # If position is invalid, ball is not active
            return False

    def reset(self, start_row=None, start_col=None):
        """Resets the ball's position and activates it."""
        # Use initial start_row/col if specific ones aren't provided
        self.grid_row = start_row if start_row is not None else self.initial_start_row
        self.grid_col = start_col if start_col is not None else self.initial_start_col
        
        # Ensure the reset position is valid
        if not (0 <= self.grid_row < PYRAMID_ROWS and \
                0 <= self.grid_col < CUBES_PER_ROW[self.grid_row]):
            # Fallback to a default safe position if provided start_row/col is invalid
            print(f"Warning: Invalid reset position ({self.grid_row}, {self.grid_col}) for ball. Defaulting.")
            self.grid_row = 1 # Example: second row
            if PYRAMID_ROWS > 1 and CUBES_PER_ROW[1] > 0:
                 self.grid_col = random.randint(0, CUBES_PER_ROW[1] -1)
            else: # Fallback if pyramid is very small
                self.grid_row = 0
                self.grid_col = 0


        self.is_active = True
        self.update_screen_pos()
        self.last_move_time = pygame.time.get_ticks()
        print(f"Ball reset to ({self.grid_row}, {self.grid_col})")


    def move(self):
        """Moves the ball down the pyramid randomly."""
        if not self.is_active:
            return

        current_time = pygame.time.get_ticks()
        if current_time - self.last_move_time > self.move_interval:
            self.last_move_time = current_time
            
            next_row = self.grid_row + 1
            if next_row >= PYRAMID_ROWS: # Fallen off the bottom
                self.is_active = False
                self.update_screen_pos() # Move to off-screen coordinates
                # play_sound("fall") # Optional: sound for ball falling off
                print(f"Ball fell off bottom from ({self.grid_row}, {self.grid_col})")
                return

            possible_next_cols = []
            # Potential next left cube: (next_row, self.grid_col)
            if 0 <= self.grid_col < CUBES_PER_ROW[next_row]:
                possible_next_cols.append(self.grid_col)
            
            # Potential next right cube: (next_row, self.grid_col + 1)
            if 0 <= self.grid_col + 1 < CUBES_PER_ROW[next_row]:
                possible_next_cols.append(self.grid_col + 1)

            if not possible_next_cols: # No valid moves down (e.g., edge of pyramid)
                self.is_active = False
                self.update_screen_pos()
                # play_sound("fall") # Optional
                print(f"Ball has no valid moves from ({self.grid_row}, {self.grid_col})")
                return

            # Choose one of the valid next columns randomly
            next_col = random.choice(possible_next_cols)
            
            self.grid_row = next_row
            self.grid_col = next_col
            
            if self.update_screen_pos(): # True if new position is valid
                play_sound("enemy_hop") # Using enemy_hop for now, can change to "ball_bounce"
            else: # Should be caught by is_active False in update_screen_pos if it falls off
                # This else might be redundant if update_screen_pos handles deactivation
                print(f"Ball moved to invalid position ({self.grid_row}, {self.grid_col})")

    def draw(self, surface):
        """Draws the ball on the screen."""
        if self.is_active and self.screen_x > 0: # screen_x > 0 as a quick check for on-screen
            pygame.draw.circle(surface, self.color, (self.screen_x, self.screen_y), self.radius)
            # Optional: draw an outline for the ball
            # pygame.draw.circle(surface, VGA_BLACK, (self.screen_x, self.screen_y), self.radius, 1)

# Example usage (not part of the class, for testing if run standalone)
if __name__ == '__main__':
    # This block is for testing Ball class independently.
    # It requires some QBert constants to be available or mocked.
    # For full integration, import Ball into QBert.py.

    # Mock necessary QBert constants for standalone testing
    PYRAMID_ROWS = 7
    CUBES_PER_ROW = [i + 1 for i in range(PYRAMID_ROWS)]
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    PYRAMID_TOP_X = SCREEN_WIDTH // 2
    PYRAMID_TOP_Y = 100
    ISO_CUBE_WIDTH = 80
    ISO_CUBE_TOP_H = 50
    GRID_COL_SPACING = ISO_CUBE_WIDTH
    GRID_ROW_SPACING = ISO_CUBE_TOP_H * 0.75
    VGA_RED = (170, 0, 0)

    def get_cube_screen_center_pos(grid_row, grid_col):
        if not (0 <= grid_row < PYRAMID_ROWS and 0 <= grid_col < CUBES_PER_ROW[grid_row]):
            return None
        screen_x = PYRAMID_TOP_X + (grid_col - grid_row / 2.0) * GRID_COL_SPACING
        screen_y = PYRAMID_TOP_Y + grid_row * GRID_ROW_SPACING
        return int(screen_x), int(screen_y)

    def play_sound(sound_name):
        print(f"Mock play_sound: {sound_name}")


    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Ball Test")
    clock = pygame.time.Clock()

    # Create a ball instance
    test_ball = Ball(start_row=0, start_col=0, color=VGA_RED, radius=10, move_interval=1000)
    test_ball.reset() # Activate the ball

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        test_ball.move()

        screen.fill((0,0,0)) # Black background
        test_ball.draw(screen)
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
