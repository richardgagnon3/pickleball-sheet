"""Random games sheet generator / optimizer.

Generates many random (but always valid) games sheets for a given number of
players, courts and games, scores each one with ``sheet_score.score_sheet``
and keeps the best ones.

Each candidate sheet is built game by game:

* **Pauses**: the players who paused the least so far are benched first;
  among them, those who played the longest since their last pause are
  preferred, with some random jitter so every candidate is different.
  Players who already sat on the bench together are avoided, even if it
  delays a pause by about one game (accepted by sheet_score.PAUSE_TOLERANCE).
* **Teams**: several random ways of splitting the remaining players into
  courts/teams are tried, and the one creating the fewest repeated
  partners (then opponents) so far is kept.

This is "best of N random tries", not an exhaustive search: more tries give
better sheets, but there is no guarantee of finding the best possible sheet.
"""

import argparse
import itertools
import logging
import os
import random
import time
from collections import Counter

from game_data_io import games_to_csv_rows, write_csv_rows
from games_table import GamesTable
from sheet_score import RANKING_HEADER, score_sheet, SheetScore

_logger = logging.getLogger("__main__")

PLAYERS_PER_COURT = 4
# Random jitter applied to the pause choice. Each candidate uses one of these:
# 0 gives a strict rotation (good pauses), larger values explore more.
JITTERS = (0.0, 0.5, 1.0, 2.0)


def _pair(a: str, b: str) -> tuple:
    return (a, b) if a <= b else (b, a)


# Cost (in games of pause delay) of each previous bench sit-out with an already
# chosen player. Each candidate uses one of these: below 1 it only breaks ties
# in the pause rotation, above 1 it may delay a pause by a game to vary the bench.
BENCH_MATE_COSTS = (0.4, 1.0, 1.5)


def _choose_bench(players, nb_bench, rests, last_rest, game_idx, rng, jitter, bench_mates,
                  bench_mate_cost):
    """Pick the players to bench for game ``game_idx``, one at a time."""
    noise = {p: rng.uniform(0, jitter) for p in players}
    bench = []
    for _ in range(nb_bench):
        def priority(p):
            since_last = game_idx - last_rest[p]  # large = played for a long time
            repeats = sum(bench_mates[_pair(p, q)] for q in bench)
            return (rests[p], -since_last + noise[p] + bench_mate_cost * repeats)
        bench.append(min((p for p in players if p not in bench), key=priority))
    return bench


def _choose_courts(on_court, nb_courts, partners, opponents, rng, team_tries):
    """Split ``on_court`` players into courts/teams, avoiding repeats."""
    best, best_cost = None, None
    for _ in range(team_tries):
        p = on_court[:]
        rng.shuffle(p)
        courts = [(p[i:i + 2], p[i + 2:i + 4]) for i in range(0, nb_courts * 4, 4)]
        cost = 0
        for t1, t2 in courts:
            cost += 10 * (partners[_pair(*t1)] + partners[_pair(*t2)])
            cost += sum(opponents[_pair(a, b)] for a, b in itertools.product(t1, t2))
        if best_cost is None or cost < best_cost:
            best, best_cost = courts, cost
            if cost == 0:
                break
    return best


def generate_sheet(nb_players: int, nb_courts: int, nb_games: int,
                   rng: random.Random, jitter: float = 2.0, team_tries: int = 20,
                   bench_mate_cost: float = 1.0) -> list:
    """Generate one random valid sheet, as games_data (same format as SheetReader.read())."""
    if nb_players < nb_courts * PLAYERS_PER_COURT:
        raise ValueError(f"{nb_players} players is not enough for {nb_courts} court(s)")
    players = [str(i) for i in range(1, nb_players + 1)]
    nb_bench = nb_players - nb_courts * PLAYERS_PER_COURT
    rests = {p: 0 for p in players}
    last_rest = {p: -1 for p in players}
    partners, opponents, bench_mates = Counter(), Counter(), Counter()

    games_data = []
    for g in range(nb_games):
        bench = _choose_bench(players, nb_bench, rests, last_rest, g, rng, jitter, bench_mates,
                              bench_mate_cost)
        for p in bench:
            rests[p] += 1
            last_rest[p] = g
        for a, b in itertools.combinations(bench, 2):
            bench_mates[_pair(a, b)] += 1
        on_court = [p for p in players if p not in bench]
        courts = _choose_courts(on_court, nb_courts, partners, opponents, rng, team_tries)

        game = {"Game": f"p{g + 1}"}
        for c, (t1, t2) in enumerate(courts, 1):
            # SheetReader sorts team members numerically; do the same here.
            game[f"Terrain {c}"] = {"Team1": sorted(t1, key=int), "Team2": sorted(t2, key=int)}
            partners[_pair(*t1)] += 1
            partners[_pair(*t2)] += 1
            for a, b in itertools.product(t1, t2):
                opponents[_pair(a, b)] += 1
        if nb_bench:
            game["Bench"] = sorted(bench, key=int)
        games_data.append(game)
    return games_data


def optimize(nb_players: int, nb_courts: int, nb_games: int, tries: int = 5000,
             keep: int = 5, seed: int | None = None, weights: dict | None = None) -> list:
    """Generate ``tries`` sheets and return the ``keep`` best as [(SheetScore, games_data)].

    Sheets with an identical score and content are kept once.
    """
    rng = random.Random(seed)
    best: list[tuple[SheetScore, list]] = []
    seen = set()
    for _ in range(tries):
        games_data = generate_sheet(nb_players, nb_courts, nb_games, rng,
                                    jitter=rng.choice(JITTERS),
                                    bench_mate_cost=rng.choice(BENCH_MATE_COSTS))
        key = str(games_data)
        if key in seen:
            continue
        seen.add(key)
        score = score_sheet(games_data, weights)
        if len(best) < keep or score.total < best[-1][0].total:
            best.append((score, games_data))
            best.sort(key=lambda r: (r[0].total, r[0].as_tuple()))
            del best[keep:]
            if best[0][0].total == 0 and len(best) == keep and best[-1][0].total == 0:
                break  # cannot do better
    return best


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sheet_generator",
        description="Generate many random games sheets and keep the fairest ones "
                    "(see sheet_score.py for the score).",
    )
    parser.add_argument("-p", "--players", type=int, required=True, help="Number of players")
    parser.add_argument("-c", "--courts", type=int, default=1, help="Number of courts (default 1)")
    parser.add_argument("-g", "--games", type=int, required=True, help="Number of games in the night")
    parser.add_argument("-n", "--tries", type=int, default=5000,
                        help="Number of random sheets to try (default 5000)")
    parser.add_argument("-k", "--keep", type=int, default=5,
                        help="Number of best sheets to save (default 5)")
    parser.add_argument("-s", "--seed", type=int, default=None,
                        help="Random seed, to get the same result again")
    parser.add_argument("-o", "--output-dir", default="games/generated",
                        help="Directory for the generated sheets (default games/generated)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show details of the best sheet")
    args = parser.parse_args(argv)
    logging.getLogger("__main__").setLevel(logging.CRITICAL)

    start = time.time()
    try:
        results = optimize(args.players, args.courts, args.games, args.tries, args.keep, args.seed)
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    elapsed = time.time() - start

    os.makedirs(args.output_dir, exist_ok=True)
    prefix = f"{args.players:02d}j-{args.courts}t-{args.games}g"
    print(f"Tried {args.tries} sheets in {elapsed:.1f}s, best {len(results)} saved in {args.output_dir}/")
    print(f"\n{RANKING_HEADER}")
    for rank, (score, games_data) in enumerate(results, 1):
        GamesTable(games_data)  # sanity check: never write an invalid sheet
        path = os.path.join(args.output_dir, f"{prefix}-best-{rank:02d}.csv")
        write_csv_rows(path, games_to_csv_rows(games_data))
        print(score.ranking_row(rank, path))
    if args.verbose and results:
        print(f"\nBest sheet:\n{results[0][0].report()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
