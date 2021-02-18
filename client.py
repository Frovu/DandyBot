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
LAST_BOT = Path(".lastbot")
LAST_TILE = Path(".lasttile")
DEFAULT_PLAYER_TILE = 2138

class Client:
    def __init__(self):
        self.menu = dict()
        self.game = None
        self.root = root = tk.Tk()
        root.configure(background="black")
        root.title("DandyBot")
        canvas = tk.Canvas(root, bg="black", highlightthickness=0)
        canvas.pack(side=tk.LEFT)
        self.m_frame = frame = tk.Frame(root, bg="black", width=96)
        frame.pack(side=tk.RIGHT, anchor="n")
        label = tk.Label(frame, font=("TkFixedFont",),
                         justify=tk.RIGHT, fg="white", bg="gray15")
        label.pack(side=tk.TOP, anchor="n")
        tileset = json.loads(DATA_DIR.joinpath("tileset.json").read_text())
        tileset["data"] = DATA_DIR.joinpath(tileset["file"]).read_bytes()
        self.board = Board(tileset, canvas, label)

        if LAST_BOT.exists() and Path(LAST_BOT.read_text()).exists():
            self.bot = Path(LAST_BOT.read_text())
        else:
            self.bot = None

        self.bot_label = tk.Label(frame, font=("TkFixedFont",),
                         justify=tk.RIGHT, bg="gray15")
        self.bot_label.pack(side=tk.TOP, anchor="n", fill="x", pady=5)
        self.bot_label["text"] = f"bot: {self.bot.stem if self.bot else 'undefined'}"
        self.bot_label["fg"] = "green" if self.bot else "red"

        ##### Tile selector #####
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


        self.init_level()
        self.show_menu()
        root.mainloop()

    def init_level(self):
        map = json.loads(Path("./game/maps/starter_screen.json").read_text())
        self.board.load(map)

    def add_menu_button(self, name, text, handler):
        self.menu[name] = b = tk.Button(self.m_frame, text=text,
            fg="gray1", bg="gray30", highlightthickness=0)
        b.config(command=handler)
        b.pack(side=tk.TOP, padx=1, fill="x")

    def show_menu(self):
        self.add_menu_button("change_bot", "change bot", self.change_bot)
        self.add_menu_button("sp", "single player", self.start_sp)
        self.add_menu_button("mp", "multiplayer", self.start_mp)
        self.add_menu_button("exit", "exit", lambda: self.root.destroy())

    def change_bot(self):
        newbot = tkinter.filedialog.askopenfilename(
            initialdir=Path("bots"), filetypes=[("python files", "*.py")])
        if newbot and Path(newbot).exists():
            self.bot = Path(newbot)
            self.bot_label["text"] = f"bot: {self.bot.stem}"
            self.bot_label["fg"] = "green"
            LAST_BOT.write_text(str(self.bot))

    def start_sp(self):
        if self.game: self.game.stop()
        self.game = Singleplayer(self.board, self.bot, self.tile)
        self.game.start(self.root.after)

    def start_mp(self):
        pass

client = Client()
