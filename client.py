import sys
import json
from pathlib import Path
import tkinter as tk
sys.path.insert(0, './game')
from board import Board

DATA_DIR = Path("./game/data")

class Client:
    def __init__(self):
        self.root = root = tk.Tk()
        root.configure(background="black")
        canvas = tk.Canvas(root, bg="black", highlightthickness=0)
        canvas.pack(side=tk.LEFT)
        self.m_frame = frame = tk.Frame(root)
        frame.pack(side=tk.LEFT, anchor="n")
        label = tk.Label(frame, font=("TkFixedFont",),
                         justify=tk.RIGHT, fg="white", bg="gray20")
        label.pack(side=tk.TOP, anchor="n")
        filename = sys.argv[1] if len(sys.argv) == 2 else "./game/data/game.json"
        self.game = json.loads(Path(filename).read_text())
        tileset = json.loads(DATA_DIR.joinpath("tileset.json").read_text())
        tileset["data"] = DATA_DIR.joinpath(tileset["file"]).read_bytes()
        self.board = Board(tileset, canvas, label)
        #root.after(0, update)

        self.init_level()
        self.show_menu()
        root.mainloop()

    def init_level(self):
        self.board.load(self.game.get("maps")[0], self.game.get("tiles"))

    def show_menu(self):
        b_sp = tk.Button(self.m_frame, text="single player")
        b_mp = tk.Button(self.m_frame, text="multiplayer")
        b_exit = tk.Button(self.m_frame, text="exit")
        b_sp.config(command=self.start_sp)
        b_mp.config(command=self.start_mp)
        b_exit.config(command=lambda: self.root.destroy())
        b_sp.pack(side=tk.TOP)
        b_mp.pack(side=tk.TOP)
        b_exit.pack(side=tk.TOP)

    def start_sp(self):
        pass

    def start_mp(self):
        pass


def start_single():
    def update():
        t = time.time()
        if board.play():
            dt = int((time.time() - t) * 1000)
            root.after(max(DELAY - dt, 0), update)
        else:
            label["text"] += "\n\nGAME OVER!"


client = Client()
