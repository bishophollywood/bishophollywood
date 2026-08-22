"""Waiver-wire pickup suggestions based on projected points by position."""
from dataclasses import dataclass

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


def suggest_waivers(league: League, team: Team) -> list[WaiverSuggestion]:
    free_agents = league.free_agents(size=FREE_AGENT_POOL_SIZE)
    roster = team.roster
    bench = [p for p in roster if pu.is_bench(p)]

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
