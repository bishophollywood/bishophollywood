"""Thin wrapper around espn_api.football.League for this agent's needs."""
from espn_api.football import League, Team

from .config import Config


def connect(config: Config) -> League:
    return League(
        league_id=config.league_id,
        year=config.season_year,
        espn_s2=config.espn_s2,
        swid=config.swid,
    )


def get_my_team(league: League, team_id: int) -> Team:
    for team in league.teams:
        if team.team_id == team_id:
            return team
    known_ids = ", ".join(f"{t.team_id} ({t.team_name})" for t in league.teams)
    raise RuntimeError(
        f"No team with team_id={team_id} in this league. Known teams: {known_ids}"
    )


def current_week(league: League) -> int:
    week = getattr(league, "current_week", None)
    if week:
        return week
    # Fallback for older espn_api versions.
    return getattr(league, "currentMatchupPeriod", 1)
