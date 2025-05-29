import pygame

class Disc:
    """Represents a floating disc that Q*bert can use to return to the top."""
    def __init__(self, screen_x, screen_y, radius, color, cooldown_duration):
        self.screen_x = screen_x
        self.screen_y = screen_y
        self.radius = radius
        self.color = color
        self.active_color = color
        self.cooldown_color = (100, 100, 100) # Greyed out color for cooldown
        self.is_active = True
        self.COOLDOWN_DURATION = cooldown_duration
        self.cooldown_timer_start = 0 # Timestamp when cooldown begins

    def draw(self, surface):
        """Draws the disc on the screen."""
        current_color = self.active_color if self.is_active else self.cooldown_color
        pygame.draw.circle(surface, current_color, (self.screen_x, self.screen_y), self.radius)
        # Optional: Draw an outline
        pygame.draw.circle(surface, (0,0,0), (self.screen_x, self.screen_y), self.radius, 1)


    def activate(self):
        """Activates the disc, making it usable."""
        self.is_active = True
        self.cooldown_timer_start = 0
        print(f"Disc at ({self.screen_x}, {self.screen_y}) activated.")

    def deactivate(self):
        """Deactivates the disc and starts its cooldown."""
        self.is_active = False
        self.cooldown_timer_start = pygame.time.get_ticks()
        print(f"Disc at ({self.screen_x}, {self.screen_y}) deactivated. Cooldown started.")

    def update_cooldown(self):
        """Checks if the cooldown period has passed and reactivates the disc."""
        if not self.is_active:
            current_time = pygame.time.get_ticks()
            if current_time - self.cooldown_timer_start >= self.COOLDOWN_DURATION:
                self.activate()
