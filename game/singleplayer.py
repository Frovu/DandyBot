
import json
from pathlib import Path
from game import Game

class Singleplayer:
    def __init__(self, board, data_dir):
        self.board = board
        game = json.loads(data_dir.joinpath("game.json").read_text())
        self.game = Game(game)
        map, players = self.game.fetch()
        self.board.load(map, game.get("tiles"))

    def play(self):
        self.game.play()
