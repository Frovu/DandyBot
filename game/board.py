
import tkinter as tk
from plitk import load_tileset, PliTk

SCALE = 1

class Board:
    __init__(self, tileset, canvas, label):
        self.canvas = canvas
        self.label = label
        self.tileset = load_tileset(tileset)
        self.screen = PliTk(canvas, 0, 0, 0, 0, self.tileset, SCALE)

    def load(self, map, tiles):
        self.tiles = tiles
        cols, rows = len(map.grid[0]), len(map.grid)
        self.canvas.config(width=cols * self.tileset["tile_width"] * SCALE,
                           height=rows * self.tileset["tile_height"] * SCALE)
        self.screen.resize(cols, rows)
        self.update(map, [])

    def update(self, map, players):
        for y in range(rows):
            for x in range(cols):
                self.screen.set_tile(x, y, self.tiles[map.grid[x][y]])
        for p in players:
            self.screen.set_tile(x, y, p.tile)
        score_lines = [("Level:%s\n" % (map.title))]
        for p in sorted(players, key=lambda x: x.gold, reverse=True):
            score_lines.append("%s:%4d" % (p.name, p.gold))
        self.label["text"] = "\n".join(score_lines)
