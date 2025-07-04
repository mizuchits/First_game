import pygame
import sys
import os
import math
import random
import time
import json
from settings import load_settings, save_settings
from game_patterns import LEVEL_PATTERNS, PatternSwitcher

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
MENU_MUSIC_PATH = os.path.join(ASSET_PATH, "Bocchi the Rock! - Guitar, Loneliness and Blue Planet [instrumental] (ギターと孤独と蒼い惑星, 기타와 고독과 푸른 행성).mp3")  # Change filename as needed

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

def get_key_state(settings):
    """Return a dict mapping action names to whether their key is pressed."""
    pressed = pygame.key.get_pressed()
    keymap = {}
    for action, keyname in settings["key_bindings"].items():
        try:
            key_const = getattr(pygame, f'K_{keyname.lower()}')
        except AttributeError:
            # fallback for special keys
            key_const = pygame.key.key_code(keyname)
        keymap[action] = pressed[key_const]
    return keymap

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

    def handle_input(self, keymap):
        if not self.alive:
            return
        dx, dy = 0, 0
        if keymap.get("move_left"):
            dx -= 1
        if keymap.get("move_right"):
            dx += 1
        if keymap.get("move_up"):
            dy -= 1
        if keymap.get("move_down"):
            dy += 1
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071
        self.x += dx * self.speed
        self.y += dy * self.speed
        self.x = max(self.radius, min(WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(HEIGHT - self.radius, self.y))

    def dash(self, keymap):
        if self.dash_timer == 0 and self.alive:
            dx, dy = 0, 0
            if keymap.get("move_left"):
                dx -= 1
            if keymap.get("move_right"):
                dx += 1
            if keymap.get("move_up"):
                dy -= 1
            if keymap.get("move_down"):
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
# Main menu state
MENU = "menu"
GAME = "game"
SETTINGS = "settings"
BUTTON_BINDS = "button_binds"
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

binds_button = Button("Control Binds", slider_x, slider_y + 60, slider_width, 40)

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

def draw_button_binds(settings, selected_action):
    screen.fill((20, 20, 40))
    title = font.render("Control Binds", True, WHITE)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 60))
    y = 160
    x = WIDTH // 2 - 200
    for action, key in settings["key_bindings"].items():
        action_name = action.replace("_", " ").capitalize()
        if selected_action == action:
            color = BLUE
        else:
            color = WHITE
        action_text = small_font.render(f"{action_name}:", True, color)
        key_text = small_font.render(f"{key.upper()}", True, color)
        screen.blit(action_text, (x, y))
        pygame.draw.rect(screen, color, (x + 220, y, 120, 36), 2 if selected_action == action else 1)
        screen.blit(key_text, (x + 230, y))
        y += 60
    esc_text = small_font.render("Press ESC to return", True, WHITE)
    screen.blit(esc_text, (WIDTH // 2 - esc_text.get_width() // 2, HEIGHT - 60))

def button_binds_menu(settings):
    running = True
    selected_action = None
    actions = list(settings["key_bindings"].keys())
    action_rects = []
    x = WIDTH // 2 - 200
    y = 160
    for action in actions:
        rect = pygame.Rect(x + 220, y, 120, 36)
        action_rects.append((action, rect))
        y += 60

    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if selected_action is None:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    for action, rect in action_rects:
                        if rect.collidepoint(mouse_pos):
                            selected_action = action
                            break
            else:
                if event.type == pygame.KEYDOWN:
                    # Update the key binding
                    key_name = pygame.key.name(event.key)
                    settings["key_bindings"][selected_action] = key_name
                    from settings import save_settings
                    save_settings(settings)
                    selected_action = None

        draw_button_binds(settings, selected_action)
        pygame.display.flip()

def bullet_hell_game():
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.stop()
    settings = load_settings()
    player = Player(WIDTH // 2, HEIGHT // 2)
    level_index = 0
    level = Level(LEVEL_PATTERNS[level_index])
    running = True
    death = False
    death_time = 0
    show_death_screen = False

    btn_width, btn_height = 220, 60
    retry_btn = Button("Retry", WIDTH // 2 - btn_width // 2, HEIGHT // 2 + 40, btn_width, btn_height)
    quit_btn = Button("Quit to Menu", WIDTH // 2 - btn_width // 2, HEIGHT // 2 + 120, btn_width, btn_height)

    # Pattern switcher for dynamic laser patterns
    pattern_switcher = PatternSwitcher(LEVEL_PATTERNS, fps=FPS)
    lasers = []

    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if not death and not show_death_screen:
                if event.type == pygame.KEYDOWN:
                    # Use the dash key from settings
                    dash_key = settings["key_bindings"].get("dash", "space")
                    try:
                        dash_key_const = getattr(pygame, f'K_{dash_key.lower()}')
                    except AttributeError:
                        dash_key_const = pygame.key.key_code(dash_key)
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if event.key == dash_key_const:
                        keymap = get_key_state(settings)
                        player.dash(keymap)
                    if event.key == pygame.K_TAB:
                        level_index = (level_index + 1) % len(LEVEL_PATTERNS)
                        level = Level(LEVEL_PATTERNS[level_index])
            elif show_death_screen:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    retry_btn.update(mouse_pos)
                    quit_btn.update(mouse_pos)
                    if retry_btn.is_hovered(mouse_pos):
                        return bullet_hell_game()
                    elif quit_btn.is_hovered(mouse_pos):
                        return

        if not death and not show_death_screen:
            keymap = get_key_state(settings)
            player.handle_input(keymap)
            player.update_dash_timer()
            # Update lasers using the pattern switcher
            pattern_func, pattern_frame = pattern_switcher.get_current_pattern()
            new_lasers = pattern_func(pattern_frame)
            if new_lasers:
                lasers.extend(new_lasers)
            for laser in lasers:
                laser.update()
            # Check for player collisions with lasers
            if player.is_hit(lasers):
                player.alive = False
                death = True
                death_time = pygame.time.get_ticks()
        elif death and not show_death_screen:
            if pygame.time.get_ticks() - death_time > 1000:
                show_death_screen = True

        screen.fill((0, 0, 0))
        # Draw lasers and player
        for laser in lasers:
            laser.draw(screen)
        player.draw(screen)

        if not death and not show_death_screen:
            info_text = small_font.render(
                "Move: Your binds | Dash: Your bind | Next Pattern: TAB | ESC: Menu", True, WHITE)
            screen.blit(info_text, (WIDTH // 2 - info_text.get_width() // 2, HEIGHT - 40))
            level_text = small_font.render(f"Pattern {level_index + 1}/{len(LEVEL_PATTERNS)}", True, WHITE)
            screen.blit(level_text, (10, HEIGHT - 40))
        elif show_death_screen:
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
    # Load settings at start
    from settings import load_settings, save_settings
    settings = load_settings()
    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if state == MENU:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if start_button.is_hovered(pygame.mouse.get_pos()):
                        bullet_hell_game()
                        if os.path.exists(MENU_MUSIC_PATH):
                            pygame.mixer.music.load(MENU_MUSIC_PATH)
                            pygame.mixer.music.play(-1)
                            pygame.mixer.music.set_volume(volume_slider.get_value())
                        state = MENU
                    elif settings_button.is_hovered(pygame.mouse.get_pos()):
                        state = SETTINGS

            elif state == SETTINGS:
                volume_slider.handle_event(event)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if binds_button.is_hovered(pygame.mouse.get_pos()):
                        # Open button binds menu
                        button_binds_menu(settings)
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