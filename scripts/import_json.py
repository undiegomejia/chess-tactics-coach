"""
Utility script to output sample PGN as JSON.

Prints a notable chess game (Gukesh vs Ding Liren, World Championship 2024)
in JSON format suitable for API testing.
"""

import json
pgn = """[Event "WCh 2024"]
[Site "Singapore SIN"]
[Date "2024.12.03"]
[Round "7.1"]
[White "Gukesh,D"]
[Black "Ding Liren"]
[Result "1/2-1/2"]
[WhiteElo "2783"]
[BlackElo "2728"]
[ECO "D78"]

1.Nf3 d5 2.g3 g6 3.d4 Bg7 4.c4 c6 5.Bg2 Nf6 6.O-O O-O 7.Re1 dxc4 8.e4 Bg4
9.Nbd2 c5 10.d5 e6 11.h3 Bxf3 12.Bxf3 exd5 13.exd5 Nbd7 14.Nxc4 b5 15.Na3 Qb6
16.Bf4 Rfe8 17.Qd2 Rad8 18.Nc2 Nf8 19.b4 c4 20.Be3 Qa6 21.Bd4 Rxe1+ 22.Rxe1 Qxa2
23.Ra1 Qb3 24.Ra3 Qb1+ 25.Kg2 Rd7 26.Ra5 Qb3 27.Ra3 Qb1 28.Ra5 Qb3 29.Rxb5 Qd3
30.Qf4 Qxc2 31.Bxf6 Qf5 32.Qxf5 gxf5 33.Bxg7 Kxg7 34.Rc5 Ng6 35.Rxc4 Ne5
36.Rd4 Nc6 37.Rf4 Ne7 38.b5 Kf6 39.Rd4 h6 40.Kf1 Ke5 41.Rh4 Nxd5 42.Rxh6 Nc3
43.Rc6 Ne4 44.Ke1 f6 45.h4 Rd3 46.Bd1 f4 47.gxf4+ Kxf4 48.Bc2 Rd5 49.Rc4 f5
50.Rb4 Kf3 51.Bd1+ Kg2 52.Rb3 Re5 53.f4 Re7 54.Re3 Rh7 55.h5 Nf6 56.Re5 Nxh5
57.Rxf5 Ng3 58.Rf8 Rb7 59.Ba4 Kf3 60.f5 Kf4 61.f6 Ne4 62.Bc2 Nd6 63.Rd8 Ke5
64.Bb3 Nf7 65.Rd5+ Kxf6 66.Kd2 Rb6 67.Bc4 Rd6 68.Kc3 Rxd5 69.Bxd5 Nd6 70.Kb4 Nxb5
71.Kxb5 a6+ 72.Kxa6  1/2-1/2"""

print(json.dumps({"pgn": pgn}, indent=2))