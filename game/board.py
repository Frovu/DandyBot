
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
        scale = max(max_scale, DEFAULT_SCALE)
        self.screen = PliTk(canvas, 0, 0, 0, 0, self.tileset, scale)

    def set_max_scale(self, new_scale):
        self.max_scale = new_scale
        if self.scale > new_scale:
            self.rescale(new_scale)

    def rescale(self, scale):
        if scale != self.screen.scale:
            self.screen = PliTk(canvas, 0, 0, self.screen.cols, self.screen.rows, self.tileset, scale)
        self.canvas.config(width=self.screen.cols * self.tileset["tile_width"] * scale,
                           height=self.screen.rows * self.tileset["tile_height"] * scale)

    def load(self, map):
        scale = max(map.get("scale") or DEFAULT_SCALE, self.max_scale)
        self.rescale(scale)
        self.tiles = dict(DEFAULT_TILES)
        if map.get("tiles"): self.tiles.update(map["tiles"])
        cols, rows = len(map["grid"][0]), len(map["grid"])
        self.screen.resize(cols, rows)
        self.map_title = map.get("title") or "unknown"
        self.update(map["grid"], [])

    def update(self, grid, players):
        for y in range(len(grid)):
            for x in range(len(grid[0])):
                self.screen.set_tile(x, y, self.tiles[grid[y][x]])
        for p in players:
            self.screen.set_tile(p.x, p.y, p.tile)
        lines = []
        if self.challenge:
            lines.append("Chal: %s\nLevels total: %4d" %
                (self.challenge.get("title"), len(self.challenge["levels"])))
        lines.append("Level: %3s" % (self.map_title))
        for p in sorted(players, key=lambda x: x.gold, reverse=True):
            lines.append("%s: %3d" % (p.name, p.gold))
        self.label["text"] = "\n".join(lines)

    def set_challenge(self, chal):
        self.challenge = chal
