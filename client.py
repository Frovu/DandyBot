
class App:
    __init__(self):
        self.root = tk.Tk()

def start_single():
    def update():
        t = time.time()
        if board.play():
            dt = int((time.time() - t) * 1000)
            root.after(max(DELAY - dt, 0), update)
        else:
            label["text"] += "\n\nGAME OVER!"

    root =
    root.configure(background="black")
    canvas = tk.Canvas(root, bg="black", highlightthickness=0)
    canvas.pack(side=tk.LEFT)
    label = tk.Label(root, font=("TkFixedFont",),
                     justify=tk.RIGHT, fg="white", bg="gray20")
    label.pack(side=tk.RIGHT, anchor="n")
    filename = sys.argv[1] if len(sys.argv) == 2 else "game.json"
    game = json.loads(Path(filename).read_text())
    board = Board(game, canvas, label)
    root.after(0, update)
    root.mainloop()

def load():


load()
