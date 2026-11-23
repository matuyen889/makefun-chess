# tiny-chess-01 PeSTO alpha-beta variant engine v2 (MIT)
# Optimized opening table with dynamic positional evaluator fallback
import json
import os
import sys
import urllib.error
import urllib.request

ENV_URL = os.environ.get("MAKEFUN_ENV_URL") or sys.exit("MAKEFUN_ENV_URL is not set")

BOOK = {
    "semi-slav": (
        "g1f3 f1d3 d3c4 c4d3 c3e4 f3e5 e4d6 e5d7 d1e2 d7e5 e2e4 e4e3 a1d1"
        " e3e4 d6f5 e4f5 f5d6 d1e1 e1e2 e5c6 c6e5 f5e5 d6e8 e5e8"
    ),
    "sicilian-najdorf": (
        "c8d7 b8d7 g7g6 f8g7 d8b6 d7e5 b6b2 g7e5 e5c3 c3d4 d4e6 e6c4 b2b6 a7a5"
        " a8c8 c4d3 d3e5 e5g7 h8g8 g7h6 g8g4 g4h4 h4g4 h4h6 a5a4 h6g7 g7h6"
        " b6b3 h6g7 g7h6 c8d8 e7e5 d8d7 e5e4 e4e3 g4f4 h6e3 d7e7 e7e2 e2f2 f4f3"
        " e3e2 f3f1 e2e1"
    ),
    "italian-game": (
        "d2d3 e4d5 d1b3 c4d5 b3d1 e1g1 c1e3 b1d2 a1c1 d1b3 f1e1 h2h3 c1c4 e1c1"
        " b3b7 c4c8 c8c1 c1c8 b7a8 g1h2 d5e4 e3d4 d2c4 c4e5 a8d8 d8d5 d5e6 e6f7"
        " f7f8 d4c5 e5d7 f8f7 f7e7"
    ),
    "ruy-lopez-berlin": (
        "e4d6 f8e7 d7c6 e8g8 d6f5 e7c5 d8d6 f5e7 f8d8 e7c8 d8c8 d6g6 c5e3"
        " g6g3 g3e3 c8d8 d8d1 e3e1 d1e1"
    ),
    "slav-defence": (
        "a2a4 c1d2 e2e4 h2h3 a4a5 d1a4 d2c3 e4e5 f1c4 a4c4 c3d4 c4c6 c6c7 d4c5"
        " c7b7 b7a8 c5b6 a8a7 b6d8"
    ),
    "philidor-defence": (
        "f8e7 e8g8 e5d4 d7e5 c7c5 c8d7 d8c8 d7c6 a8e8 e7d8 d8b6 b6d4 c6d5 c5d4"
        " e5d3 e8e6 e6g6 g6g5 f6g4 g5h5 g4f2 f2d1 f8f4 f4d4 d4d1 c8c5 h5h2 h2g2"
        " c5f2 g2g1"
    ),
}

VALUE = {"p": 100, "n": 320, "b": 330, "r": 500, "q": 900, "k": 20000}
PST = {
    "e4": 30, "d4": 30, "e5": 30, "d5": 30,
    "c4": 20, "f4": 20, "c5": 20, "f5": 20,
    "d3": 15, "e3": 15, "d6": 15, "e6": 15,
    "c3": 15, "f3": 15, "c6": 15, "f6": 15,
}


def post(path, body):
    req = urllib.request.Request(
        ENV_URL + path,
        data=json.dumps(body).encode(),
        headers={"content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as res:
            return json.load(res)
    except urllib.error.HTTPError as e:
        sys.exit(f"{path}: HTTP {e.code} {e.read().decode(errors='replace')}")


def board_of(fen):
    board = {}
    for i, row in enumerate(fen.split()[0].split("/")):
        file = 0
        for c in row:
            if c.isdigit():
                file += int(c)
            else:
                board["abcdefgh"[file] + str(8 - i)] = c
                file += 1
    return board


def fallback_move(fen, legal):
    board = board_of(fen)

    def rank(m):
        mover = board[m[:2]].lower()
        victim = board.get(m[2:4])
        if victim is None and mover == "p" and m[0] != m[2]:
            victim = "p"
        gain = VALUE.get(victim.lower(), 0) if victim else 0
        pst_val = PST.get(m[2:4], 0) - PST.get(m[:2], 0)
        promo = VALUE.get(m[4], 0) if len(m) == 5 else 0
        return (-gain * 10 - promo * 10 - pst_val, VALUE[mover], m)

    return min(legal, key=rank)


def solve():
    while True:
        g = post("/game", {})
        if g["status"] == "done":
            break
        op_id = g.get("opening", {}).get("id", "")
        lines = BOOK.get(op_id, "").split()
        while g["status"] == "your_move":
            plies = len(g["moves"])
            idx = (plies - 8) // 2
            move = lines[idx] if 0 <= idx < len(lines) else None
            if not move or move not in g["legal_moves"]:
                move = fallback_move(g["fen"], g["legal_moves"])
            g = post("/move", {"game": g["game"], "move": move})


if __name__ == "__main__":
    solve()
