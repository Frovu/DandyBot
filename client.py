import sys
import json
from pathlib import Path
import tkinter as tk
import tkinter.filedialog
sys.path.insert(0, './game')
from plitk import PliTk
from board import Board
from singleplayer import Singleplayer

DATA_DIR = Path("./game/data")
CHALLENGES = Path("./game/challenges")
LAST_BOT = Path(".lastbot")
LAST_TILE = Path(".lasttile")
DEFAULT_PLAYER_TILE = 2138
MENU_WIDTH = 156
MENU_HEIGHT = 360

class Client:
    def __init__(self):
        self.game = None
        self.chal = None
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
        self.board = Board(tileset, canvas, label)

        #################### Bot label ####################
        if LAST_BOT.exists() and Path(LAST_BOT.read_text()).exists():
            self.bot = Path(LAST_BOT.read_text())
        else:
            self.bot = None
        self.bot_label = tk.Label(frame, font=("TkFixedFont",),
                         justify=tk.RIGHT, bg="gray15")
        self.bot_label.pack(side=tk.TOP, anchor="n", fill="x", pady=5)
        self.bot_label["text"] = f"Bot: {self.bot.stem if self.bot else 'undefined'}"
        self.bot_label["fg"] = "green" if self.bot else "red"

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
        tile_label = tk.Label(frame, font=("TkFixedFont",7),
                         justify=tk.RIGHT, fg="gray50", bg="black")
        tile_label.pack(side=tk.TOP)

        def switch_tile(n):
            tile_plitk.set_tile(0, 0, n)
            self.tile = n
            tile_label["text"] = f"tile: {n}"
            LAST_TILE.write_text(str(self.tile))
            # TODO: restrict choice
        switch_tile(int(LAST_TILE.read_text()) if LAST_TILE.exists() else DEFAULT_PLAYER_TILE) #FIXME: bad file contents
        btn_left.config(command=lambda: switch_tile(self.tile-1))
        btn_right.config(command=lambda: switch_tile(self.tile+1))
        #################### Menu ####################
        menu_frame = tk.Frame(frame, bg="black")
        menu_frame.pack(side=tk.TOP, fill="x")
        self.menu = Menu(self, menu_frame)
        self.menu.show("main")
        self.init_level()
        root.mainloop()

    def init_level(self):
        map = json.loads(Path("./game/maps/starter_screen.json").read_text())
        self.board.load(map)

    def change_bot(self):
        newbot = tkinter.filedialog.askopenfilename(
            initialdir=Path("bots"), filetypes=[("python files", "*.py")])
        if newbot and Path(newbot).exists():
            self.bot = Path(newbot)
            self.bot_label["text"] = f"bot: {self.bot.stem}"
            self.bot_label["fg"] = "green"
            LAST_BOT.write_text(str(self.bot))

    def choose_challenge(self, label):
        chal_file = tkinter.filedialog.askopenfilename(title="Choose challenge",
            initialdir=CHALLENGES, filetypes=[("json files", "*.json")])
        if not chal_file: return
        # TODO: check chal integrity idk
        self.chal = Path(chal_file)
        label["text"] = f"Chal: {self.chal.stem}"
        label["fg"] = "gray60"

    def play_sp(self):
        if not self.chal:
            return self.show_error("Select challenge!")
        chal = json.loads(self.chal.read_text())
        if self.game: self.game.stop()
        self.game = Singleplayer(chal, self.board, self.bot, self.tile)
        self.game.start(self.root.after)

    def start_mp(self):
        pass

    def show_error(self, text):
        label = tk.Message(self.m_frame, font=("TkFixedFont",), width=MENU_WIDTH,
                            text=text, fg="#ba0000", bg="gray10", justify=tk.RIGHT)
        label.pack(anchor="se", fill="x")
        self.root.after(1500, lambda: label.pack_forget())

class Menu:
    def __init__(self, client, frame):
        self.client = client
        self.frame = frame
        self.items = dict()
        self.packed = []
        self.add_button("change_bot", "change bot", client.change_bot)
        self.add_button("sp", "single player", lambda: self.show("sp"))
        self.add_button("mp", "multiplayer", lambda: self.show("mp"))
        self.add_button("exit", "exit", lambda: client.root.destroy())
        self.add_button("back", "back", lambda: self.show("main"))
        self.add_button("sp_select", "select chal", lambda: client.choose_challenge(self.items["sp_chal"]))
        self.add_button("sp_play", "play", lambda: client.play_sp())
        self.items["sp_chal"] = tk.Label(frame, font=("TkFixedFont",),
                            text="Challenge: None", fg="#aa0000", bg="gray10")
        self.items["not_implemented"] = tk.Label(frame, font=("TkFixedFont",11),
                            text="Not implemented", fg="red", bg="gray10")

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
            self.show_one("exit")
        elif page == "sp":
            self.show_one("sp_chal")
            self.show_one("sp_select")
            self.show_one("sp_play")
            self.show_one("back")
        elif page == "mp":
            self.show_one("not_implemented")
            self.show_one("back")

client = Client()
