
import json
from pathlib import Path
import tkinter as tk
from plitk import PliTk

DEFAULT_TILES = json.loads(Path("./game/data/default_tiles.json").read_text())
SCALE = 1

class Board:
    def __init__(self, tileset, canvas, label):
        self.canvas = canvas
        self.label = label
        self.tileset = tileset
        self.screen = PliTk(canvas, 0, 0, 0, 0, self.tileset, SCALE)

    def load(self, map):
        self.tiles = dict(DEFAULT_TILES)
        if "tiles" in map: self.tiles.update(map["tiles"])
        cols, rows = len(map["grid"][0]), len(map["grid"])
        self.canvas.config(width=cols * self.tileset["tile_width"] * SCALE,
                           height=rows * self.tileset["tile_height"] * SCALE)
        self.screen.resize(cols, rows)
        self.map_title = map.get("title") or "unknown"
        self.update(map["grid"], [])

    def update(self, grid, players):
        for y in range(len(grid)):
            for x in range(len(grid[0])):
                self.screen.set_tile(x, y, self.tiles[grid[y][x]])
        for p in players:
            self.screen.set_tile(p.x, p.y, p.tile)
        score_lines = [("Level:%s\n" % (self.map_title))]
        for p in sorted(players, key=lambda x: x.gold, reverse=True):
            score_lines.append("%s:%4d" % (p.name, p.gold))
        self.label["text"] = "\n".join(score_lines)
