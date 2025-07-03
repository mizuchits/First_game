import pygame
import sys
import os
import math
import random
import time

# Initialize Pygame
pygame.init()

# Set up display
WIDTH, HEIGHT = 1280, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("My 2D Game")

# Set up clock for FPS
clock = pygame.time.Clock()
FPS = 60

# Colors
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)
BLUE = (0, 120, 215)
GREEN = (0, 200, 0)
RED = (200, 0, 0)

# Fonts
font = pygame.font.SysFont(None, 48)
small_font = pygame.font.SysFont(None, 32)

# Load menu music
ASSET_PATH = os.path.join(os.path.dirname(__file__), "assets")
MENU_MUSIC_PATH = os.path.join(ASSET_PATH, "Clair Obscur Expedition 33 Lumière [Official Music Video].mp3")  # Change filename as needed

if os.path.exists(MENU_MUSIC_PATH):
    pygame.mixer.music.load(MENU_MUSIC_PATH)
else:
    print("Menu music not found at:", MENU_MUSIC_PATH)

# Button class
class Button:
    def __init__(self, text, x, y, w, h):
        self.text = text
        self.rect = pygame.Rect(x, y, w, h)
        self.color = GRAY
        self.hover_color = BLUE
        self.current_color = self.color

    def draw(self, surface):
        pygame.draw.rect(surface, self.current_color, self.rect, border_radius=8)
        text_surf = font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def is_hovered(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

    def update(self, mouse_pos):
        self.current_color = self.hover_color if self.is_hovered(mouse_pos) else self.color

# Slider class for volume
class Slider:
    def __init__(self, x, y, w, h, min_val, max_val, start_val):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.value = start_val
        self.handle_rect = pygame.Rect(x + int((start_val - min_val) / (max_val - min_val) * w) - 10, y - 5, 20, h + 10)
        self.dragging = False

    def draw(self, surface):
        pygame.draw.rect(surface, WHITE, self.rect, 2)
        pygame.draw.rect(surface, GREEN if self.dragging else GRAY, self.handle_rect)
        value_text = small_font.render(f"{int(self.value * 100)}%", True, WHITE)
        surface.blit(value_text, (self.rect.right + 20, self.rect.centery - value_text.get_height() // 2))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.handle_rect.collidepoint(event.pos):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            x = max(self.rect.left, min(event.pos[0], self.rect.right))
            self.handle_rect.x = x - self.handle_rect.width // 2
            rel_x = x - self.rect.left
            self.value = self.min_val + (rel_x / self.rect.width) * (self.max_val - self.min_val)

    def get_value(self):
        return self.value

# Player class for bullet hell movement
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 16
        self.color = BLUE
        self.speed = 5
        self.dash_distance = 80
        self.dash_cooldown = 60
        self.dash_timer = 0
        self.hitbox_radius = 4
        self.alive = True

    def handle_input(self, keys):
        if not self.alive:
            return
        dx, dy = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += 1
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071
        self.x += dx * self.speed
        self.y += dy * self.speed
        self.x = max(self.radius, min(WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(HEIGHT - self.radius, self.y))

    def dash(self, keys):
        if self.dash_timer == 0 and self.alive:
            dx, dy = 0, 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                dx -= 1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx += 1
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                dy -= 1
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                dy += 1
            if dx == 0 and dy == 0:
                dy = -1
            if dx != 0 and dy != 0:
                dx *= 0.7071
                dy *= 0.7071
            self.x += dx * self.dash_distance
            self.y += dy * self.dash_distance
            self.x = max(self.radius, min(WIDTH - self.radius, self.x))
            self.y = max(self.radius, min(HEIGHT - self.radius, self.y))
            self.dash_timer = self.dash_cooldown

    def update_dash_timer(self):
        if self.dash_timer > 0:
            self.dash_timer -= 1

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.hitbox_radius)
        if self.dash_timer > 0 and self.alive:
            cooldown_text = small_font.render(f"Dash CD: {self.dash_timer//FPS + 1}s", True, RED)
            surface.blit(cooldown_text, (10, 10))

    def is_hit(self, lasers):
        if not self.alive:
            return False
        for laser in lasers:
            # Distance from hitbox to laser line segment
            lx, ly = laser.x, laser.y
            ex = lx + math.cos(laser.angle) * laser.length
            ey = ly + math.sin(laser.angle) * laser.length
            px, py = self.x, self.y
            # Closest point on the laser segment to the player
            dx, dy = ex - lx, ey - ly
            if dx == 0 and dy == 0:
                dist = math.hypot(px - lx, py - ly)
            else:
                t = max(0, min(1, ((px - lx) * dx + (py - ly) * dy) / (dx * dx + dy * dy)))
                closest_x = lx + t * dx
                closest_y = ly + t * dy
                dist = math.hypot(px - closest_x, py - closest_y)
            if dist <= self.hitbox_radius + laser.width // 2:
                return True
        return False

class Laser:
    def __init__(self, x, y, angle, speed=6, color=RED, width=4, length=32):
        self.x = x
        self.y = y
        self.angle = angle  # in radians
        self.speed = speed
        self.color = color
        self.width = width
        self.length = length
        self.active = True

    def update(self):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        # Deactivate if out of screen
        if (self.x < -self.length or self.x > WIDTH + self.length or
            self.y < -self.length or self.y > HEIGHT + self.length):
            self.active = False

    def draw(self, surface):
        end_x = self.x + math.cos(self.angle) * self.length
        end_y = self.y + math.sin(self.angle) * self.length
        pygame.draw.line(surface, self.color, (self.x, self.y), (end_x, end_y), self.width)

class Level:
    def __init__(self, pattern_func):
        self.pattern_func = pattern_func
        self.lasers = []
        self.frame = 0

    def update(self, player):
        self.frame += 1
        # Generate new lasers according to the pattern
        new_lasers = self.pattern_func(self.frame)
        if new_lasers:
            self.lasers.extend(new_lasers)
        # Update lasers
        for laser in self.lasers:
            laser.update()
        # Remove inactive lasers
        self.lasers = [l for l in self.lasers if l.active]

    def draw(self, surface):
        for laser in self.lasers:
            laser.draw(surface)

# Example pattern functions
def pattern_simple_radial(frame):
    lasers = []
    if frame % 60 == 0:  # Every second
        center_x, center_y = WIDTH // 2, 100
        for i in range(8):
            angle = i * (2 * math.pi / 8)
            lasers.append(Laser(center_x, center_y, angle))
    return lasers

def pattern_sweeping(frame):
    lasers = []
    if frame % 10 == 0:
        angle = math.pi / 2 + math.sin(frame / 60) * math.pi / 4
        lasers.append(Laser(random.randint(100, WIDTH-100), 0, angle, speed=8, color=BLUE, width=6, length=48))
    return lasers

def pattern_random_burst(frame):
    lasers = []
    if frame % 90 == 0:
        for _ in range(12):
            angle = random.uniform(0, 2 * math.pi)
            lasers.append(Laser(WIDTH//2, HEIGHT//2, angle, speed=4, color=GREEN, width=3, length=24))
    return lasers

LEVEL_PATTERNS = [
    pattern_simple_radial,
    pattern_sweeping,
    pattern_random_burst,
]

# Main menu state
MENU = "menu"
GAME = "game"
SETTINGS = "settings"
state = MENU

# Button positions
button_width, button_height = 250, 60
start_x = (WIDTH - button_width) // 2
start_y = HEIGHT // 2 - button_height
settings_y = start_y + button_height + 20

start_button = Button("Start", start_x, start_y, button_width, button_height)
settings_button = Button("Settings", start_x, settings_y, button_width, button_height)

# Settings controls
slider_width, slider_height = 300, 10
slider_x = (WIDTH - slider_width) // 2
slider_y = HEIGHT // 2 - 40
volume_slider = Slider(slider_x, slider_y, slider_width, slider_height, 0.0, 1.0, 0.5)

binds_button = Button("Button Binds (Coming Soon)", slider_x, slider_y + 60, slider_width, 40)

def draw_menu():
    screen.fill(DARK_GRAY)
    mouse_pos = pygame.mouse.get_pos()
    start_button.update(mouse_pos)
    settings_button.update(mouse_pos)
    start_button.draw(screen)
    settings_button.draw(screen)

def draw_settings():
    screen.fill((30, 30, 30))
    settings_text = font.render("Settings", True, WHITE)
    screen.blit(settings_text, (WIDTH // 2 - settings_text.get_width() // 2, 80))
    volume_text = small_font.render("General Volume", True, WHITE)
    screen.blit(volume_text, (slider_x, slider_y - 30))
    volume_slider.draw(screen)
    binds_button.draw(screen)
    esc_text = small_font.render("Press ESC to return", True, WHITE)
    screen.blit(esc_text, (WIDTH // 2 - esc_text.get_width() // 2, HEIGHT - 60))

def bullet_hell_game():
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.stop()
    player = Player(WIDTH // 2, HEIGHT // 2)
    level_index = 0
    level = Level(LEVEL_PATTERNS[level_index])
    running = True
    death = False
    death_time = 0
    show_death_screen = False

    # Death screen buttons
    btn_width, btn_height = 220, 60
    retry_btn = Button("Retry", WIDTH // 2 - btn_width // 2, HEIGHT // 2 + 40, btn_width, btn_height)
    quit_btn = Button("Quit to Menu", WIDTH // 2 - btn_width // 2, HEIGHT // 2 + 120, btn_width, btn_height)

    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if not death and not show_death_screen:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if event.key == pygame.K_SPACE:
                        keys = pygame.key.get_pressed()
                        player.dash(keys)
                    if event.key == pygame.K_TAB:
                        level_index = (level_index + 1) % len(LEVEL_PATTERNS)
                        level = Level(LEVEL_PATTERNS[level_index])
            elif show_death_screen:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    retry_btn.update(mouse_pos)
                    quit_btn.update(mouse_pos)
                    if retry_btn.is_hovered(mouse_pos):
                        # Restart game
                        return bullet_hell_game()
                    elif quit_btn.is_hovered(mouse_pos):
                        return  # Return to menu

        if not death and not show_death_screen:
            keys = pygame.key.get_pressed()
            player.handle_input(keys)
            player.update_dash_timer()
            level.update(player)
            if player.is_hit(level.lasers):
                player.alive = False
                death = True
                death_time = pygame.time.get_ticks()
        elif death and not show_death_screen:
            # Wait 1 second before showing death screen
            if pygame.time.get_ticks() - death_time > 1000:
                show_death_screen = True

        screen.fill((0, 0, 0))
        level.draw(screen)
        player.draw(screen)

        if not death and not show_death_screen:
            info_text = small_font.render(
                "Move: Arrow keys/WASD | Dash: SPACE | Next Pattern: TAB | ESC: Menu", True, WHITE)
            screen.blit(info_text, (WIDTH // 2 - info_text.get_width() // 2, HEIGHT - 40))
            level_text = small_font.render(f"Pattern {level_index + 1}/{len(LEVEL_PATTERNS)}", True, WHITE)
            screen.blit(level_text, (10, HEIGHT - 40))
        elif show_death_screen:
            # Draw death screen
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            death_text = font.render("You Died!", True, RED)
            screen.blit(death_text, (WIDTH // 2 - death_text.get_width() // 2, HEIGHT // 2 - 80))
            retry_btn.update(pygame.mouse.get_pos())
            quit_btn.update(pygame.mouse.get_pos())
            retry_btn.draw(screen)
            quit_btn.draw(screen)

        pygame.display.flip()

def main():
    global state
    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if state == MENU:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if start_button.is_hovered(pygame.mouse.get_pos()):
                        bullet_hell_game()  # Start bullet hell game when Start is pressed
                        # After game ends, return to menu and restart music
                        if os.path.exists(MENU_MUSIC_PATH):
                            pygame.mixer.music.load(MENU_MUSIC_PATH)
                            pygame.mixer.music.play(-1)
                            pygame.mixer.music.set_volume(volume_slider.get_value())
                        state = MENU
                    elif settings_button.is_hovered(pygame.mouse.get_pos()):
                        state = SETTINGS

            elif state == SETTINGS:
                volume_slider.handle_event(event)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    state = MENU

        # Play menu music in both MENU and SETTINGS
        if state in (MENU, SETTINGS):
            if not pygame.mixer.music.get_busy() and os.path.exists(MENU_MUSIC_PATH):
                pygame.mixer.music.play(-1)
            pygame.mixer.music.set_volume(volume_slider.get_value())
            if state == MENU:
                draw_menu()
            else:
                draw_settings()

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()