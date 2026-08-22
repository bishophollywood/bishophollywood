"""Start/sit recommendations for the current week's matchup."""
from dataclasses import dataclass

from espn_api.football import League

from . import player_util as pu


@dataclass
class SwapRecommendation:
    bench_player: str
    starter_player: str
    slot: str
    reason: str
    projected_gain: float


def _find_my_lineup(league: League, team_id: int, week: int):
    # espn_api's BoxScore.home_team/away_team are plain team_id ints, not Team objects.
    for box in league.box_scores(week):
        if box.home_team == team_id:
            return box.home_lineup
        if box.away_team == team_id:
            return box.away_lineup
    return None


def recommend_lineup(league: League, team_id: int, week: int) -> list[SwapRecommendation]:
    lineup = _find_my_lineup(league, team_id, week)
    if lineup is None:
        return []

    starters = [p for p in lineup if not pu.is_bench(p)]
    bench = [p for p in lineup if pu.is_bench(p)]

    recommendations: list[SwapRecommendation] = []
    used_bench_names = set()

    for starter in starters:
        starter_slot = pu.slot(starter)
        candidates = [
            b for b in bench
            if b.name not in used_bench_names and starter_slot in pu.eligible_slots(b)
        ]
        if not candidates:
            continue

        best = max(candidates, key=pu.projected_points)

        if pu.is_inactive(starter):
            recommendations.append(SwapRecommendation(
                bench_player=best.name,
                starter_player=starter.name,
                slot=starter_slot,
                reason=f"{starter.name} is {pu.injury_status(starter)}",
                projected_gain=pu.projected_points(best) - pu.projected_points(starter),
            ))
            used_bench_names.add(best.name)
            continue

        gain = pu.projected_points(best) - pu.projected_points(starter)
        if gain > 0.5:
            recommendations.append(SwapRecommendation(
                bench_player=best.name,
                starter_player=starter.name,
                slot=starter_slot,
                reason=f"projected {pu.projected_points(best):.1f} vs {pu.projected_points(starter):.1f} pts",
                projected_gain=gain,
            ))
            used_bench_names.add(best.name)

    recommendations.sort(key=lambda r: r.projected_gain, reverse=True)
    return recommendations
