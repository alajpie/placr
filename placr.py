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

try:
    conf = toml.load(open(path()+"/config.toml"))
    assert conf["user"] != "CHANGE_THIS"
    assert conf["pass"] != "CHANGE_THIS"
except:
    print("Please edit config.toml!")
    sys.exit(34)

pixels = []
text = conf["text"]
bg = conf["background_color"]
col = conf["text_color"]
pos = conf["text_position"]
fill = conf["fill_background"]
font = ImageFont.truetype(path()+"/font.ttf", size=7)
size = ImageDraw.Draw(Image.new("1", (0, 0))).textsize(text, font=font)
size = (size[0]-1, size[1])
img = Image.new("1", size, 0)
draw = ImageDraw.Draw(img)
draw.text((0, 0), text, 1, font=font)
dots = list(chunks(list(img.getdata()), size[0]))

for x, row in enumerate(dots):
    for y, q in enumerate(row):
        if fill and q == 0:
            pixels.append((pos[0]+x, pos[1]+y, bg))
        elif q == 1:
            pixels.append((pos[0]+x, pos[1]+y, col))

user = conf["user"]
password = conf["pass"]
l = {"op": "login-main", "user": user, "passwd": password, "api_type": "json"}
c = {}
h = {"User-Agent": "Placr!"}
try:
    s = toml.load(open(path()+"/save.toml"))
    assert s["u"] == user
except:
    print("Getting session...", end="", flush=1)
    r = req.post("https://www.reddit.com/api/login/"+user, cookies=c, headers=h, data=l)
    if "incorrect username or password" in r.text:
        print(" incorrect username or password!")
        print("QUITTING!")
        sys.exit(42)
    rs = r.cookies.get("reddit_session")
    c["reddit_session"] = rs
    print(" done!")
    print("Getting modhash...", end="", flush=1)
    r = req.get("https://www.reddit.com/api/me.json", cookies=c, headers=h)
    mh = r.json()["data"]["modhash"]
    print(" done!")
    toml.dump({"mh": mh, "rs": rs, "u": user}, open(path()+"/save.toml", "w"))
    print("Saving session and modhash... done!")
    h["X-Modhash"] = mh
else:
    c["reddit_session"] = s["rs"]
    h["X-Modhash"] = s["mh"]
    print("Loading session and modhash... done!")
for i, pix in enumerate(pixels):
    d = {"x": pix[0], "y": pix[1], "color": pix[2]}
    while 1:
        print("Drawing pixel #{}...".format(i), end="", flush=1)
        r = req.post("https://www.reddit.com/api/place/draw.json", cookies=c, headers=h, data=d)
        if "error" in r.json():
            if r.json()["error"] == 429:
                t = r.json()["wait_seconds"]
                print(" too soon ({} seconds left)".format(round(t)))
                print("Sleeping {} seconds...".format(round(t)), end="", flush=1)
                time.sleep(t)
                print(" done, retrying!")
                continue
            else:
                print(" ERROR:", r.json(["error"]))
                print("QUITTING!")
                sys.exit(77)
        else:
            print(" done!")
            break
