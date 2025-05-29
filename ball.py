import pygame
import random

class Ball:
    """Represents a bouncing ball enemy."""
    def __init__(self, start_row, start_col, color, radius, move_interval, 
                 get_cube_screen_center_pos_func, play_sound_func, 
                 pyramid_rows_config, cubes_per_row_config):
        self.initial_start_row = start_row # Store initial for reset
        self.initial_start_col = start_col # Store initial for reset
        self.grid_row = start_row
        self.grid_col = start_col
        self.color = color
        self.radius = radius
        self.move_interval = move_interval
        
        # Store injected dependencies
        self.get_cube_screen_center_pos = get_cube_screen_center_pos_func
        self.play_sound = play_sound_func
        self.PYRAMID_ROWS = pyramid_rows_config
        self.CUBES_PER_ROW = cubes_per_row_config

        self.last_move_time = pygame.time.get_ticks()
        self.is_active = False # Start inactive
        self.screen_x = -100 # Off-screen initially
        self.screen_y = -100 # Off-screen initially
        # self.update_screen_pos() # Don't call if starting inactive off-screen

    def update_screen_pos(self):
        """Updates the ball's screen position based on grid position."""
        pos = self.get_cube_screen_center_pos(self.grid_row, self.grid_col)
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
        if not (0 <= self.grid_row < self.PYRAMID_ROWS and \
                0 <= self.grid_col < self.CUBES_PER_ROW[self.grid_row]):
            # Fallback to a default safe position if provided start_row/col is invalid
            print(f"Warning: Invalid reset position ({self.grid_row}, {self.grid_col}) for ball. Defaulting.")
            self.grid_row = 1 # Example: second row
            if self.PYRAMID_ROWS > 1 and self.CUBES_PER_ROW[1] > 0:
                 self.grid_col = random.randint(0, self.CUBES_PER_ROW[1] -1)
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
            if next_row >= self.PYRAMID_ROWS: # Fallen off the bottom
                self.is_active = False
                self.update_screen_pos() # Move to off-screen coordinates
                # self.play_sound("fall") # Optional: sound for ball falling off
                print(f"Ball fell off bottom from ({self.grid_row}, {self.grid_col})")
                return

            possible_next_cols = []
            # Potential next left cube: (next_row, self.grid_col)
            if 0 <= self.grid_col < self.CUBES_PER_ROW[next_row]:
                possible_next_cols.append(self.grid_col)
            
            # Potential next right cube: (next_row, self.grid_col + 1)
            if 0 <= self.grid_col + 1 < self.CUBES_PER_ROW[next_row]:
                possible_next_cols.append(self.grid_col + 1)

            if not possible_next_cols: # No valid moves down (e.g., edge of pyramid)
                self.is_active = False
                self.update_screen_pos()
                # self.play_sound("fall") # Optional
                print(f"Ball has no valid moves from ({self.grid_row}, {self.grid_col})")
                return

            # Choose one of the valid next columns randomly
            next_col = random.choice(possible_next_cols)
            
            self.grid_row = next_row
            self.grid_col = next_col
            
            if self.update_screen_pos(): # True if new position is valid
                self.play_sound("ball_bounce") # Changed from "enemy_hop" to specific sound
            else: # Should be caught by is_active False in update_screen_pos if it falls off
                # This else might be redundant if update_screen_pos handles deactivation
                print(f"Ball moved to invalid position ({self.grid_row}, {self.grid_col})")

    def draw(self, surface):
        """Draws the ball on the screen."""
        if self.is_active and self.screen_x > 0: # screen_x > 0 as a quick check for on-screen
            pygame.draw.circle(surface, self.color, (self.screen_x, self.screen_y), self.radius)
            # Optional: draw an outline for the ball
            # pygame.draw.circle(surface, (0,0,0), (self.screen_x, self.screen_y), self.radius, 1)
