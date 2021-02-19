import sys
import json
sys.path.insert(0, './game')
from game import Game
import asyncio

class ServerGame(Game):
    def __init__(self):
        pass

class Server:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

    async def serve(self):
        server = await asyncio.start_server(
            self.handler, self.ip, self.port)

        addr = server.sockets[0].getsockname()
        print(f'Serving on {addr}')

        async with server:
            await server.serve_forever()

    async def handler(self, reader, writer):
        data = await reader.read(100)
        message = data.decode()
        addr = writer.get_extra_info('peername')

        print(f"Received {message} from {addr}")
        if message.startswith("get"):
            resp = self.get(message.split()[1])
        elif message.startswith("ping"):
            resp = "pong"
        else:
            resp = "400"
        print(f"Sending: {resp}")
        writer.write(resp.encode())
        await writer.drain()

        writer.close()

    def get(self, what):
        if what == "challenge":
            return "the trial"
        else:
            return None

server = Server('127.0.0.1', 8888)
asyncio.run(server.serve())
