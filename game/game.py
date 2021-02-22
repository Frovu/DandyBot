import sys
import json
from pathlib import Path
from random import shuffle
from importlib import import_module, reload

sys.path.insert(0, './bots')

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
    def __init__(self, challenge):
        self.challenge = challenge
        self.level_index = 0
        self.players = []
        self.load_level()
        # load challenge bots
        if challenge.get("bots"):
            for bot in challenge["bots"]:
                try:
                    return import_module(bot).script
                except:
                    raise Exception(f"Failed to load bot: {bot}")
                tile = challenge["tiles"][name] if "tiles" in challenge and name in challenge["tiles"] else BOT_TILE
                self.load_player(LocalPlayer(self.game, bot, tile, script))

    def load_player(self, player):
        self.players.append(player)
        self.add_player(player, *self.level["start"])
        shuffle(self.players)

    def load_level(self):
        self.level = self.challenge["levels"][self.level_index]
        name = self.level["map"]
        if type(name) is str: # map from separate file
            # TODO: handle map loading error
            fname = name if name.endswith(".json") else name + ".json"
            map = json.loads(MAPS_DIR.joinpath(fname))
            data = map["grid"]
            self.map_title = map["title"]
            self.map_tiles = map.get("tiles")
        else: # map from chal file
            data = self.challenge["maps"][name]
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

    # absolutely cursed method ikr
    def check_against_state(state):
        a_game = Game()
        self.has_player = [[None for y in range(rows)] for x in range(cols)]
        self.map = state["grid"]
        for p in state["players"]:
            self.has_player[p.x][p.y] = True
        self.level_index = state["level"]
        return a_game.check

    def play(self):
        for p in self.players:
            p.do_action()
        if self.gold >= self.level["gold"]:
            return self.next_level()
        self.steps += 1
        return not self.level.get("steps") or self.steps < self.level["steps"]

    def next_level(self):
        self.level_index += 1
        if self.level_index < len(self.challenge["levels"]):
            self.load_level()
            return "new map"
        return False

    def get_map(self):
        return {
            "grid": ["".join(row) for row in self.map],
            "title": self.map_title,
            "tiles": self.map_tiles or self.challenge.get("tiles")
        }

    def fetch(self):
        players = list(self.players)
        for p in players: del p.game
        grid = ["".join(row) for row in self.map]
        return grid, players


class Player:
    def __init__(self, game, name, tile):
        self.game = game
        self.name = name
        self.tile = tile
        self.x, self.y = 0, 0
        self.gold = 0

    def act(self, cmd):
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

class LocalPlayer(Player):
    def __init__(self, game, name, tile, script):
        super().__init__(game, name, tile)
        self.script = script

    def do_action(self):
        self.act(self.script(self.game.check, self.x, self.y))
