import random

def script(check, x, y):
    def detectGold(x, y):
        for i in range(100):
            for ay in range(y-i, y+i+1):
                if check("gold", x-i, ay): return x-i, ay
            for ay in range(y-i, y+i+1):
                if check("gold", x+i, ay): return x+i, ay
            for ax in range(x-i, x+i+1):
                if check("gold", ax, y+i): return ax, y+i
            for ax in range(x-i, x+i+1):
                if check("gold", ax, y-i): return ax, y-i
        return -1, -1
    #if check("level") == 1:
    gx, gy = detectGold(x, y)
    print((x,y), detectGold(x, y))
    if gx < 0: return "pass"
    if gx == x and gy == y: return "take"
    if gx > x: return "right"
    if gx < x: return "left"
    if gy > y: return "down"
    if gy < y: return "up"
