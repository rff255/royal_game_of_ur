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
GREEN           = (0, 255, 0)
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


def get_center_maker(tile_centers):
  side_length = tile_centers[1][0] - tile_centers[0][0]
  def get_center(player, index):
    if index >= 5 and index <= 12:
      return tile_centers[index-5]
    else:
      if index < 5:
        tile = tile_centers[4 - index]
      else:
        tile = tile_centers[20 - index]
      return tile[0], tile[1] + (side_length if player else -side_length)
  return get_center

def add_piece(surface, center, color=RED):
  pygame.draw.circle(surface, color, center, 25)

def remove_piece(surface, center, color=GREY):
  add_piece(surface, center, color)


class Player:
  def __init__(self, screen, side, color, tile_centers, tile_length):
    self.screen = screen
    self.side = side
    self.color = color
    self.tile_centers = tile_centers
    self.tile_length = tile_length
    self.pieces = [0]*14
    self.total = 7
    self.reserve = 0
    self.finished = 0

    self.reserve_centers = [
      (tile_centers[0][0] + i * 75,
      tile_centers[0][1] + self.tile_length * 2 * (1 if self.side else -1))
      for i in range(self.total)]

    for _ in range(self.total):
      self.add_reserve()

  def add_reserve(self):
    add_piece(self.screen, self.reserve_centers[self.reserve], self.color)
    self.reserve += 1

  def remove_reserve(self):
    if self.reserve > 0:
      self.reserve -= 1
      remove_piece(self.screen, self.reserve_centers[self.reserve])


def main():
  pygame.init()
  clock = pygame.time.Clock()

  screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
  pygame.display.set_caption('Royal Game of Ur')
  pygame.mouse.set_visible(True)

  background = pygame.Surface(screen.get_size()).convert()
  background.fill(GREY)
  tile_length = min(SCREEN_WIDTH // 14, SCREEN_HEIGHT // 5)

  tile_centers = []
  left_offset = 1
  for j in [1, 3]:
    for i in list(range(4)) + [6, 7]:
      pygame.draw.rect(background, WHITE, [(i + left_offset)*tile_length, j*tile_length, tile_length, tile_length], TILE_WIDTH)
  for i in range(8):
    tile_centers.append(pygame.draw.rect(background, WHITE, [(i + left_offset)*tile_length, 2*tile_length, tile_length, tile_length], TILE_WIDTH).center)
  # Color safe space differently
  pygame.draw.rect(background, GREEN, [(3 + left_offset)*tile_length, 2*tile_length, tile_length, tile_length], TILE_WIDTH).center

  get_center = get_center_maker(tile_centers)

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

  p = Player(background, 0, RED, tile_centers, tile_length)
  p = Player(background, 1, BLUE, tile_centers, tile_length)

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
