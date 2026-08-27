"""
Working example: tests the /health endpoint using FastAPI's TestClient
(built on httpx). Use this as your template.

Run with: pytest
"""

import pytest

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_create_and_retrieve_game(client, sample_pgn):
    create_resp = client.post("/games", json=sample_pgn)
    game_id = create_resp.json()["id"]
    
    get_resp = client.get(f"/games/{game_id}")
    assert get_resp.json()["white"] == "Magnus Carlsen"
    assert get_resp.json()["black"] == "Hikaru Nakamura"

@pytest.mark.parametrize("bad_pgn", [
    "",
    "   ",  
    "[Event 'Test']",  
    "garbage", 
])

def test_create_game_rejects_invalid_pgn(client, bad_pgn):
    response = client.post("/games", json={"pgn": bad_pgn})
    assert response.status_code == 400

def test_list_games_empty(client):
    response = client.get("/games")
    assert response.status_code == 200
    assert response.json() == []  
    assert isinstance(response.json(), list)

def test_get_analysis_for_missing_game(client):
    response = client.get("/games/99999/analysis")
    
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()

def test_list_games_multiple(client):
    pgns = [
        {"pgn": f"[White 'Player{i}']\n[Black 'Opponent']\n[Result '1-0']\n\n1. e4 1-0"}
        for i in range(3)
    ]
    
    for pgn in pgns:
        client.post("/games", json=pgn)
    
    response = client.get("/games")
    assert response.status_code == 200
    games = response.json()
    assert len(games) == 3
    
    assert all("pgn" not in game for game in games)

def test_game_evaluation(client):
    pgn = {
        "pgn": "[White 'Player']\n[Black 'Opponent']\n[Result '1-0']\n\n1. e4 1-0"
    }
    create_resp = client.post("/games", json=pgn)
    game_id = create_resp.json()["id"]
    
    analysis_resp = client.get(f"/games/{game_id}/analysis")
    assert analysis_resp.status_code == 200
    analysis_data = analysis_resp.json()

    assert isinstance(analysis_data, list)
    assert len(analysis_data) > 0

    for position_eval in analysis_data:
        assert "fen" in position_eval
        assert "evaluation" in position_eval

        assert isinstance(position_eval["fen"], str)
        assert isinstance(position_eval["evaluation"], dict)

        eval_data = position_eval["evaluation"]
        assert "type" in eval_data
        assert "value" in eval_data
        assert eval_data["type"] in ["cp", "mate"]
        assert isinstance(eval_data["value"], int)

    first_eval = analysis_data[0]
    assert "rnbqkbnr" in first_eval["fen"]
    first_eval = analysis_data[0]
    assert first_eval["evaluation"]["type"] == "cp"
    assert first_eval["evaluation"]["value"] == 30

def test_game_evaluation_invalid_pgn(client):
    garbage_pgn = {"pgn": "garbage"}
    create_resp = client.post("/games", json=garbage_pgn)
    assert create_resp.status_code == 400
    assert "detail" in create_resp.json()
    assert "no moves found" in create_resp.json()["detail"].lower()

    empty_string_pgn = {"pgn": ""}
    create_resp = client.post("/games", json=empty_string_pgn)
    assert create_resp.status_code == 400
    assert "detail" in create_resp.json()
    assert "unable to parse" in create_resp.json()["detail"].lower()
# ---------------------------------------------------------------------
# TODO: test_create_game_with_valid_pgn
#   - POST a valid PGN string to /games
#   - assert 200/201 and that the response includes parsed white/black/result

# TODO: test_create_game_with_invalid_pgn
#   - POST garbage text to /games
#   - assert it returns 400, not a 500 crash
#   - this is the test that will catch you if you forget error handling
#     in the route -- write it BEFORE you're sure the route handles it

# TODO: test_list_games_empty
#   - GET /games on a fresh DB, assert an empty list, not an error

# TODO: test_get_analysis_for_missing_game
#   - GET /games/9999/analysis where 9999 doesn't exist
#   - assert 404

# A note on test data + Stockfish: analysis tests will be slow and
# depend on a real engine binary being present. Think about whether
# that belongs in your regular test suite or a separate "integration"
# suite you run less often -- this is exactly the testing-pyramid
# conversation from Phase 6, showing up early.
