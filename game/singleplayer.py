import sys
import time
import json
from pathlib import Path
from game import Game, Player
from importlib import import_module

sys.path.insert(0, './bots')
CHALLENGES = Path("./game/challenges")
BOT_TILE = 2128
SP_DELAY = 100

class Singleplayer:
    def __init__(self, board, user_bot, user_tile):
        # TODO: challenge selection
        self.board = board
        challenge = json.loads(CHALLENGES.joinpath("original.json").read_text())
        board.set_challenge(challenge)
        self.game = Game(challenge)
        players = []
        # load challenge bots
        if challenge.get("bots"):
            for bot_name in challenge["bots"]:
                script = import_module(bot_name).script # FIXME: handle import error
                tile = challenge["tiles"][name] if "tiles" in challenge and name in challenge["tiles"] else BOT_TILE
                players.append(Player(self.game, bot_name, script, tile))
        # load player bot
        script = import_module(user_bot.stem).script # FIXME: handle import error
        players.append(Player(self.game, user_bot.stem, script, user_tile))

        self.game.load_players(players)
        self.board.load(self.game.get_map())

    def start(self, updater):
        self.updater = updater
        updater(0, self.play)

    def stop(self):
        self.updater = None

    def play(self):
        t = time.time()
        for p in self.game.players:
            action = p.script(self.game.check, p.x, p.y)
            p.set_action(action)
        cont = self.game.play()
        if cont and self.updater:
            if cont == "new map":
                self.board.load(self.game.get_map())
            map, players = self.game.fetch()
            self.board.update(map, players)
            dt = int((time.time() - t) * 1000)
            self.updater(max(SP_DELAY - dt, 0), self.play)
        else:
            self.board.label["text"] += "\n\nGAME OVER!"
