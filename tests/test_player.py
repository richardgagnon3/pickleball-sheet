import pytest
from player import Player


class TestPlayer:
    def test_create_a_player(self):
        player = Player("Name_1")
        print(player)
        assert player._id is 1
        assert "Name_1" in str(player)

    def test_create_player_forcing_id(self):
        player = Player("Richard", id=100)
        print(player)
        assert player._id is 100
        assert "Richard" in str(player)
