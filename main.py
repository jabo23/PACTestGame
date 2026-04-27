import pygame
import random
import math

# constants
POINTER_WIDTH = 10
TARGET_WIDTH = 40

# pygame setup
pygame.init()
screen = pygame.display.set_mode((480, 800))
clock = pygame.time.Clock()
running = True
dt = 0


pygame.mouse.set_visible(False)

player_pos = pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2)

target_pos = pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2)

pygame.font.init()
font = pygame.font.SysFont('', 30)

score = 0

def target_hit():
    target_pos.x = random.randint(int(screen.get_width() * 0.1), int(screen.get_width() * 0.9))
    target_pos.y = random.randint(int(screen.get_height() * 0.1), int(screen.get_height() * 0.9))

def draw_target():
    pygame.draw.circle(screen, "red", target_pos, TARGET_WIDTH * 1.0)
    pygame.draw.circle(screen, "white", target_pos, TARGET_WIDTH * 0.75)
    pygame.draw.circle(screen, "red", target_pos, TARGET_WIDTH * 0.5)
    pygame.draw.circle(screen, "white", target_pos, TARGET_WIDTH * 0.25)

def distance(p1: pygame.Vector2, p2: pygame.Vector2):
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)

while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():

        if event.type == pygame.MOUSEBUTTONDOWN:
            if distance(target_pos, player_pos) <= POINTER_WIDTH + TARGET_WIDTH:
                target_hit()
                score += 1
            elif score != 0:
                score -= 1

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEMOTION:
            player_pos.x = pygame.mouse.get_pos()[0]
            player_pos.y = pygame.mouse.get_pos()[1]

    # fill the screen with a color to wipe away anything from last frame
    screen.fill("black")

    # Target
    draw_target()

    # Pointer
    pygame.draw.circle(screen, "aqua", player_pos, POINTER_WIDTH)

    screen.blit(font.render(f'Score: {score}', False, "white"), (int(screen.get_width() * 0.02), int(screen.get_height() * 0.02)))

    # flip() the display to put your work on screen
    pygame.display.flip()

    # limits FPS to 60
    # dt is delta time in seconds since last frame, used for framerate-
    # independent physics.
    dt = clock.tick(60) / 1000

pygame.quit()