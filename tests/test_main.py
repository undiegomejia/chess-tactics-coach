"""
Test suite for main FastAPI application.

Tests all API endpoints using FastAPI TestClient with in-memory SQLite database.
Uses mock Stockfish engine to avoid dependency on external binary during tests.
"""

import pytest

def test_health_check(client):
    """Test health check endpoint returns expected status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_create_and_retrieve_game(client, sample_pgn):
    """Test game creation and retrieval flow."""
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
    """Test that invalid PGN formats are rejected with 400 status."""
    response = client.post("/games", json={"pgn": bad_pgn})
    assert response.status_code == 400

def test_list_games_empty(client):
    """Test listing games when database is empty."""
    response = client.get("/games")
    assert response.status_code == 200
    assert response.json() == []  
    assert isinstance(response.json(), list)

def test_get_analysis_for_missing_game(client):
    """Test that requesting analysis for non-existent game returns 404."""
    response = client.get("/games/99999/analysis")
    
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()

def test_list_games_multiple(client):
    """Test listing multiple games and verify PGN is excluded from summary."""
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
    """Test game analysis endpoint with mock Stockfish engine."""
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
        assert "type" in position_eval
        assert "value" in position_eval

        assert isinstance(position_eval["fen"], str)
        assert isinstance(position_eval["type"], str)
        assert isinstance(position_eval["value"], int)


    first_eval = analysis_data[0]
    assert "rnbqkbnr" in first_eval["fen"]
    first_eval = analysis_data[0]
    assert first_eval["type"] == "cp"
    assert first_eval["value"] == 20

def test_game_evaluation_invalid_pgn(client):
    """Test that invalid PGN is rejected during game creation."""
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

