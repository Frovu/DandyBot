
import json
from pathlib import Path
from game import Game, Player
from importlib import import_module

CHALLENGES = Path("./game/challenges")

class Singleplayer:
    def __init__(self, board, user_bot, user_tile):
        # TODO: challenge selection
        self.board = board
        challenge = json.loads(CHALLENGES.joinpath("original.json").read_text())
        # FIXME: handle import error
        player = {
            "name": user_bot.stem,
            "tile": user_tile,
            "script": import_module(user_bot.stem).script
        }
        self.game = Game(challenge, player)
        self.board.load(self.game.get_map())

    def play(self):
        cont = self.game.play()
        if cont:
            map, players = self.game.fetch()
            self.board.update(map, players)
        return cont
