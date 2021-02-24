
import json
from pathlib import Path
import tkinter as tk
from plitk import PliTk

DEFAULT_TILES = json.loads(Path("./game/data/default_tiles.json").read_text())
DEFAULT_SCALE = 1

class Board:
    def __init__(self, tileset, canvas, label, max_scale):
        self.tileset = tileset
        self.canvas = canvas
        self.label = label
        self.max_scale = max_scale
        self.challenge = None
        scale = min(max_scale, DEFAULT_SCALE)
        self.screen = PliTk(canvas, 0, 0, 0, 0, self.tileset, scale)

    def set_max_scale(self, new_scale):
        self.max_scale = new_scale
        map_scale = min(self.map_scale, new_scale)
        print(self.map_scale, new_scale, map_scale)
        if map_scale != self.screen.scale:
            self.screen.rescale(map_scale)
            self.update(self.grid, self.players)

    def load(self, map):
        self.map_scale = map.get("scale") or DEFAULT_SCALE
        scale = min(self.map_scale, self.max_scale)
        print(f"map scale = {scale}")
        self.screen.rescale(scale)
        cols, rows = len(map["grid"][0]), len(map["grid"])
        self.screen.resize(cols, rows)
        self.tiles = dict(DEFAULT_TILES)
        if map.get("tiles"): self.tiles.update(map["tiles"])
        self.map_title = map.get("title") or "unknown"
        self.update(map["grid"], [])

    def update(self, grid, players):
        self.grid, self.players = grid, players
        cols, rows = len(grid[0]), len(grid)
        tiles = [[self.tiles[grid[y][x]] for y in range(rows)] for x in range(cols)]
        for p in players:
            tiles[p["x"]][p["y"]] = p["tile"]
        for y in range(rows):
            for x in range(cols):
                self.screen.set_tile(x, y, tiles[x][y])
        lines = []
        if self.challenge:
            lines.append("Chal: %s\nLevels total: %4d" %
                (self.challenge.get("title"), len(self.challenge["levels"])))
        lines.append("Level: %3s" % (self.map_title))
        for p in sorted(players, key=lambda x: x["gold"], reverse=True):
            lines.append("%s: %3d" % (p["name"], p["gold"]))
        self.label["text"] = "\n".join(lines)

    def set_challenge(self, chal):
        self.challenge = chal
