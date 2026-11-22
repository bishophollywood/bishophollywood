"""Start/sit recommendations for the current week's matchup."""
from collections import Counter
from dataclasses import dataclass

from espn_api.football import League

from . import player_util as pu


@dataclass
class SwapRecommendation:
    bench_player: str
    starter_player: str | None  # None when the slot is empty
    slot: str
    reason: str
    projected_gain: float


def _lineup_from_boxes(boxes, team_id: int):
    # league.box_scores() replaces home_team/away_team with Team objects once
    # resolved, so compare by id rather than the raw attribute.
    for box in boxes:
        if pu.team_id_of(box.home_team) == team_id:
            return box.home_lineup
        if pu.team_id_of(box.away_team) == team_id:
            return box.away_lineup
    return None


def find_my_lineup(league: League, team_id: int, week: int):
    return _lineup_from_boxes(league.box_scores(week), team_id)


def _required_starting_slots(boxes) -> Counter:
    # The league's lineup shape, inferred from the fullest lineup per slot
    # across every matchup this week rather than parsing league settings.
    required: Counter = Counter()
    for box in boxes:
        for lineup in (box.home_lineup, box.away_lineup):
            required |= Counter(
                pu.slot(p) for p in lineup if pu.slot(p) and not pu.is_bench(p)
            )
    return required


def recommend_lineup(league: League, team_id: int, week: int) -> list[SwapRecommendation]:
    boxes = league.box_scores(week)
    lineup = _lineup_from_boxes(boxes, team_id)
    if lineup is None:
        return []

    starters = [p for p in lineup if not pu.is_bench(p)]
    # Never recommend starting someone who is out, however they project.
    bench = [p for p in lineup if pu.is_bench(p) and not pu.is_inactive(p)]

    # Slots nobody is starting in score zero, so they are the biggest leak.
    filled = Counter(pu.slot(p) for p in starters)
    empty_slots = []
    for slot_name, needed in _required_starting_slots(boxes).items():
        empty_slots += [slot_name] * max(0, needed - filled[slot_name])

    # Build every valid (starter, bench) swap, since a bench player eligible
    # for multiple slots (e.g. an RB who also qualifies for FLEX) should be
    # placed wherever they add the most value — not wherever ESPN's lineup
    # list happens to put the eligible starter first.
    # Each candidate: (forced, gain, starter_key, starter, bench_player, slot)
    candidates = []
    for starter in starters:
        starter_slot = pu.slot(starter)
        for b in bench:
            if starter_slot not in pu.eligible_slots(b):
                continue
            gain = pu.projected_points(b) - pu.projected_points(starter)
            forced = pu.is_inactive(starter)
            if forced or gain > 0.5:
                candidates.append((forced, gain, starter.name, starter, b, starter_slot))

    for i, empty_slot in enumerate(empty_slots):
        for b in bench:
            if empty_slot not in pu.eligible_slots(b):
                continue
            gain = pu.projected_points(b)
            if gain > 0.5:
                candidates.append((True, gain, ("empty", empty_slot, i), None, b, empty_slot))

    # Forced (injury / empty-slot) moves always take priority; otherwise
    # assign the largest point gains first so each bench player lands in its
    # best slot.
    candidates.sort(key=lambda c: (not c[0], -c[1]))

    used_starters = set()
    used_bench = set()
    recommendations: list[SwapRecommendation] = []
    for forced, gain, starter_key, starter, b, slot_name in candidates:
        if starter_key in used_starters or b.name in used_bench:
            continue
        if starter is None:
            reason = f"an empty slot scores 0; projected {pu.projected_points(b):.1f} pts"
        elif forced:
            reason = f"{starter.name} is {pu.injury_status(starter)}"
        else:
            reason = f"projected {pu.projected_points(b):.1f} vs {pu.projected_points(starter):.1f} pts"
        recommendations.append(SwapRecommendation(
            bench_player=b.name,
            starter_player=starter.name if starter is not None else None,
            slot=slot_name,
            reason=reason,
            projected_gain=gain,
        ))
        used_starters.add(starter_key)
        used_bench.add(b.name)

    recommendations.sort(key=lambda r: r.projected_gain, reverse=True)
    return recommendations
