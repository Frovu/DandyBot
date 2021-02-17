import time
import sys
import json
from importlib import import_module
from pathlib import Path
from random import randrange, shuffle

sys.path.insert(0, './bots')

UP = "up"
DOWN = "down"
LEFT = "left"
RIGHT = "right"
TAKE = "take"
PASS = "pass"

LEVEL = "level"
PLAYER = "player"
GOLD = "gold"
WALL = "wall"
EMPTY = "empty"


class Game:
    def __init__(self, game):
        self.game = game
        self.load_players()
        self.level_index = 0
        self.load_level()

    def load_players(self):
        self.players = []
        for i, name in enumerate(self.game["players"]):
            script = import_module(name).script
            tile = self.game["tiles"]["@"][i]
            self.players.append(Player(name, script, self, tile))
        shuffle(self.players)

    def load_level(self):
        self.gold = 0
        self.steps = 0
        self.level = self.game["levels"][self.level_index]
        data = self.game["maps"][self.level["map"]]
        self.cols, self.rows = cols, rows = len(data[0]), len(data)
        self.map = [[data[y][x] for x in range(cols)] for y in range(rows)]
        self.has_player = [[None for y in range(rows)] for x in range(cols)]
        self.update_score()

    def get(self, x, y):
        if x < 0 or y < 0 or x >= self.cols or y >= self.rows:
            return "#"
        return self.map[y][x]

    def remove_player(self, player):
        self.has_player[player.x][player.y] = None
        self.update(player.x, player.y)

    def add_player(self, player, x, y):
        player.x, player.y = x, y
        self.has_player[x][y] = player
        self.update(x, y)

    def take_gold(self, x, y):
        self.gold += self.check(GOLD, x, y)
        self.map[y][x] = " "
        self.update(x, y)
        self.update_score()

    def check(self, cmd, *args):
        if cmd == LEVEL:
            return self.level_index + 1
        x, y = args
        item = self.get(x, y)
        if cmd == WALL:
            return item == "#"
        if cmd == GOLD:
            return int(item) if item.isdigit() else 0
        if cmd == PLAYER:
            return item != "#" and self.has_player[x][y]
        return cmd == EMPTY

    def play(self):
        for p in self.players:
            p.act(p.script(self.check, p.x, p.y))
        if self.gold >= self.level["gold"]:
            return self.next_level()
        self.steps += 1
        return self.steps < self.level["steps"]

    def next_level(self):
        self.level_index += 1
        if self.level_index < len(self.game["levels"]):
            self.load_level()
            return True
        return False

    def update(self, x, y):
        pass

    def update_score(self):
        pass

    def fetch(self):
        return self.map, self.players


class Player:
    def __init__(self, name, script, board, tile):
        self.name = name
        self.script = script
        self.board = board
        self.tile = tile
        self.x, self.y = 0, 0
        self.gold = 0

    def act(self, cmd):
        dx, dy = 0, 0
        if cmd == UP:
            dy -= 1
        elif cmd == DOWN:
            dy += 1
        elif cmd == LEFT:
            dx -= 1
        elif cmd == RIGHT:
            dx += 1
        elif cmd == TAKE:
            self.take()
        self.move(dx, dy)

    def move(self, dx, dy):
        x, y = self.x + dx, self.y + dy
        board = self.board
        board.remove_player(self)
        if not board.check(WALL, x, y) and not board.check(PLAYER, x, y):
            self.x, self.y = x, y
        board.add_player(self, self.x, self.y)

    def take(self):
        gold = self.board.check(GOLD, self.x, self.y)
        if gold:
            self.gold += gold
            self.board.take_gold(self.x, self.y)
