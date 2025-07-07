import pytest
from circle_sketch.storage.storage_sqlite import Storage

@pytest.fixture(autouse=True)
def setup_and_teardown():
    Storage.reset()
    yield
    Storage.reset()

def test_player_circle_add_and_remove():
    Storage.set_player_circle([1, 2, 3])
    circle = Storage.get_player_circle()
    assert circle == [1, 2, 3]
    Storage.set_player_circle([2, 3])
    circle = Storage.get_player_circle()
    assert circle == [2, 3]

def test_game_state_set_and_get():
    state = {"theme": "Test", "date": "2025-07-07", "submissions": {}}
    Storage.set_game_state(state)
    loaded = Storage.get_game_state()
    assert loaded["theme"] == "Test"
    assert loaded["date"] == "2025-07-07"
    assert loaded["submissions"] == {}
    Storage.set_game_state(None)
    assert Storage.get_game_state() is None
