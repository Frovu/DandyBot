import sys
import time
from game import Game, Player
from importlib import import_module, reload

sys.path.insert(0, './bots')
BOT_TILE = 2128

class Singleplayer:
    def __init__(self, challenge, board, user_bot, user_tile, tick_rate):
        self.tick_rate = tick_rate
        self.board = board
        board.set_challenge(challenge)
        self.game = Game(challenge)
        players = []
        def load_bot(bot):
            try:
                return import_module(bot).script
            except:
                raise Exception(f"Failed to load bot: {bot}")
        # load challenge bots
        if challenge.get("bots"):
            for bot_name in challenge["bots"]:
                script = load_bot(bot_name)
                tile = challenge["tiles"][name] if "tiles" in challenge and name in challenge["tiles"] else BOT_TILE
                players.append(Player(self.game, bot_name, script, tile))
        # load player bot
        if user_bot in sys.modules:
             reload(sys.modules[user_bot])
        script = load_bot(user_bot)
        players.append(Player(self.game, user_bot, script, user_tile))

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
            print(f"tick, dt/d = {dt}/{self.tick_rate}")
            self.updater(max(self.tick_rate - dt, 0), self.play)
        else:
            self.board.label["text"] += "\n\nGAME OVER!"
