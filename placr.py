import requests as req
import time
import json
import os, sys

# (x, y, color)
pixels = [(123, 321, 15), (123, 321, 15)]

def path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

try:
    conf = json.load(open(path()+"/config.json"))
    assert conf["user"] != "CHANGE_THIS"
    assert conf["pass"] != "CHANGE_THIS"
except:
    print("Please edit config.json!")
    sys.exit(34)

user = conf["user"]
password = conf["pass"]
l = {"op": "login-main", "user": user, "passwd": password, "api_type": "json"}
c = {}
h = {"User-Agent": "Placr!"}
try:
    s = json.load(open(path()+"/save.json"))
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
    json.dump({"mh": mh, "rs": rs, "u": user}, open(path()+"/save.json", "w"))
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
