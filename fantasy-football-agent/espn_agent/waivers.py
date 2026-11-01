"""Waiver-wire pickup suggestions based on projected points by position."""
from dataclasses import dataclass
from datetime import date

from espn_api.football import League, Team

from . import player_util as pu

POSITIONS = ("QB", "RB", "WR", "TE", "FLEX", "D/ST", "K")
FREE_AGENT_POOL_SIZE = 60
SUGGESTIONS_PER_POSITION = 2
MIN_EDGE_TO_SUGGEST = 2.0


@dataclass
class WaiverSuggestion:
    add_player: str
    add_projected: float
    drop_player: str
    drop_projected: float
    position: str


@dataclass
class FreeAgentOption:
    name: str
    pro_team: str
    opponent: str
    projected_points: float
    game_date: object


def suggest_waivers(league: League, team: Team) -> list[WaiverSuggestion]:
    free_agents = league.free_agents(size=FREE_AGENT_POOL_SIZE)
    roster = team.roster
    # Dropping an IR-slotted player frees the IR slot, not a usable spot for
    # a healthy add — ESPN keeps IR capacity separate from the bench. Only
    # true bench players are real drop candidates for a waiver swap.
    bench = [p for p in roster if pu.slot(p) == "BE"]

    suggestions: list[WaiverSuggestion] = []

    by_position: dict[str, list] = {}
    for fa in free_agents:
        by_position.setdefault(fa.position, []).append(fa)

    for position, candidates in by_position.items():
        candidates.sort(key=pu.projected_points, reverse=True)
        weakest_bench = [b for b in bench if b.position == position]
        weakest_bench.sort(key=pu.projected_points)

        top_candidates = candidates[:SUGGESTIONS_PER_POSITION]
        for i, fa in enumerate(top_candidates):
            drop = weakest_bench[i] if i < len(weakest_bench) else (weakest_bench[0] if weakest_bench else None)
            if drop is None:
                continue
            edge = pu.projected_points(fa) - pu.projected_points(drop)
            if edge >= MIN_EDGE_TO_SUGGEST:
                suggestions.append(WaiverSuggestion(
                    add_player=fa.name,
                    add_projected=pu.projected_points(fa),
                    drop_player=drop.name,
                    drop_projected=pu.projected_points(drop),
                    position=position,
                ))

    suggestions.sort(key=lambda s: s.add_projected - s.drop_projected, reverse=True)
    return suggestions


def list_free_agents(
    league: League, position: str, count: int = 10, today_only: bool = False
) -> list[FreeAgentOption]:
    """Free agents at a position, ranked by this week's projected points.

    For a same-week streaming decision (e.g. a one-off D/ST pickup) rather
    than the season-long roster-fit logic in suggest_waivers().
    """
    week = league.current_week
    candidates = league.free_agents(week=week, size=50, position=position)
    candidates.sort(key=pu.projected_points, reverse=True)

    if today_only:
        today = date.today()
        candidates = [
            c for c in candidates
            if pu.game_date(c) is not None and pu.game_date(c).date() == today
        ]

    return [
        FreeAgentOption(
            name=c.name,
            pro_team=c.proTeam,
            opponent=pu.pro_opponent(c),
            projected_points=pu.projected_points(c),
            game_date=pu.game_date(c),
        )
        for c in candidates[:count]
    ]
