import json
from pathlib import Path
from random import shuffle

MAPS_DIR = Path("./game/maps")

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
        self.chal = game
        self.level_index = 0
        self.players = []
        self.load_level()

    def load_players(self, players):
        self.players = players
        shuffle(self.players)
        for p in self.players:
            self.add_player(p, *self.level["start"])

    def load_level(self):
        self.level = self.chal["levels"][self.level_index]
        name = self.level["map"]
        if type(name) is str: # map from separate file
            # TODO: handle map loading error
            fname = name if name.endswith(".json") else name + ".json"
            map = json.loads(MAPS_DIR.joinpath(fname))
            data = map["grid"]
            self.map_title = map["title"]
            self.map_tiles = map.get("tiles")
        else: # map from chal file
            data = self.chal["maps"][name]
            self.map_title = str(name + 1)
            self.map_tiles = None

        self.gold = 0
        self.steps = 0
        self.cols, self.rows = cols, rows = len(data[0]), len(data)
        self.map = [[data[y][x] for x in range(cols)] for y in range(rows)]
        self.has_player = [[None for y in range(rows)] for x in range(cols)]
        for p in self.players:
            self.add_player(p, *self.level["start"])

    def get(self, x, y):
        if x < 0 or y < 0 or x >= self.cols or y >= self.rows:
            return "#"
        return self.map[y][x]

    def remove_player(self, player):
        self.has_player[player.x][player.y] = None

    def add_player(self, player, x, y):
        player.x, player.y = x, y
        self.has_player[x][y] = player

    def take_gold(self, x, y):
        self.gold += self.check(GOLD, x, y)
        self.map[y][x] = " "

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
            p.act()
        if self.gold >= self.level["gold"]:
            return self.next_level()
        self.steps += 1
        return not self.level.get("steps") or self.steps < self.level["steps"]

    def next_level(self):
        self.level_index += 1
        if self.level_index < len(self.chal["levels"]):
            self.load_level()
            return True
        return False

    def get_map(self):
        return {
            "grid": self.map,
            "title": self.map_title,
            "tiles": self.map_tiles or self.chal.get("tiles")
        }

    def fetch(self):
        return self.map, self.players


class Player:
    def __init__(self, game, name, script, tile):
        self.game = game
        self.name = name
        self.script = script
        self.tile = tile
        self.next_action = PASS
        self.x, self.y = 0, 0
        self.gold = 0

    def set_action(self, action):
        self.next_action = action

    def act(self):
        cmd = self.next_action
        if cmd == PASS: return
        dx, dy = 0, 0
        if cmd == TAKE:
            self.take()
        elif cmd == UP:
            dy -= 1
        elif cmd == DOWN:
            dy += 1
        elif cmd == LEFT:
            dx -= 1
        elif cmd == RIGHT:
            dx += 1
        self.move(dx, dy)
        self.next_action = PASS

    def move(self, dx, dy):
        if dx or dy:
            x, y = self.x + dx, self.y + dy
            game = self.game
            game.remove_player(self)
            if not game.check(WALL, x, y) and not game.check(PLAYER, x, y):
                self.x, self.y = x, y
            game.add_player(self, self.x, self.y)

    def take(self):
        gold = self.game.check(GOLD, self.x, self.y)
        if gold:
            self.gold += gold
            self.game.take_gold(self.x, self.y)
