"""On-demand trade evaluation: compares points-per-game value of both sides."""
from dataclasses import dataclass

from espn_api.football import League

from . import player_util as pu


@dataclass
class TradeEvaluation:
    players_you_receive: list[str]
    players_you_send: list[str]
    value_received: float
    value_sent: float

    @property
    def net_value(self) -> float:
        return self.value_received - self.value_sent

    @property
    def verdict(self) -> str:
        if self.net_value > 1.0:
            return "Favors you"
        if self.net_value < -1.0:
            return "Favors the other team"
        return "Roughly even"


def _find_player_anywhere(league: League, name: str):
    name_lower = name.strip().lower()
    for team in league.teams:
        for player in team.roster:
            if player.name.lower() == name_lower:
                return player
    raise ValueError(f"Could not find rostered player named '{name}' in this league")


def evaluate_trade(league: League, receive: list[str], send: list[str]) -> TradeEvaluation:
    received_players = [_find_player_anywhere(league, n) for n in receive]
    sent_players = [_find_player_anywhere(league, n) for n in send]
    return TradeEvaluation(
        players_you_receive=[p.name for p in received_players],
        players_you_send=[p.name for p in sent_players],
        value_received=sum(pu.points_per_game(p) for p in received_players),
        value_sent=sum(pu.points_per_game(p) for p in sent_players),
    )
