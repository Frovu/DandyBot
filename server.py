import sys
import json
sys.path.insert(0, './game')
from pathlib import Path
from game import Game, Player
import asyncio
BOT_TILE = 2128
PLAYER_TILE = 2138
CHUNK = 128
TICKRATE = 100
CHALLENGES = Path('./game/challenges')

class Connection:
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer

    async def communicate(self, cmd, object=None):
        message = cmd
        if not object is None:
            message += " " + json.dumps(object)
        self.writer.write(message.encode())
        await self.writer.drain()
        resp = await  self.reader.read(CHUNK)
        resp = resp.decode()
        if not object is None and resp == "ok":
            return True
        try:
            return json.loads(resp)
        except:
            await self.bad_request()
            raise Exception("Failed to communicate: "+cmd)

    async def bad_request(self):
        self.writer.write("400".encode())
        await self.writer.drain()

    def close(self):
        self.writer.close()

class RemotePlayer(Player, Connection):
    def __init__(self, game, reader, writer):
        Connection.__init__(reader, writer)
        self.username = None
        self.game = game

    async def connect(self):
        data = await self.communicate("player")
        username = data.get("name")
        bot_name = data.get("bot")
        bot_tile = data.get("tile")
        if not self.username or not bot_name or not bot_tile:
            await self.bad_request()
            raise Exception("Bad player data")
        self.username = str(username)
        Player.__init__(self.game, str(bot_name), int(bot_tile))


class ServerGame(Game):
    def __init__(self, challenge, tick_rate):
        super().__init__(challenge)
        self.tick_rate = tick_rate

    async def connect_player(self, reader, writer):
        player = RemotePlayer(self, reader, writer)
        await player.connect()
        self.load_player(player)

class Server:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.games = []

    def load_challenge(self, title):
        chal_path = CHALLENGES.joinpath(title)
        return json.loads(chal_path.read_text())

    async def start_game(self, chal_name, reader, writer):
        chal = self.load_challenge(chal_name)
        game = ServerGame(chal, TICKRATE)
        try:
            await game.connect_player(reader, writer)
            self.games.append(game)
        except:
            print("failed to connect player to solo game")


    async def handler(self, reader, writer):
        data = await reader.read(CHUNK)
        message = data.decode()
        addr = writer.get_extra_info('peername')

        print(f"Received {message} from {addr}")
        if message.startswith("get"):
            resp = self.get(message.split()[1])
        elif message.startswith("ping"):
            resp = "pong"
        elif message.startswith("start"):
            await self.start_game("original.json", reader, writer)
            # TODO chose mode
            # start single player server challenge

        else:
            resp = "400"
        print(f"Sending: {resp}")
        writer.write(resp.encode())
        await writer.drain()

    def get(self, what):
        if what == "challenge":
            return "the trial"
        else:
            return None

    async def serve(self):
        server = await asyncio.start_server(
            self.handler, self.ip, self.port)

        addr = server.sockets[0].getsockname()
        print(f'Serving on {addr}')

        async with server:
            await server.serve_forever()

server = Server('127.0.0.1', 8989)
asyncio.run(server.serve())
