import requests as req
import time
import toml
import os, sys

def path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

conf = toml.load(open(path() + "/config.toml"))
users = conf["accounts"]
for user in users:
    if user["name"] == "CHANGE_THIS":
        print("Please edit config.toml!")
        sys.exit(34)

try:
    accounts = toml.load(open(path() + "/save.toml"))["accounts"]
except:
    accounts = []

header = {"User-Agent": "LaddrPlacr! (https://github.com/hawkfalcon/placr)"}
for user in users:
    loaded = False
    for account in accounts:
        if user["name"] == account["name"]:
            user["rs"] = account["rs"]
            user["mh"] = account["mh"]
            user["next"] = account["next"]
            loaded = True
    if loaded:
        continue
    print("Getting session for {}...".format(user["name"]), end="", flush=1)
    data = {"op": "login-main", "user": user["name"], "passwd": user["pass"], "api_type": "json"}
    response = req.post("https://www.reddit.com/api/login/" + user["name"], headers=header, data=data)
    if "incorrect username or password" in response.text:
        print(" incorrect username or password!")
        print("QUITTING!")
        sys.exit(42)

    user["rs"] = response.cookies.get("reddit_session")
    print(" done!")
    print("Getting modhash for {}...".format(user["name"]), end="", flush=1)
    response = req.get("https://www.reddit.com/api/me.json", cookies={"reddit_session": user["rs"]}, headers=header)
    user["mh"] = response.json()["data"]["modhash"]
    user["next"] = float(time.time())
    print(" done!")
toml.dump({"accounts":users}, open(path() + "/save.toml", "w"))

# x, y, color
pixels = []
pos = conf["position"]
length = conf["length"]

# populate vertical line
for y in range(0, length):
    pixels.append((pos[0], pos[1] + y, conf["color"]))

print("Total pixels:", len(pixels))
print("Calculating progress...", end="", flush=1)
for i, pix in enumerate(pixels[:]):
    data = {"x": pix[0], "y": pix[1], "color": pix[2]}
    response = req.get("https://www.reddit.com/api/place/pixel.json?x={}&y={}".format(data["x"], data["y"]), headers=header)
    try:
        if response.json()["color"] == data["color"]:
            pixels.remove(pix)
    except:
        if data["color"] == 0: #blank pixel, never colored
            pixels.remove(pix)
print(" done!")
print("Remaining pixels:", len(pixels))
print("Estimated time to completion:")
print("  with 5 min delay ->", len(pixels) / len(users) * 5, "minutes")
print("  with 10 min delay ->", len(pixels) / len(users) * 10, "minutes")
print("Note: If the program is not displaying anything, it's waiting for an account to become available")

for i, pix in enumerate(pixels):
    data = {"x": pix[0], "y": pix[1], "color": pix[2]}
    while 1:
        while 1:
            user = None
            for next_user in users:
                if next_user["next"] < time.time():
                    user = next_user
            if user:
                break
            else:
                time.sleep(5)
        response = req.get("https://www.reddit.com/api/place/pixel.json?x={}&y={}".format(data["x"], data["y"]), headers=header)
        try:
            if response.json()["color"] == data["color"]:
                print("Skipping pixel #{} ({}, {}) (already correct color)".format(i, data["x"], data["y"]))
                break
        except:
            pass
        print("Drawing pixel #{} ({}, {}) with {}...".format(i, data["x"], data["y"], user["name"]), end="", flush=1)
        mh_header = {"X-Modhash": user["mh"]}
        mh_header.update(header)
        response = req.post("https://www.reddit.com/api/place/draw.json", cookies={"reddit_session": user["rs"]}, headers=mh_header, data=data)
        if "error" in response.json():
            if response.json()["error"] == 429:
                user["next"] = float(time.time() + response.json()["wait_seconds"])
                toml.dump({"accounts":users}, open(path() + "/save.toml", "w"))
                print(" too soon ({} seconds left)".format(round(response.json()["wait_seconds"])))
                continue
            else:
                print(" ERROR:", response.json()["error"])
                print("QUITTING!")
                sys.exit(77)
        else:
            user["next"] = float(time.time() + response.json()["wait_seconds"])
            toml.dump({"accounts":users}, open(path() + "/save.toml", "w"))
            print(" done! (delay: {}s)".format(round(response.json()["wait_seconds"])))
            break
