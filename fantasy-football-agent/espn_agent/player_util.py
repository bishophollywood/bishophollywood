"""Defensive accessors for espn_api Player/BoxPlayer objects.

espn_api's attribute names have shifted slightly across versions, so these
helpers try the modern name first and fall back to older ones instead of
raising AttributeError.
"""

BENCH_SLOTS = {"BE", "IR"}
INACTIVE_STATUSES = {"OUT", "INJURY_RESERVE", "SUSPENSION", "DOUBTFUL"}


def projected_points(player) -> float:
    for attr in ("projected_points", "projected_total_points", "projected_avg_points"):
        value = getattr(player, attr, None)
        if value is not None:
            return float(value)
    return 0.0


def actual_points(player) -> float:
    for attr in ("points", "total_points"):
        value = getattr(player, attr, None)
        if value is not None:
            return float(value)
    return 0.0


def injury_status(player) -> str:
    return getattr(player, "injuryStatus", None) or getattr(player, "injury_status", None) or "ACTIVE"


def is_inactive(player) -> bool:
    return injury_status(player) in INACTIVE_STATUSES


def slot(player) -> str:
    return getattr(player, "slot_position", None) or getattr(player, "lineupSlot", None) or ""


def eligible_slots(player) -> set:
    return set(getattr(player, "eligibleSlots", []) or [])


def is_bench(player) -> bool:
    return slot(player) in BENCH_SLOTS


def points_per_game(player) -> float:
    """Season average points/game, falling back to projected average for
    players with no games played yet (rookies, early season)."""
    avg = getattr(player, "avg_points", 0) or 0
    if avg:
        return float(avg)
    return float(getattr(player, "projected_avg_points", 0) or 0)
