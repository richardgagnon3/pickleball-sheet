import pytest
from sheet_reader import SheetReader

def print_court(name, games):
    print(f"/------------------------\\")
    print(f"|    Court: {name:12s} |")
    grid = ['+--------+',
            '| Game   |',
            '|--------|',
            '| Team 1 |',
            '|        |',
            '| Team 2 |',
            '|--------|',
            ]
    for game in games.keys():
        grid[0] += f"-------|"
        grid[1] += f" {game:^5s} |"
        grid[2] += f"-------|"
        player = [games[game]['Team1'][0], games[game]['Team1'][1]]
        grid[3] += f" {player[0]:>2s},{player[1]:<2s} |"
        grid[4] += f"   vs  |"
        player = [games[game]['Team2'][0], games[game]['Team2'][1]]
        grid[5] += f" {player[0]:>2s},{player[1]:<2s} |"
        grid[6] += f"-------+"

    for line in grid:
        print(line)

def print_bench(name, games):
    print(f"/----------------\\")
    print(f"|   {name:12s} |")
    grid = ['+--------+',
            '| Game   |',
            '|--------+',
            ]
    game_list = list(games.keys())
    nb_benched_players = len(games[game_list[0]])
    for i in range(nb_benched_players):
        grid.append('|        |')
    grid.append('+--------+')
    for game in game_list:
        grid[0] += f"-------+"
        grid[1] += f" {game:^5s} |"
        grid[2] += f"-------+"
        for i in range(nb_benched_players):
            player = games[game][i]
            grid[3+i] += f" {player:^5s} |"
        grid[3+nb_benched_players] += f"-------+"

    for line in grid:
        print(line)

def print_sheet(sheet):
    court_list = list(sheet.keys())
    for court in court_list:
        if court is not "Bench":
            print_court(court, sheet[court])
        else:
            print_bench(court, sheet[court])


class TestSheetReader:

    def test_file_does_not_exist(self):
        reader = SheetReader("bad_filename.csv")
        with pytest.raises(FileNotFoundError):
            reader.read()

    def test_read_csv_file(self):
        reader = SheetReader('/'.join(["pickleball-sheet/src" , "11j-2t.csv"]))
        game_table = reader.read()
        #print(str(game_table))
        print_sheet(game_table)
        #assert False, f"No check developped!"

        