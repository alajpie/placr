import requests as req
import time
import toml
import os, sys
from PIL import Image, ImageFont, ImageDraw

def path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]

def get_board():
    r = req.get("https://www.reddit.com/api/place/board-bitmap")
    board = [[None for a in range(1000)] for b in range(1000)]
    f = 4
    for y in range(1000):
        for x in range(500):
            board[x*2][y] = r.content[f] >> 4
            board[x*2+1][y] = r.content[f] & 0b1111
            f+=1
    return board

conf = toml.load(open(path()+"/config.toml"))
users = conf["accounts"]
for u in users:
    if u["name"] == "CHANGE_THIS":
        print("Please edit config.toml!")
        sys.exit(34)

try:
    save = toml.load(open(path()+"/save.toml"))["accounts"]
except:
    save = []

h = {"User-Agent": "Placr! (https://github.com/k2l8m11n2/placr)"}
for u in users:
    loaded = False
    for s in save:
        if u["name"] == s["name"]:
            u["rs"] = s["rs"]
            u["mh"] = s["mh"]
            u["next"] = s["next"]
            loaded = True
    if loaded:
        continue
    print("Getting session for {}...".format(u["name"]), end="", flush=1)
    l = {"op": "login-main", "user": u["name"], "passwd": u["pass"], "api_type": "json"}
    r = req.post("https://www.reddit.com/api/login/"+u["name"], headers=h, data=l)
    if "incorrect username or password" in r.text:
        print(" incorrect username or password!")
        print("QUITTING!")
        sys.exit(42)
    u["rs"] = r.cookies.get("reddit_session")
    print(" done!")
    print("Getting modhash for {}...".format(u["name"]), end="", flush=1)
    r = req.get("https://www.reddit.com/api/me.json", cookies={"reddit_session": u["rs"]}, headers=h)
    u["mh"] = r.json()["data"]["modhash"]
    u["next"] = float(time.time())
    print(" done!")
toml.dump({"accounts":users}, open(path()+"/save.toml", "w"))

pixels = []
text = conf["text"]
pos = conf["text_position"]
pad = conf["padding"]
font = ImageFont.truetype(path()+"/font.ttf", size=7)
size = ImageDraw.Draw(Image.new("1", (0, 0))).textsize(text, font=font)
size = (size[0]-1+pad*2, size[1]+pad*2)
img = Image.new("1", size, 0)
draw = ImageDraw.Draw(img)
draw.text((pad, pad), text, 1, font=font)
dots = list(chunks(list(img.getdata()), size[0]))

for y, row in enumerate(dots):
    for x, q in enumerate(row):
        if conf["fill_background"] and q == 0:
            pixels.append((pos[0]+x, pos[1]+y, conf["background_color"], True))
        elif q == 1:
            pixels.append((pos[0]+x, pos[1]+y, conf["text_color"], False))

pixels.sort(key=lambda x: x[0])
if conf["background_later"]:
    pixels.sort(key=lambda x: x[3])

print("Total pixels:", len(pixels))
print("Calculating progress...", end="", flush=1)
progpix = pixels[:]
board = get_board()
for i, pix in enumerate(progpix[:]):
    if board[pix[0]][pix[1]] == pix[2]:
        progpix.remove(pix)
print(" done!")
print("Remaining pixels:", len(progpix))
print("Estimated time to completion:")
print("  with 5 min cooldown ->", len(progpix)/len(users)*5, "minutes")
print("  with 10 min cooldown ->", len(progpix)/len(users)*10, "minutes")
print("Note: If the program is not displaying anything, it's waiting for an account to become available")

i = -1
while i < len(pixels):
    i += 1
    pix = pixels[i]
    d = {"x": pix[0], "y": pix[1], "color": pix[2]}
    while 1:
        while 1:
            u = None
            for x in users:
                if x["next"] < time.time():
                    u = x
            if u:
                board = get_board()
                break
            else:
                time.sleep(5)
        if board[d["x"]][d["y"]] == d["color"]:
            break
        print(time.strftime("[%H:%M:%S] ")+"Drawing pixel #{} ({}, {}) with {}...".format(i, d["x"], d["y"], u["name"]), end="", flush=1)
        nh = {"X-Modhash": u["mh"]}
        nh.update(h)
        r = req.post("https://www.reddit.com/api/place/draw.json", cookies={"reddit_session": u["rs"]}, headers=nh, data=d)
        if "error" in r.json():
            if r.json()["error"] == 429:
                u["next"] = float(time.time()+r.json()["wait_seconds"])
                toml.dump({"accounts":users}, open(path()+"/save.toml", "w"))
                print(" too soon ({} seconds left)".format(round(r.json()["wait_seconds"])))
                continue
            else:
                print(" ERROR:", r.json()["error"])
                print("QUITTING!")
                sys.exit(77)
        else:
            u["next"] = float(time.time()+r.json()["wait_seconds"])
            toml.dump({"accounts":users}, open(path()+"/save.toml", "w"))
            print(" done! (cooldown: {}s)".format(round(r.json()["wait_seconds"])))
            i = -1
            break
