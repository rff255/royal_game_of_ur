#!/usr/bin/python3

import operator
import random
import math

import pygame
from pygame.locals import *

if not pygame.font: print ('Warning, fonts disabled')
if not pygame.mixer: print ('Warning, sound disabled')


SCREEN_WIDTH    = 800
SCREEN_HEIGHT   = 300

BLACK           = (0, 0, 0)
GREY            = (100, 100, 100)
WHITE           = (255, 255, 255)
RED             = (255, 0, 0)
GREEN           = (0, 255, 0)
BLUE            = (0, 0, 255)

TILE_WIDTH      = 4


def draw_triangle(surface, color, center, side, thickness=5):
  x, y = center
  height = int(side / 2 * math.sqrt(3))
  vertices = [(x - side, y + height), ((x + side), y + height), (x, y - height)]
  pygame.draw.polygon(surface, color, vertices, thickness)
  spot_y_center = int(y - height + 2 * height / math.sqrt(3))
  return x, spot_y_center


def draw_dice(surface, center, radius=4):
  roll = random.randint(0, 1)
  color = WHITE if roll else BLACK
  pygame.draw.circle(surface, color, (center[0], center[1]), radius)
  return roll

def roll_dice(surface, centers, radius=4):
  total = 0
  for center in centers:
    total += draw_dice(surface, center, radius)
  return total


def add_piece(surface, center, color=RED):
  pygame.draw.circle(surface, color, center, 12)

def remove_piece(surface, center, color=GREY):
  add_piece(surface, center, color)

def highlight(surface, center, color=RED):
  pygame.draw.circle(surface, color, center, 20, 2)

def dehighlight(surface, center, color=GREY):
  highlight(surface, center, color)


class Player:
  def __init__(self, screen, side, color, tiles, tile_length):
    self.screen = screen
    self.side = side
    self.color = color
    safe_tiles = [t.move(0, tile_length if side else -tile_length) for t in tiles]
    self.tiles = safe_tiles[3::-1] + tiles + safe_tiles[:-3:-1]
    self.end = safe_tiles[4].union(safe_tiles[5])
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

    self.highlighted = []
    self.hover_highlighted = []
    self.selected = -1

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

  def highlight_reserve(self):
    for center in (self.reserve_centers[i] for i in range(self.reserve)):
      highlight(self.screen, center, self.color)
      self.highlighted.append(center)

  def add_piece(self, index):
    if self.selected == -1:
      if not self.remove_reserve():
        return False

    if not self.pieces[index]:
      if self.is_shared(index) and self.other.pieces[index]:
        self.other.add_reserve()
        self.other.remove_piece(index)
      add_piece(self.screen, self.tiles[index].center, self.color)
      self.pieces[index] = 1
      if self.selected != -1:
        self.remove_piece(self.selected)
      return True
    return False

  def remove_piece(self, index):
    if self.pieces[index]:
      remove_piece(self.screen, self.tiles[index].center)
      self.pieces[index] = 0
      return True
    return False

  def highlight(self, index, hover=False):
    if index == len(self.pieces):
      center = self.end.center
    else:
      center = self.tiles[index].center
    if hover:
      if center in self.hover_highlighted:
        return
      self.hover_highlighted.append(center)
    else:
      self.highlighted.append(center)
    highlight(self.screen, center, self.color)

  def dehighlight(self, hover=False):
    target = self.hover_highlighted if hover else self.highlighted
    for center in target:
      dehighlight(self.screen, center)
    target.clear()

  def highlight_valid_pieces(self, roll):
    if roll <= 4 and not self.pieces[roll-1]:
      self.highlight_reserve()
    for index, piece in enumerate(self.pieces):
      if piece and self.is_valid_move(index, roll):
        self.highlight(index)

  def highlight_valid_moves(self, index, roll, hover=False):
    if self.is_valid_move(index, roll):
      self.highlight(index + roll, hover)

  def is_valid_move(self, index, roll):
    if index == -1 and self.reserve == 0:
      return False
    elif index >= 0 and index < len(self.pieces) and not self.pieces[index]:
      return False
    potential_move = index + roll
    if potential_move > len(self.pieces):
      return False
    elif potential_move == len(self.pieces):
      return True
    elif not self.pieces[potential_move]:
      if self.is_shared(potential_move):
        if self.other.pieces[potential_move] and potential_move == 7:
          return False
      return True

  def reserve_click(self, pos):
    return abs(pos[1] - self.reserve_centers[0][1]) < self.tile_length / 2

  def valid_select(self, pos):
    rect = pygame.Rect(0, 0, self.tile_length, self.tile_length)
    for center in self.highlighted:
      rect.center = center
      if rect.collidepoint(pos):
        return True
    return False

  def get_index(self, pos):
    try:
      return ([tile.collidepoint(pos) for tile in self.tiles] + [self.end.collidepoint(pos)]).index(True)
    except ValueError:
      return -1

  def is_shared(self, index):
    return index >= 4 and index <= 11


class Waiting_For:
  ROLL      = 0
  SELECT    = 1


class Board:
  def __init__(self, screen, tiles, tile_length):
    self.screen = screen
    self.tiles = tiles
    self.tile_length = tile_length
    self.double_roll = [3, 7, 13]

    self.top_player = Player(screen, 0, RED, tiles, tile_length)
    self.bottom_player = Player(screen, 1, BLUE, tiles, tile_length)
    self.top_player.other = self.bottom_player
    self.bottom_player.other = self.top_player

    self.player_turn = 0

    self.status = Waiting_For.ROLL

  def init_font(self, spot_centers, rolled_text_pos, button_text_pos):
    self.font = pygame.font.Font(None, 40)
    self.spot_centers = spot_centers
    self.rolled_text_pos = rolled_text_pos
    self.button_text_pos = button_text_pos

  def click_roll(self):
    if self.status == Waiting_For.ROLL:
      rolled_color, button_color = (BLUE, WHITE) if self.player_turn else (RED, WHITE)
      self.roll = roll_dice(self.screen, self.spot_centers)
      rolled_text = self.font.render("You rolled a: %d" % (self.roll,), True, rolled_color, GREY)
      button_text = self.font.render("Roll", True, button_color, GREY)
      self.screen.blit(rolled_text, self.rolled_text_pos)
      self.screen.blit(button_text, self.button_text_pos)

      if self.roll == 0:
        self.change_player()
        return

      self.get_player(self.player_turn).highlight_valid_pieces(self.roll)

      if len(self.get_player(self.player_turn).highlighted) == 0:
        self.change_player()
        return

      self.status = Waiting_For.SELECT

  def change_player(self):
    self.player_turn = 1 - self.player_turn

  def add_reserve(self, player):
    return self.get_player(player).add_reserve()

  def remove_reserve(self, player):
    return self.get_player(player).remove_reserve()

  def get_player(self, player):
    return self.bottom_player if player else self.top_player

  def left_click(self, pos):
    click_player = pos[1] > (self.tiles[0].top if self.player_turn else self.tiles[0].bottom)
    player = self.get_player(click_player)

    if click_player == self.player_turn:
      if self.status == Waiting_For.SELECT:
        if len(player.hover_highlighted) > 0:
          selection = player.get_index(pos)
          player.dehighlight()
          player.selected = selection

          destination = selection + self.roll
          if destination == len(player.pieces):
            player.remove_piece(player.selected)
            player.finished += 1
            if player.finished == player.total:
              self.game_over()
          else:
            player.add_piece(destination)
          player.dehighlight()
          player.dehighlight(hover=True)
          self.status = Waiting_For.ROLL
          if destination not in self.double_roll:
            self.change_player()

  def hover(self, pos):
    player = self.get_player(self.player_turn)
    if self.status == Waiting_For.SELECT:
      player.dehighlight(hover=True)
      if player.valid_select(pos):
        selection = player.get_index(pos)
        player.highlight_valid_moves(selection, self.roll, hover=True)

  def game_over(self):
    color, name = (BLUE, "BLUE") if self.player_turn else (RED, "RED")
    text = self.font.render("Player %s wins!" % (name,), True, color, GREY)
    pos = text.get_rect()
    pos.center = self.screen.get_rect().center
    self.screen.blit(text, pos)


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
  for j in [1, 3]:
    for i in [0, 6]:
      pygame.draw.rect(background, GREEN, [(i + left_offset)*tile_length, j*tile_length, tile_length, tile_length], TILE_WIDTH)

  dice_centers = [((9 + left_offset) * tile_length + (i * tile_length), 2 * tile_length + tile_length // 3) for i in range(4)]
  spot_centers = []
  for center in dice_centers:
    spot_center = draw_triangle(background, WHITE, center, 3 * tile_length // 7)
    spot_centers.append(spot_center)


  if pygame.font:
    font = pygame.font.Font(None, 40)

    rolled_color = RED
    rolled_text = font.render("You rolled a: %s" % (' ',), True, rolled_color, GREY)
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

    if event.type == MOUSEMOTION:
      board.hover(pygame.mouse.get_pos())

    screen.blit(background, (0, 0))
    pygame.display.update()


  pygame.quit()

if __name__ == '__main__':
  main()