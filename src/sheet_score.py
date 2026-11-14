"""Global fairness score for a games sheet (pure logic, no GUI).

The score is a penalty: **lower is better, 0 is a perfect sheet**.

Four criteria are measured, in priority order:

1. games     - every player plays the same number of games.
2. pauses    - the number of games played between two pauses is the same for everybody.
3. partners  - players team with as many different partners as possible.
4. opponents - players face as many different opponents as possible.

Each criterion is measured the same way: we count how far a distribution of
integers (games per player, games between pauses, times each pair teamed up,
times each pair faced each other) is from the most even distribution
possible with the same total. ``_excess`` returns that distance, which roughly
reads as "number of units that would have to move to make it perfectly
even". Because of this, an unavoidable imbalance (e.g. 11 players sharing 40
playing slots can't all play the same number of games) costs nothing, and only
avoidable imbalance is penalized.

The global score is the weighted sum of the four penalties. Weights decrease
by a factor of 10 to reflect the priority order (see ``DEFAULT_WEIGHTS``).

Scores are meant to compare sheets for the same configuration (same
players, courts and number of games).
"""

import argparse
import itertools
import logging
import os
from collections import Counter
from dataclasses import dataclass, field

_logger = logging.getLogger("__main__")

CRITERIA = ("games", "pauses", "partners", "opponents")
DEFAULT_WEIGHTS = {"games": 1000.0, "pauses": 100.0, "partners": 10.0, "opponents": 1.0}


def _excess(counts: list[int], total: int | None = None, nb_slots: int | None = None) -> float:
    """Distance between ``counts`` and the most even integer distribution of the same total.

    Args:
        counts: observed integer values (missing slots are treated as 0).
        total: sum to distribute; defaults to ``sum(counts)``.
        nb_slots: number of slots the total is distributed over; defaults to ``len(counts)``.
            Use it when some slots never appear in ``counts`` (e.g. pairs that never met).

    Returns:
        (sum of squares - minimal sum of squares) / 2. It's 0 when every value is
        the floor or ceiling of the mean; moving one unit from a value to another
        one 2 lower reduces it by 1.
    """
    if total is None:
        total = sum(counts)
    if nb_slots is None:
        nb_slots = len(counts)
    if nb_slots == 0:
        return 0.0
    q, r = divmod(total, nb_slots)
    min_sum_sq = (nb_slots - r) * q * q + r * (q + 1) * (q + 1)
    return (sum(c * c for c in counts) - min_sum_sq) / 2


def _iter_courts(game: dict):
    """Yield (team1, team2) for each court of a game."""
    for key, value in game.items():
        if key in ("Game", "Bench"):
            continue
        yield value.get("Team1", []), value.get("Team2", [])


def _players(games_data: list) -> list:
    players = set()
    for game in games_data:
        players.update(game.get("Bench", []))
        for team1, team2 in _iter_courts(game):
            players.update(team1)
            players.update(team2)
    players.discard("")
    return sorted(players)


def _pair(a: str, b: str) -> tuple:
    return (a, b) if a <= b else (b, a)


@dataclass
class SheetScore:
    """Detailed fairness score of a games sheet. Lower is better, 0 is perfect."""

    games: float = 0.0
    pauses: float = 0.0
    partners: float = 0.0
    opponents: float = 0.0
    weights: dict = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    # Informative details, not used in the total.
    games_per_player: dict = field(default_factory=dict)
    gaps_per_player: dict = field(default_factory=dict)
    back_to_back_pauses: list = field(default_factory=list)
    partner_counts: Counter = field(default_factory=Counter)
    opponent_counts: Counter = field(default_factory=Counter)
    nb_players: int = 0

    @property
    def total(self) -> float:
        return sum(self.weights[c] * getattr(self, c) for c in CRITERIA)

    def as_tuple(self) -> tuple:
        """Strict priority ordering key: compare criterion 1 first, then 2, etc."""
        return tuple(getattr(self, c) for c in CRITERIA)

    def _pair_summary(self, counts: Counter) -> str:
        nb_pairs = self.nb_players * (self.nb_players - 1) // 2
        never = nb_pairs - len(counts)
        most = max(counts.values()) if counts else 0
        most_pairs = [f"{a}-{b}" for (a, b), c in sorted(counts.items()) if c == most]
        return (f"never={never}/{nb_pairs} pairs, most={most}x "
                f"({', '.join(most_pairs[:6])}{', ...' if len(most_pairs) > 6 else ''})")

    def report(self) -> str:
        lines = [f"Fairness score: {self.total:.1f} (lower is better, 0 = perfect)"]
        labels = {
            "games": "Games per player",
            "pauses": "Games between pauses",
            "partners": "Partner repeats",
            "opponents": "Opponent repeats",
        }
        for c in CRITERIA:
            value = getattr(self, c)
            lines.append(f"  {labels[c]:<22s} {value:6.1f} x {self.weights[c]:<6g} = "
                         f"{value * self.weights[c]:8.1f}")
        if self.games_per_player:
            g = self.games_per_player.values()
            lines.append(f"    games played: {min(g)} - {max(g)}")
        all_gaps = [x for gaps in self.gaps_per_player.values() for x in gaps]
        if all_gaps:
            lines.append(f"    games between pauses: {min(all_gaps)} - {max(all_gaps)}")
        if self.back_to_back_pauses:
            lines.append(f"    back-to-back pauses: {', '.join(self.back_to_back_pauses)}")
        lines.append(f"    partners:  {self._pair_summary(self.partner_counts)}")
        lines.append(f"    opponents: {self._pair_summary(self.opponent_counts)}")
        return "\n".join(lines)


def score_sheet(games_data: list, weights: dict | None = None) -> SheetScore:
    """Compute the fairness score of a (valid) games sheet.

    Args:
        games_data: list of games as produced by ``SheetReader.read()``.
        weights: optional per-criterion weights overriding ``DEFAULT_WEIGHTS``.
    """
    score = SheetScore()
    if weights:
        score.weights.update(weights)
    if not games_data:
        return score

    players = _players(games_data)
    nb_players = len(players)
    score.nb_players = nb_players
    nb_pairs = nb_players * (nb_players - 1) // 2

    # 1. Games played per player
    games_per_player = {p: 0 for p in players}
    for game in games_data:
        for team1, team2 in _iter_courts(game):
            for p in team1 + team2:
                if p in games_per_player:
                    games_per_player[p] += 1
    score.games_per_player = games_per_player
    score.games = _excess(list(games_per_player.values()))

    # 2. Games played between two consecutive pauses (games before the first
    #    pause and after the last pause are ignored, like PlayerStatistics).
    gaps_per_player = {}
    for p in players:
        paused_at = [i for i, game in enumerate(games_data) if p in game.get("Bench", [])]
        gaps = [b - a - 1 for a, b in zip(paused_at, paused_at[1:])]
        gaps_per_player[p] = gaps
        if 0 in gaps:
            score.back_to_back_pauses.append(p)
    score.gaps_per_player = gaps_per_player
    all_gaps = [x for gaps in gaps_per_player.values() for x in gaps]
    # Back-to-back pauses cost one extra point each on top of the unevenness.
    score.pauses = _excess(all_gaps) + all_gaps.count(0)

    # 3 & 4. Partners and opponents
    for game in games_data:
        for team1, team2 in _iter_courts(game):
            for team in (team1, team2):
                for a, b in itertools.combinations(team, 2):
                    score.partner_counts[_pair(a, b)] += 1
            for a, b in itertools.product(team1, team2):
                score.opponent_counts[_pair(a, b)] += 1
    score.partners = _excess(list(score.partner_counts.values()),
                             sum(score.partner_counts.values()), nb_pairs)
    score.opponents = _excess(list(score.opponent_counts.values()),
                              sum(score.opponent_counts.values()), nb_pairs)
    return score


def main(argv: list | None = None) -> int:
    from games_table import GamesTable  # pylint: disable=import-outside-toplevel
    from sheet_reader import SheetReader  # pylint: disable=import-outside-toplevel

    parser = argparse.ArgumentParser(
        prog="sheet_score",
        description="Compute the fairness score of one or more games sheets and rank them "
                    "(lower is better).",
    )
    parser.add_argument("csv_files", nargs="+")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show score details")
    args = parser.parse_args(argv)
    # GamesTable/SheetReader log every validation error; the summary line below is enough.
    logging.getLogger("__main__").setLevel(logging.CRITICAL)

    results = []
    for csv_file in args.csv_files:
        if not os.path.isfile(csv_file):
            print(f"{csv_file}: file not found")
            continue
        try:
            games_data = SheetReader(csv_file).read()
            GamesTable(games_data)  # validates the sheet
        except Exception as e:  # pylint: disable=broad-exception-caught
            # GamesTable raises "Invalid games table:" followed by one error per line.
            reasons = [line for line in str(e).splitlines()
                       if line.strip() and not line.startswith("Invalid games table")]
            print(f"{csv_file}: invalid sheet, skipped")
            for reason in reasons or [str(e)]:
                print(f"    {reason}")
            continue
        score = score_sheet(games_data)
        results.append((score, csv_file))
        if args.verbose:
            print(f"\n{csv_file}\n{score.report()}")

    if not results:
        return 1
    results.sort(key=lambda r: (r[0].total, r[0].as_tuple()))
    print(f"\n{'Rank':>4}  {'Score':>8}  {'Games':>6} {'Pauses':>6} {'Partn':>6} {'Oppon':>6}  File")
    for rank, (score, csv_file) in enumerate(results, 1):
        print(f"{rank:>4}  {score.total:8.1f}  {score.games:6.1f} {score.pauses:6.1f} "
              f"{score.partners:6.1f} {score.opponents:6.1f}  {csv_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
