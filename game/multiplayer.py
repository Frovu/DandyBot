import sys
import asyncio
from queue import Queue
from threading import Thread
from game import Game, Player
from importlib import import_module, reload

sys.path.insert(0, './bots')

class Multiplayer:
    def __init__(self, board, server, port):
        self.queue = Queue()
        self.board = board
        self.server = server
        self.port = port
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self.connect())
        self.thread = Thread(target=self.loop.run_forever)
        self.thread.start()

    async def connect(self):
        try:
            self.reader, self.writer = await asyncio.open_connection(self.server, self.port)
        except:
            return self.handle_error("Can't connect to server!")
        self.writer.write("ping".encode())
        data = await self.reader.read(100)
        print(f'Received: {data.decode()!r}')
        if data.decode() == "pong":
            self.queue.put(("success", "Connected!"))
            self.queue.put(("switch_tab", "mp_server"))
        else:
            self.handle_error("Failed server handshake")

    def handle_error(self, message):
        self.queue.put(("error", message))

    def start_game(self, player_bot, player_tile):
        try:
            if player_bot in sys.modules:
                 reload(sys.modules[player_bot])
            self.script = import_module(player_bot).script
        except:
            raise Exception(f"Failed to load bot: {bot}")

    def disconnect(self):
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()
        self.loop.close()
