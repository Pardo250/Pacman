import json
import os

_FILE = "highscore.json"


def load():
    try:
        with open(_FILE) as f:
            return int(json.load(f).get("high", 0))
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return 0


def save(score):
    try:
        with open(_FILE, "w") as f:
            json.dump({"high": score}, f)
    except OSError:
        pass
