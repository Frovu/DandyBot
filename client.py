import sys
import json
import traceback
from pathlib import Path
ROOT = Path(__file__).parent.resolve()
import tkinter as tk
import tkinter.filedialog
sys.path.append(str(Path(ROOT, 'game')))
from plitk import PliTk
from board import Board
from singleplayer import Singleplayer
from multiplayer import Multiplayer

DATA_DIR = Path(ROOT, "game/data")
CHALLENGES = Path(ROOT, "game/challenges")
DEFAULT_SETTINGS = Path(ROOT, "default_settings.json")
SETTINGS = Path(ROOT, "settings.json")

SETTINGS_IN_MENU = { # dict of settings_name: label_text
    "tickrate": "tick, ms",
    "max_scale": "max tile scale",
    "server_ip": "server address",
    "server_port": "server port",
    "username": "user name"
}
MP_SETTINGS = ["server_ip", "server_port", "username"]
SETTINGS_INT = ["tickrate", "server_port"]
SETTINGS_FLOAT = ["max_scale"]
MENU_WIDTH = 156
MENU_HEIGHT = 400
GREEN = "#40ff40"

class Client:
    def __init__(self):
        #################### Init settings ####################
        sets = (SETTINGS if SETTINGS.exists() else DEFAULT_SETTINGS).read_text()
        self.settings = json.loads(sets)

        self.mp  = None
        self.game = None

        #################### Init window ####################
        self.root = root = tk.Tk()
        root.configure(background="black")
        root.title("DandyBot")
        canvas = tk.Canvas(root, bg="black", highlightthickness=0)
        canvas.pack(side=tk.LEFT)
        self.m_frame = frame = tk.Frame(root, bg="black", width=MENU_WIDTH, height=MENU_HEIGHT)
        frame.pack_propagate(0)
        frame.pack(side=tk.RIGHT, anchor="n", fill="x")
        label = tk.Label(frame, font=("TkFixedFont",),
                         justify=tk.RIGHT, fg="white", bg="gray15")
        label.pack(side=tk.TOP, fill="x", anchor="n")
        tileset = json.loads(DATA_DIR.joinpath("tileset.json").read_text())
        tileset["data"] = DATA_DIR.joinpath(tileset["file"]).read_bytes()
        self.board = Board(tileset, canvas, label, self.settings["max_scale"])

        #################### Bot label ####################
        self.bot_label = tk.Label(frame, font=("TkFixedFont",),
                         justify=tk.RIGHT, bg="gray15")
        self.bot_label.pack(side=tk.TOP, anchor="n", fill="x", pady=5)
        self.bot_label["text"] = f"Bot: {self.settings.get('bot') or 'undefined'}"
        self.bot_label["fg"] = GREEN if self.settings.get('bot') else "red"

        #################### Tile selector ####################
        tile_frame = tk.Frame(frame, bg="black")
        tile_frame.pack(side=tk.TOP)
        btn_left = tk.Button(tile_frame, text="<", fg="gray1", bg="gray30", highlightthickness=0)
        btn_right = tk.Button(tile_frame, text=">", fg="gray1", bg="gray30", highlightthickness=0)
        tile_canvas = tk.Canvas(tile_frame, bg="black", highlightthickness=0)
        tile_canvas.config(width=tileset["tile_width"], height=tileset["tile_height"])
        btn_left.pack(side=tk.LEFT, padx=3, pady=3)
        tile_canvas.pack(side=tk.LEFT)
        btn_right.pack(side=tk.LEFT, padx=3, pady=3)
        tile_plitk = PliTk(tile_canvas, 0, 0, 1, 1, tileset, 1)
        tile_label = tk.Label(frame, font=("TkFixedFont",7), text="tile: "+str(self.settings["tile"]),
                         justify=tk.RIGHT, fg="gray50", bg="black")
        tile_label.pack(side=tk.TOP)

        def switch_tile(n):
            # TODO: restrict choice
            tile_plitk.set_tile(0, 0, n)
            tile_label["text"] = f"tile: {n}"
            self.settings["tile"] = n
            self.save_settings(0)
        tile_plitk.set_tile(0, 0, self.settings["tile"])
        btn_left.config(command=lambda: switch_tile(self.settings["tile"] - 1))
        btn_right.config(command=lambda: switch_tile(self.settings["tile"] + 1))
        ########################   Menu   ########################
        menu_frame = tk.Frame(frame, bg="black")
        menu_frame.pack(side=tk.TOP, fill="x")
        self.menu = Menu(self, menu_frame)
        self.menu.show("main")
        self.init_level()
        root.mainloop()

    def init_level(self):
        map = json.loads(Path(ROOT, "game/maps/starter_screen.json").read_text())
        self.board.load(map)

    def change_bot(self):
        newbot = tkinter.filedialog.askopenfilename(
            initialdir=Path(ROOT, "bots"), filetypes=[("python files", "*.py")])
        if newbot and Path(newbot).exists():
            self.settings["bot"] = Path(newbot).stem
            self.bot_label["text"] = "bot: " + self.settings["bot"]
            self.bot_label["fg"] = GREEN
            self.save_settings(0)

    def choose_challenge(self, label):
        chal_file = tkinter.filedialog.askopenfilename(title="Choose challenge",
            initialdir=CHALLENGES, filetypes=[("json files", "*.json")])
        if not chal_file: return
        chal = Path(chal_file)
        self.settings["challenge"] = chal_file
        self.save_settings(0)
        label["text"] = f"Chal: {chal.stem}"
        label["fg"] = "gray60"

    def play_sp(self):
        if not self.settings["challenge"]:
            return self.show_error("Select challenge!")
        chal_path = CHALLENGES.joinpath(self.settings["challenge"])
        if not chal_path.exists():
            return self.show_error(f"Not found chal: {chal_path.file}")
        chal = json.loads(chal_path.read_text())
        # TODO: check chal integrity idk
        if self.game: self.game.stop()
        try:
            self.game = Singleplayer(chal, self.board,
                self.settings["bot"],
                self.settings["tile"],
                self.settings["tickrate"])
            self.game.start(self.root.after)
        except Exception as e:
            traceback.print_exc()
            return self.show_error(str(e))

    def stop_sp(self):
        if self.game: self.game.stop()

    def mp_connect(self):
        self.save_settings(1, MP_SETTINGS)
        self.mp = Multiplayer(self.board,
            self.settings["server_ip"],
            self.settings["server_port"],
            self.settings["username"])
        self.menu.add_button("mp_new_room", "new room", lambda: self.mp_join(None))
        self.menu.add_button("mp_refresh", "refresh", lambda: self.mp.check_rooms())
        self.mp.check_rooms()
        def updater():
            if not self.mp: return
            while True:
                try:
                    type, message = self.mp.queue.get_nowait()
                except:
                    break
                if type == "error":
                    self.show_error(message)
                elif type == "close":
                    self.mp_disconnect()
                elif type == "success":
                    self.show_success(message)
                elif type == "switch_tab":
                    self.menu.show(message)
                elif type == "add_room":
                    btn_name = "mp_room_"+message
                    if self.menu.items.get(btn_name) is None:
                        self.menu.add_button(btn_name, message, lambda: self.mp_join(message))
                    self.menu.show("mp_server")
                else:
                    self.show_error("unhandled mp event: "+type)
            self.root.after(50, updater)
        self.root.after(0, updater)

    def mp_join(self, name):
        if not self.mp is None:
            self.mp.join_room(name, self.settings["bot"], self.settings["tile"])

    def mp_play(self):
        if not self.mp is None:
            self.mp.play()

    def mp_disconnect(self):
        if not self.mp is None:
            for i in self.menu.items:
                if i.startswith("mp_room_"):
                    del self.menu.items[i]
            self.mp.disconnect()
            self.mp = None
            self.show_success("Disconnected")
            self.menu.show("mp")

    def default_settings(self):
        self.settings = json.loads(DEFAULT_SETTINGS.read_text())

    def save_settings(self, user_input, only=None):
        if user_input:
            for setting in (only or SETTINGS_IN_MENU):
                set = self.menu.settings[setting].get()
                if setting in SETTINGS_INT: set = int(set)
                if setting in SETTINGS_FLOAT: set = float(set)
                self.settings[setting] = set
                # settings that require additional action
                if setting == "max_scale":
                    self.board.set_max_scale(self.settings[setting])
        SETTINGS.write_text(json.dumps(self.settings, indent=4))
        if not only: self.show_success("Settings saved!")

    def exit(self):
        if self.mp: self.mp.disconnect()
        self.root.destroy()

    def show_message(self, text, color):
        label = tk.Message(self.m_frame, font=("TkFixedFont",), width=MENU_WIDTH,
                            text=text, fg=color, bg="gray10", justify=tk.RIGHT)
        label.pack(anchor="se", fill="x")
        self.root.after(1500, lambda: label.pack_forget())

    def show_error(self, text):
        self.show_message(text, "#ba0000")

    def show_success(self, text):
        self.show_message(text, "#44ff44")

class Menu:
    def __init__(self, client, frame):
        self.client = client
        self.settings = dict()
        self.frame = frame
        self.items = dict()
        self.packed = []
        self.add_button("change_bot", "change bot", client.change_bot)
        self.add_button("sp", "single player", lambda: self.show("sp"))
        self.add_button("mp", "multiplayer", lambda: self.show("mp"))
        self.add_button("exit", "exit", client.exit)
        self.add_button("back", "back", lambda: self.show("main"))
        self.add_button("sp_select", "select chal", lambda: client.choose_challenge(self.items["sp_chal"]))
        self.add_button("sp_play", "play", client.play_sp)
        self.add_button("sp_stop", "stop", client.stop_sp)
        self.add_button("settings", "settings", lambda: self.show("settings"))
        self.add_button("set_default", "default", client.default_settings)
        self.add_button("set_save", "save", lambda: client.save_settings(1))
        self.add_button("mp_connect", "connect", client.mp_connect)
        self.add_button("mp_play", "start", client.mp_play)
        self.add_button("mp_disconnect", "disconnect", client.mp_disconnect)
        chal = Path(client.settings.get("challenge")).stem
        self.items["sp_chal"] = tk.Label(frame, font=("TkFixedFont",), text="Chal: "+chal
                ,fg="gray60" if chal else "#aa0000", bg="gray10")
        self.items["not_implemented"] = tk.Label(frame, font=("TkFixedFont",11),
                            text="Not implemented", fg="red", bg="gray10")

        for setting in SETTINGS_IN_MENU:
            self.items[f"s_{setting}_label"] = tk.Label(frame, font=("TkFixedFont",),
                        text=SETTINGS_IN_MENU[setting], fg="white", bg="gray10")
            self.settings[setting] = tk.StringVar()
            self.settings[setting].set(client.settings[setting])
            self.items[f"s_{setting}"] = tk.Entry(frame, textvariable=self.settings[setting])

    def clean(self):
        for widget in self.packed:
            widget.pack_forget()

    def add_button(self, name, text, handler):
        self.items[name] = tk.Button(self.frame, text=text,
                                fg="gray1", bg="gray30", highlightthickness=0)
        self.items[name].config(command=handler)

    def show_one(self, name):
        self.packed.append(self.items[name])
        self.items[name].pack(side=tk.TOP, padx=1, fill="x")

    def show(self, page):
        self.clean()
        if page == "main":
            self.show_one("change_bot")
            self.show_one("sp")
            self.show_one("mp")
            self.show_one("settings")
            self.show_one("exit")
        elif page == "sp":
            self.show_one("sp_chal")
            self.show_one("sp_select")
            self.show_one("sp_play")
            self.show_one("sp_stop")
            self.show_one("back")
        elif page == "mp":
            # self.show_one("not_implemented")
            for setting in MP_SETTINGS:
                self.show_one(f"s_{setting}_label")
                self.show_one(f"s_{setting}")
            self.show_one("mp_connect")
            self.show_one("back")
        elif page == "mp_server":
            for i in self.items:
                if i.startswith("mp_room_"):
                    self.show_one(i)
            self.show_one("mp_new_room")
            self.show_one("mp_refresh")
            self.show_one("mp_disconnect")
        elif page == "mp_room":
            self.show_one("mp_play")
            self.show_one("mp_disconnect")
        elif page == "settings":
            for setting in SETTINGS_IN_MENU:
                if setting in MP_SETTINGS: continue
                self.show_one(f"s_{setting}_label")
                self.show_one(f"s_{setting}")
            self.show_one("set_default")
            self.show_one("set_save")
            self.show_one("back")

client = Client()
