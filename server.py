import sys
import json
sys.path.insert(0, './game')
from pathlib import Path
from game import Game, Player
import asyncio
BOT_TILE = 2128
PLAYER_TILE = 2138
CHUNK = 1024
TICKRATE = 100
CHALLENGES = Path('./game/challenges')

class Connection:
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer

    async def communicate(self, command, object=None):
        message = command + ("" if object is None else (" " + json.dumps(object))) + "\n"
        if not object is None:
            message += " " + json.dumps(object)
        self.writer.write(message.encode())
        await self.writer.drain()
        print("sent: "+message)
        resp = await  self.reader.read(CHUNK)
        resp = resp.decode()
        if not object is None and resp == "ok":
            return True
        try:
            return json.loads(resp)
        except:
            await self.send_status("400")
            raise Exception("Failed to communicate: "+command)

    async def send_status(self, message):
        self.writer.write(message.encode() + b'\n')
        await self.writer.drain()

    def close(self):
        self.writer.close()

class RemotePlayer(Player, Connection):
    def __init__(self, game, reader, writer):
        Connection.__init__(self, reader, writer)
        self.username = None
        self.game = game

    async def connect(self):
        data = await self.communicate("player")
        username = data.get("name")
        bot_name = data.get("bot")
        bot_tile = data.get("tile")
        if not username or not bot_name or not bot_tile:
            await self.send_status("400")
            raise Exception("Bad player data")
        self.username = str(username)
        Player.__init__(self, self.game, str(bot_name), int(bot_tile))
        await self.send_status("200")

        await self.communicate("map", self.game.get_map())

    async def start(self):
        pass


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
            await game.start()
            self.games.append(game)
        except Exception as e:
            print("failed to connect player to solo game: "+str(e))

    async def resp(self, writer, msg):
        writer.write(msg.encode() + b'\n')
        await writer.drain()

    async def listener(self, reader, writer):
        while True:
            data = await reader.read(CHUNK)
            message = data.decode()
            if not message:
                await asyncio.sleep(0.01)
                continue
            if message.startswith("get"):
                await self.resp(writer, self.get(message.split()[1]))
            elif message.startswith("ping"):
                await self.resp(writer, "pong")
            elif message.startswith("start"):
                await self.start_game("original.json", reader, writer)

    async def handler(self, reader, writer):
        addr = writer.get_extra_info('peername')
        print(f"{addr} connected")
        await self.listener(reader, writer)

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
