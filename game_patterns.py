import math
import random

WIDTH, HEIGHT = 800, 600

RED = (200, 0, 0)
BLUE = (0, 120, 215)
GREEN = (0, 200, 0)

class Laser:
    def __init__(self, x, y, angle, speed=6, color=RED, width=4, length=32):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.color = color
        self.width = width
        self.length = length
        self.active = True

    def update(self):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        if (self.x < -self.length or self.x > WIDTH + self.length or
            self.y < -self.length or self.y > HEIGHT + self.length):
            self.active = False

    def draw(self, surface):
        import pygame
        end_x = self.x + math.cos(self.angle) * self.length
        end_y = self.y + math.sin(self.angle) * self.length
        pygame.draw.line(surface, self.color, (self.x, self.y), (end_x, end_y), self.width)

def pattern_simple_radial(frame):
    lasers = []
    if frame % 60 == 0:
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
    (pattern_simple_radial, 8),   # 8 seconds
    (pattern_sweeping, 6),        # 6 seconds
    (pattern_random_burst, 10),   # 10 seconds
]

class PatternSwitcher:
    def __init__(self, patterns, fps=60):
        self.patterns = patterns
        self.current_index = 0
        self.frame = 0
        self.pattern_timer = 0
        self.fps = fps

    def get_current_pattern(self):
        pattern_func, duration = self.patterns[self.current_index]
        if self.pattern_timer >= duration * self.fps:
            self.current_index = (self.current_index + 1) % len(self.patterns)
            self.pattern_timer = 0
            self.frame = 0
            pattern_func, duration = self.patterns[self.current_index]
        self.pattern_timer += 1
        self.frame += 1
        return pattern_func, self.frame