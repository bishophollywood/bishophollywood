"""Loads ESPN league configuration from environment variables (.env locally, secrets in CI)."""
import os
from dataclasses import dataclass
from datetime import date

from dotenv import load_dotenv

load_dotenv()


def _default_season_year() -> int:
    today = date.today()
    # ESPN's "year" is the calendar year the season started in. The league year
    # rolls over in March, well before a new season's rosters are set.
    return today.year if today.month >= 3 else today.year - 1


def _require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Missing required environment variable {name}. "
            f"Copy .env.example to .env and fill it in (see README)."
        )
    return value


@dataclass(frozen=True)
class Config:
    league_id: int
    season_year: int
    team_id: int
    espn_s2: str
    swid: str
    report_output: str


def load_config() -> Config:
    league_id = int(_require("ESPN_LEAGUE_ID"))
    team_id = int(_require("ESPN_TEAM_ID"))
    season_year = int(os.environ.get("ESPN_SEASON_YEAR") or _default_season_year())
    espn_s2 = _require("ESPN_S2")
    swid = _require("ESPN_SWID")
    report_output = os.environ.get("REPORT_OUTPUT") or "reports/latest.md"
    return Config(
        league_id=league_id,
        season_year=season_year,
        team_id=team_id,
        espn_s2=espn_s2,
        swid=swid,
        report_output=report_output,
    )
