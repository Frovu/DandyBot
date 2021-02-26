import sys
import time
import json
sys.path.insert(0, './game')
from pathlib import Path
from game import Game, Player
from threading import Thread
import asyncio
BOT_TILE = 2128
PLAYER_TILE = 2138
CHUNK = 1024
TICKRATE = 75
CHALLENGES = Path('./game/challenges')

def is_pending(future):
    return type(future) is asyncio.Future and not (future.done() or future.cancelled())

class Connection:
    def __init__(self, server, reader, writer):
        self.server = server
        self.reader = reader
        self.writer = writer
        self.futures = {}

    def close(self):
        self.writer.close()


    async def send(self, message):
        self.writer.write(message.encode()+b'\n')
        await self.writer.drain()

    async def communicate(self, command, object=None, await_resp=True):
        message = command + ("" if object is None else (" " + json.dumps(object)))
        await self.send(message)
        if not await_resp: return True
        existing = self.futures.get(command)
        future = asyncio.get_event_loop().create_future()
        if is_pending(existing):
            existing.cancel("overwrite")
        print("set", [command])
        self.futures[command] = future
        return await future

    async def listen(self):
        while not self.writer.is_closing():
            data = await self.reader.read(CHUNK)
            if len(data) < 1:
                await asyncio.sleep(0.01) # FIXME: probably unnecessary
                continue
            for message in data.decode().split("\n"):
                print("got: "+message)
                split = message.split(" ")
                comm_request = self.futures.get(split[0])
                if is_pending(comm_request):
                    resp = None if len(split) < 2 else message[len(split[0])+1:]
                    comm_request.set_result(resp)
                # elif message.startswith("get"):
                #     await self.resp(writer, self.get(message.split()[1]))
                elif message.startswith("ping"):
                    await self.send("pong")
                elif message.startswith("rooms"):
                    rooms = list(self.server.games.keys())
                    await self.send("rooms "+json.dumps(rooms))
                elif message.startswith("connect"):
                    game = (self.server.create_game() if len(split) < 2
                        else self.server.games.get(split[1]))
                    if game is None:
                        await self.send("404")
                    else:
                        asyncio.create_task(game.connect_player(self))
                elif message.startswith("start"):
                    if len(split) < 2:
                        await self.send("400")
                    game = self.server.games.get(split[1])
                    if game is None:
                        await self.send("404")
                    else:
                        asyncio.create_task(game.start())


class RemotePlayer(Player):
    def __init__(self, game, connection):
        self.server_game = game # idk python inheritance too hard for me
        self.conn = connection
        self.username = None

    async def connect(self):
        data = await self.conn.communicate("player", self.server_game.name)
        print(321)
        data = json.loads(data)
        username = data.get("name")
        bot_name = data.get("bot")
        bot_tile = data.get("tile")
        if not username or not bot_name or not bot_tile:
            await self.conn.send("400")
            raise Exception("Bad player data")
        self.username = str(username)
        Player.__init__(self, self.server_game, str(bot_name), int(bot_tile))
        await self.conn.send("200")
        await self.conn.communicate("map", self.game.get_map())

    async def do_action(self):
        print(self.name+" acts")
        map, players = self.game.fetch()
        state = {
            "x": self.x, "y": self.y,
            "grid": map,
            "players": players,
            "level": self.game.level_index}
        await self.conn.communicate("state", state)
        res = await self.conn.communicate("action")
        try:
            res = json.loads(res)
        except:
            res = None
        if res is None or res.get("action") is None:
            print("bad action resp: "+str(res))
            self.act("pass")
        else:
            self.act(res["action"])


class ServerGame(Game):
    def __init__(self, name, challenge, tick_rate):
        super().__init__(challenge)
        self.name = name
        self.tick_rate = tick_rate
        self.running = False
        self.remote_players = []
        self.host = None
        #asyncio.create_task(self.ping_players())

    async def ping_players(self):
        while not self.running:
            await asyncio.sleep(3)
            for p in list(self.remote_players):
                try:
                    pong = await asyncio.wait_for(p.conn.communicate("ping"), timeout=1.0)
                except asyncio.TimeoutError:
                    pong = False
                if not pong:
                    print(f"player {p.username} timed out from game {self.name}")
                    await p.conn.send("timed_out")
                    p.close()
                    self.remote_players.remove(p)
                else:
                    print(f"ping player {p.username}: ok")
            if len(self.remote_players) < 1:
                print(f"closing game {self.name}, no players")
                server.close_game(self.name)

    async def connect_player(self, connection):
        player = RemotePlayer(self, connection)
        await player.connect()
        self.remote_players.append(player)
        self.load_player(player)
        if len(self.remote_players) == 1:
            self.host = player
        return player

    def stop(self):
        self.running = False
        #asyncio.create_task(self.ping_players())

    async def start(self):
        self.running = True
        while self.running:
            t = time.time()
            status = await self.play()
            if status:
                if status == "new map":
                    for p in self.remote_players:
                        await p.conn.communicate("map", self.get_map())
                dt = int((time.time() - t) * 1000)
                print(f"tick, dt/d = {dt}/{self.tick_rate}")
                await asyncio.sleep(int(max(self.tick_rate - dt, 0))/1000)
            else:
                for p in self.remote_players:
                    await p.conn.send("game_over")
                self.stop()


class Server:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.games = {}

    def close_game(self, name):
        self.games[name].loop.stop()
        del self.games[name]

    def create_game(self):
        chal_path = CHALLENGES.joinpath("original.json")
        chal = json.loads(chal_path.read_text())
        name = str(len(self.games))
        print("new game: "+name)
        self.games[name] = ServerGame(name, chal, TICKRATE)
        return self.games[name]

    async def handler(self, reader, writer):
        print(f"{writer.get_extra_info('peername')} connected")
        conn = Connection(self, reader, writer)
        await conn.listen()

    async def serve(self):
        server = await asyncio.start_server(self.handler, self.ip, self.port)
        addr = server.sockets[0].getsockname()
        print(f'Serving on {addr}')
        async with server:
            await server.serve_forever()

server = Server('127.0.0.1', 8989)
asyncio.run(server.serve())
