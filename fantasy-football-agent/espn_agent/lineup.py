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
    # league.box_scores() replaces home_team/away_team with Team objects once
    # resolved, so compare by id rather than the raw attribute.
    for box in league.box_scores(week):
        if pu.team_id_of(box.home_team) == team_id:
            return box.home_lineup
        if pu.team_id_of(box.away_team) == team_id:
            return box.away_lineup
    return None


def recommend_lineup(league: League, team_id: int, week: int) -> list[SwapRecommendation]:
    lineup = _find_my_lineup(league, team_id, week)
    if lineup is None:
        return []

    starters = [p for p in lineup if not pu.is_bench(p)]
    bench = [p for p in lineup if pu.is_bench(p)]

    # Build every valid (starter, bench) swap, since a bench player eligible
    # for multiple slots (e.g. an RB who also qualifies for FLEX) should be
    # placed wherever they add the most value — not wherever ESPN's lineup
    # list happens to put the eligible starter first.
    candidates = []
    for starter in starters:
        starter_slot = pu.slot(starter)
        for b in bench:
            if starter_slot not in pu.eligible_slots(b):
                continue
            gain = pu.projected_points(b) - pu.projected_points(starter)
            forced = pu.is_inactive(starter)
            if forced or gain > 0.5:
                candidates.append((forced, gain, starter, b, starter_slot))

    # Forced (injury) swaps always take priority; otherwise assign the
    # largest point gains first so each bench player lands in its best slot.
    candidates.sort(key=lambda c: (not c[0], -c[1]))

    used_starters = set()
    used_bench = set()
    recommendations: list[SwapRecommendation] = []
    for forced, gain, starter, b, starter_slot in candidates:
        if starter.name in used_starters or b.name in used_bench:
            continue
        reason = (
            f"{starter.name} is {pu.injury_status(starter)}" if forced
            else f"projected {pu.projected_points(b):.1f} vs {pu.projected_points(starter):.1f} pts"
        )
        recommendations.append(SwapRecommendation(
            bench_player=b.name,
            starter_player=starter.name,
            slot=starter_slot,
            reason=reason,
            projected_gain=gain,
        ))
        used_starters.add(starter.name)
        used_bench.add(b.name)

    recommendations.sort(key=lambda r: r.projected_gain, reverse=True)
    return recommendations
