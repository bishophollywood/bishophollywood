"""Projected-score preview of the current week's matchup."""
from dataclasses import dataclass

from espn_api.football import League

from . import player_util as pu


@dataclass
class MatchupPreview:
    my_team_name: str
    opponent_name: str
    my_projected: float
    opponent_projected: float
    my_top_players: list[tuple[str, float]]
    opponent_top_players: list[tuple[str, float]]
    injury_flags: list[str]


def _starters(lineup):
    return [p for p in lineup if not pu.is_bench(p)]


def _top_players(lineup, n=3) -> list[tuple[str, float]]:
    starters = sorted(_starters(lineup), key=pu.projected_points, reverse=True)
    return [(p.name, pu.projected_points(p)) for p in starters[:n]]


def _team_name(league: League, team_id) -> str:
    if team_id is None:
        return "Bye Week"
    for team in league.teams:
        if team.team_id == team_id:
            return team.team_name
    return "Unknown Team"


def get_matchup_preview(league: League, team_id: int, week: int) -> MatchupPreview | None:
    # espn_api's BoxScore.home_team/away_team are plain team_id ints, not Team objects.
    for box in league.box_scores(week):
        is_home = box.home_team == team_id
        is_away = box.away_team == team_id
        if not (is_home or is_away):
            continue

        my_lineup, opp_lineup = (box.home_lineup, box.away_lineup) if is_home else (box.away_lineup, box.home_lineup)
        opp_team_id = box.away_team if is_home else box.home_team

        my_starters = _starters(my_lineup)
        opp_starters = _starters(opp_lineup)

        injury_flags = [
            f"{p.name} ({pu.injury_status(p)})"
            for p in my_starters
            if pu.is_inactive(p)
        ]

        return MatchupPreview(
            my_team_name=_team_name(league, team_id),
            opponent_name=_team_name(league, opp_team_id),
            my_projected=sum(pu.projected_points(p) for p in my_starters),
            opponent_projected=sum(pu.projected_points(p) for p in opp_starters),
            my_top_players=_top_players(my_lineup),
            opponent_top_players=_top_players(opp_lineup),
            injury_flags=injury_flags,
        )
    return None
