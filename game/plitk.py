import json
from pathlib import Path
import tkinter as tk

SCALE_DIV = 100

def get_tile_ppm(tileset, index):
    x = tileset["tile_width"] * (index % tileset["columns"])
    y = tileset["tile_height"] * (index // tileset["columns"])
    w = tileset["columns"] * tileset["tile_width"]
    data = bytes()
    for i in range(w * y + x, w * (y + tileset["tile_height"]) + x, w):
        data += tileset["data"][i * 3: i * 3 + tileset["tile_width"] * 3]
    return bytes("P6\n%d %d\n255\n" % (tileset["tile_width"],
                                       tileset["tile_height"]), "ascii") + data

class PliTk:
    def __init__(self, canvas, x, y, cols, rows, tileset, scale):
        self.canvas = canvas
        self.x, self.y = x, y
        self.tileset = tileset
        self.scale = scale
        self.images = dict()
        self.tiles = []
        self.load_tile_image(0)
        self.resize(cols, rows)

    def load_tile_image(self, index):
        img = tk.PhotoImage(data=get_tile_ppm(self.tileset, index))
        if self.scale != 1.0:
            img = img.zoom(int(self.scale * SCALE_DIV))
            img = img.subsample(SCALE_DIV)
        self.images[index] = img
        return img

    def rescale(self, new_scale):
        if new_scale != self.scale:
            self.scale = new_scale
            for i in self.images:
                self.load_tile_image(i)
            self.resize(self.cols, self.rows)

    def resize(self, cols, rows):
        self.cols, self.rows = cols, rows
        self.canvas.config(width=cols  * self.tileset["tile_width"]  * self.scale,
                           height=rows * self.tileset["tile_height"] * self.scale)
        while self.tiles:
            self.canvas.delete(self.tiles.pop())
        for j in range(rows):
            for i in range(cols):
                self.tiles.append(self.canvas.create_image(
                    self.x + i * self.tileset["tile_width"] * self.scale,
                    self.y + j * self.tileset["tile_height"] * self.scale,
                    image=self.images[0], anchor="nw"))

    def set_tile(self, x, y, index):
        img = self.images.get(index) or self.load_tile_image(index)
        self.canvas.itemconfigure(self.tiles[self.cols * y + x], image=img)
