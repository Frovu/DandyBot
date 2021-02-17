
import tkinter as tk
from plitk import PliTk

SCALE = 1

class Board:
    def __init__(self, tileset, canvas, label):
        self.canvas = canvas
        self.label = label
        self.tileset = tileset
        self.screen = PliTk(canvas, 0, 0, 0, 0, self.tileset, SCALE)

    def load(self, map, tiles):
        self.tiles = tiles
        cols, rows = len(map[0]), len(map) # TODO: .get("grid")
        self.canvas.config(width=cols * self.tileset["tile_width"] * SCALE,
                           height=rows * self.tileset["tile_height"] * SCALE)
        self.screen.resize(cols, rows)
        self.update(map, [])

    def update(self, map, players):
        for y in range(len(map)):
            for x in range(len(map[0])):
                self.screen.set_tile(x, y, self.tiles[map[y][x]]) # TODO: .get("grid")
        for p in players:
            self.screen.set_tile(p.x, p.y, p.tile)
        score_lines = [("Level:%s\n" % ("asdsadsadads"))] # TODO: map.get("title")
        for p in sorted(players, key=lambda x: x.gold, reverse=True):
            score_lines.append("%s:%4d" % (p.name, p.gold))
        self.label["text"] = "\n".join(score_lines)
