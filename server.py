import sys
import json
sys.path.insert(0, './game')
from game import Game, Player
import asyncio
BOT_TILE = 2128
CHUNK = 128

class RemotePlayer(Player):
    def __init__(self, game, player_name, bot_name, tile, reader, writer):
        super().__init__(game, bot_name, tile)
        self.username = player_name
        self.reader = reader
        self.writer = writer

    def disconnect(self):
        self.writer.close()

class ServerGame(Game):
    def __init__(self, challenge, tick_rate):
        super().__init__(challenge)
        self.tick_rate = tick_rate

    async def connect_player(self, reader, writer):
        writer.write("player".encode())
        player_data = await reader.read(CHUNK)
        try:
            data = json.loads(player_data)
        except:
            writer.write("400".encode())
            return await writer.drain()



class Server:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port


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
