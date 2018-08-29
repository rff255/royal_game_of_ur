#!/usr/bin/python3

import os
import operator
import random
import math

import pygame
from pygame.locals import *

if not pygame.font: print ('Warning, fonts disabled')
if not pygame.mixer: print ('Warning, sound disabled')

main_dir = os.path.split(os.path.abspath(__file__))[0]
data_dir = os.path.join(main_dir, 'data')


SCREEN_WIDTH    = 1920
SCREEN_HEIGHT   = 1080

BLACK           = (0, 0, 0)
GREY            = (100, 100, 100)
WHITE           = (255, 255, 255)
RED             = (255, 0, 0)
BLUE            = (0, 0, 255)

TILE_WIDTH      = 10


def draw_triangle(surface, color, center, side, thickness=5):
  x, y = center
  height = int(side / 2 * math.sqrt(3))
  vertices = [(x - side, y + height), ((x + side), y + height), (x, y - height)]
  pygame.draw.polygon(surface, color, vertices, thickness)
  spot_y_center = int(y - height + 2 * height / math.sqrt(3))
  return x, spot_y_center


def roll_dice(surface, center, radius=10):
  color = WHITE if random.randint(0, 1) else BLACK
  pygame.draw.circle(surface, color, (center[0], center[1]), radius)


def main():
  pygame.init()
  clock = pygame.time.Clock()

  screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
  pygame.display.set_caption('Royal Game of Ur')
  pygame.mouse.set_visible(True)

  background = pygame.Surface(screen.get_size()).convert()
  background.fill(GREY)
  tile_length = min(SCREEN_WIDTH // 14, SCREEN_HEIGHT // 5)

  left_offset = 1
  for j in [1, 3]:
    for i in list(range(4)) + [6, 7]:
      pygame.draw.rect(background, WHITE, [(i + left_offset)*tile_length, j*tile_length, tile_length, tile_length], TILE_WIDTH)
  for i in range(8):
    if i == 5:
      pygame.draw.rect(background, WHITE, [(i + left_offset)*tile_length, 2*tile_length, tile_length, tile_length], TILE_WIDTH*3)
    else:
      pygame.draw.rect(background, WHITE, [(i + left_offset)*tile_length, 2*tile_length, tile_length, tile_length], TILE_WIDTH)

  dice_centers = [((9 + left_offset) * tile_length + (i * tile_length), 2 * tile_length + tile_length // 3) for i in range(4)]
  spot_centers = []
  for center in dice_centers:
    spot_center = draw_triangle(background, WHITE, center, 3 * tile_length // 7)
    roll_dice(background, spot_center)
    spot_centers.append(spot_center)


  if pygame.font:
    font = pygame.font.Font(None, 100)

    rolled_text = font.render("You rolled a:", True, RED, GREY)
    rolled_text_pos = rolled_text.get_rect()
    rolled_text_pos.midtop = ((10 + left_offset) * tile_length, 3 * tile_length)
    background.blit(rolled_text, rolled_text_pos)

    button_text = font.render("Roll", True, BLUE, GREY)
    button_text_pos = button_text.get_rect()
    button_text_pos.top = 1 * tile_length
    button_text_pos.left = rolled_text_pos.left
    background.blit(button_text, button_text_pos)


  running = True
  while running:
    for event in pygame.event.get():
      if event.type == QUIT:
        running = False

    screen.blit(background, (0, 0))

    pygame.display.update()
    clock.tick(60)


  pygame.quit()

if __name__ == '__main__':
  main()
