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

for y, row in enumerate(dots):
    for x, q in enumerate(row):
        if fill and q == 0:
            pixels.append((pos[0]+x, pos[1]+y, bg))
        elif q == 1:
            pixels.append((pos[0]+x, pos[1]+y, col))

pixels.sort(key=lambda x: x[0])

print("Total pixels:", len(pixels))
print("Calculating progress...", end="", flush=1)
for i, pix in enumerate(pixels[:]):
    d = {"x": pix[0], "y": pix[1], "color": pix[2]}
    r = req.get("https://www.reddit.com/api/place/pixel.json?x={}&y={}".format(d["x"], d["y"]), headers=h)
    try:
        if r.json()["color"] == d["color"]:
            pixels.remove(pix)
    except:
        pass
print(" done!")
print("Remaining pixels:", len(pixels))
print("Estimated time to completion:")
print("  with 5 min delay ->", len(pixels)/len(users)*5, "minutes")
print("  with 10 min delay ->", len(pixels)/len(users)*10, "minutes")
print("Note: If the program is not displaying anything, it's waiting for an account to become available")

for i, pix in enumerate(pixels):
    d = {"x": pix[0], "y": pix[1], "color": pix[2]}
    while 1:
        while 1:
            u = None
            for x in users:
                if x["next"] < time.time():
                    u = x
            if u:
                break
            else:
                time.sleep(5)
        r = req.get("https://www.reddit.com/api/place/pixel.json?x={}&y={}".format(d["x"], d["y"]), headers=h)
        try:
            if r.json()["color"] == d["color"]:
                print("Skipping pixel #{} ({}, {}) (already correct color)".format(i, d["x"], d["y"]))
                break
        except:
            pass
        print("Drawing pixel #{} ({}, {}) with {}...".format(i, d["x"], d["y"], u["name"]), end="", flush=1)
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
            print(" done! (delay: {}s)".format(round(r.json()["wait_seconds"])))
            break
