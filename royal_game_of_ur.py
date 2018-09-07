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


def draw_dice(surface, center, radius=10):
  roll = random.randint(0, 1)
  color = WHITE if roll else BLACK
  pygame.draw.circle(surface, color, (center[0], center[1]), radius)
  return roll

def roll_dice(surface, centers, radius=10):
  total = 0
  for center in centers:
    total += draw_dice(surface, center, radius)
  return total


def add_piece(surface, center, color=RED):
  pygame.draw.circle(surface, color, center, 25)

def remove_piece(surface, center, color=GREY):
  add_piece(surface, center, color)


class Player:
  def __init__(self, screen, side, color, tiles, tile_length):
    self.screen = screen
    self.side = side
    self.color = color
    safe_tiles = [t.move(0, tile_length if side else -tile_length) for t in tiles]
    self.tiles = safe_tiles[:4] + tiles + safe_tiles[-2:]
    self.tile_length = tile_length
    self.pieces = [0]*14
    self.total = 7
    self.reserve = 0
    self.finished = 0
    self.other = None

    self.reserve_centers = [
      (tiles[0].center[0] + i * 75,
      tiles[0].center[1] + self.tile_length * 2 * (1 if self.side else -1))
      for i in range(self.total)]

    for _ in range(self.total):
      self.add_reserve()

  def add_reserve(self):
    if self.reserve < self.total:
      add_piece(self.screen, self.reserve_centers[self.reserve], self.color)
      self.reserve += 1
      return True
    return False

  def remove_reserve(self):
    if self.reserve > 0:
      self.reserve -= 1
      remove_piece(self.screen, self.reserve_centers[self.reserve])
      return True
    return False

  def add_piece(self, index):
    if not self.pieces[index] and self.remove_reserve():
      if self.is_shared(index) and self.other.pieces[index]:
        self.other.remove_piece(index)
      add_piece(self.screen, self.tiles[index].center, self.color)
      self.pieces[index] = 1
      return True
    return False

  def remove_piece(self, index):
    if self.pieces[index] and self.add_reserve():
      remove_piece(self.screen, self.tiles[index].center)
      self.pieces[index] = 0
      return True
    return False

  def get_index(self, pos):
    try:
      return [tile.collidepoint(pos) for tile in self.tiles].index(True)
    except ValueError:
      return None

  def is_shared(self, index):
    return index >= 4 and index <= 11

class Board:
  def __init__(self, screen, tiles, tile_length):
    self.screen = screen
    self.tiles = tiles
    self.tile_length = tile_length

    self.top_player = Player(screen, 0, RED, tiles, tile_length)
    self.bottom_player = Player(screen, 1, BLUE, tiles, tile_length)
    self.top_player.other = self.bottom_player
    self.bottom_player.other = self.top_player

    self.player_turn = 0

  def init_font(self, spot_centers, rolled_text_pos, button_text_pos):
    self.font = pygame.font.Font(None, 100)
    self.spot_centers = spot_centers
    self.rolled_text_pos = rolled_text_pos
    self.button_text_pos = button_text_pos

  def click_roll(self):
    rolled_color, button_color = (RED, WHITE) if self.player_turn else (BLUE, WHITE)
    rolled_text = self.font.render("You rolled a: %d" % (roll_dice(self.screen, self.spot_centers),), True, rolled_color, GREY)
    button_text = self.font.render("Roll", True, button_color, GREY)
    self.screen.blit(rolled_text, self.rolled_text_pos)
    self.screen.blit(button_text, self.button_text_pos)
    self.player_turn = 1 - self.player_turn

  def add_reserve(self, player):
    return self.get_player(player).add_reserve()

  def remove_reserve(self, player):
    return self.get_player(player).remove_reserve()

  def get_player(self, player):
    return self.bottom_player if player else self.top_player

  def left_click(self, pos):
    player = self.get_player(pos[1] > self.tiles[0].centery)
    index = player.get_index(pos)
    if index != None:
      player.add_piece(index)


def main():
  pygame.init()
  clock = pygame.time.Clock()

  screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
  pygame.display.set_caption('Royal Game of Ur')
  pygame.mouse.set_visible(True)

  background = pygame.Surface(screen.get_size()).convert()
  background.fill(GREY)
  tile_length = min(SCREEN_WIDTH // 14, SCREEN_HEIGHT // 5)

  tiles = []
  left_offset = 1
  for j in [1, 3]:
    for i in list(range(4)) + [6, 7]:
      pygame.draw.rect(background, WHITE, [(i + left_offset)*tile_length, j*tile_length, tile_length, tile_length], TILE_WIDTH)
  for i in range(8):
    tiles.append(pygame.draw.rect(background, WHITE, [(i + left_offset)*tile_length, 2*tile_length, tile_length, tile_length], TILE_WIDTH))
  # Color safe space differently
  pygame.draw.rect(background, GREEN, [(3 + left_offset)*tile_length, 2*tile_length, tile_length, tile_length], TILE_WIDTH)

  dice_centers = [((9 + left_offset) * tile_length + (i * tile_length), 2 * tile_length + tile_length // 3) for i in range(4)]
  spot_centers = []
  for center in dice_centers:
    spot_center = draw_triangle(background, WHITE, center, 3 * tile_length // 7)
    spot_centers.append(spot_center)


  if pygame.font:
    font = pygame.font.Font(None, 100)

    rolled_color = RED
    rolled_text = font.render("You rolled a: %d" % (roll_dice(background, spot_centers),), True, rolled_color, GREY)
    rolled_text_pos = rolled_text.get_rect()
    rolled_text_pos.midtop = ((10 + left_offset) * tile_length, 3 * tile_length)
    background.blit(rolled_text, rolled_text_pos)


    button_color = WHITE
    button_text = font.render("Roll", True, button_color, GREY)
    button_text_pos = button_text.get_rect()
    button_text_pos.top = 1 * tile_length
    button_text_pos.left = rolled_text_pos.left
    background.blit(button_text, button_text_pos)
    pygame.draw.rect(background, BLACK, button_text_pos, 3)


  board = Board(background, tiles, tile_length)
  board.init_font(spot_centers, rolled_text_pos, button_text_pos)
  screen.blit(background, (0, 0))

  running = True
  while running:

    event = pygame.event.wait()
    if event.type == QUIT:
      running = False
      break

    if event.type == MOUSEBUTTONUP:
      click = event.button
      if click == 1: # left click
        if button_text_pos.collidepoint(event.pos):
          board.click_roll()
        else:
          board.left_click(event.pos)

    screen.blit(background, (0, 0))
    pygame.display.update()


  pygame.quit()

if __name__ == '__main__':
  main()
