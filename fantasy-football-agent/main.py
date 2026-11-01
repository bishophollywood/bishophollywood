"""CLI entry point for the ESPN fantasy football agent.

Usage:
    python main.py report                 # generate the weekly report (default)
    python main.py trade --receive "Ja'Marr Chase" --send "DK Metcalf,James Cook"
"""
import argparse
import os
import sys

from espn_agent import client, player_util as pu
from espn_agent.config import load_config
from espn_agent.lineup import recommend_lineup
from espn_agent.matchup import get_matchup_preview
from espn_agent.report import build_report
from espn_agent.trades import evaluate_trade
from espn_agent.waivers import list_free_agents, suggest_waivers


def run_report(week: int | None) -> str:
    config = load_config()
    league = client.connect(config)
    team = client.get_my_team(league, config.team_id)
    target_week = week or client.current_week(league)

    matchup = get_matchup_preview(league, config.team_id, target_week)
    lineup_recs = recommend_lineup(league, config.team_id, target_week)
    waiver_suggestions = suggest_waivers(league, team)

    report = build_report(
        week=target_week,
        team_name=getattr(team, "team_name", str(config.team_id)),
        matchup=matchup,
        lineup_recs=lineup_recs,
        waiver_suggestions=waiver_suggestions,
    )

    os.makedirs(os.path.dirname(config.report_output) or ".", exist_ok=True)
    with open(config.report_output, "w") as f:
        f.write(report)

    return report


def run_trade(receive: list[str], send: list[str]) -> str:
    config = load_config()
    league = client.connect(config)
    result = evaluate_trade(league, receive, send)

    lines = [
        "# Trade Evaluation",
        f"**You receive:** {', '.join(result.players_you_receive)} "
        f"({result.value_received:.1f} pts/game combined)",
        f"**You send:** {', '.join(result.players_you_send)} "
        f"({result.value_sent:.1f} pts/game combined)",
        f"**Net value:** {result.net_value:+.1f} pts/game — {result.verdict}",
    ]
    return "\n".join(lines) + "\n"


def run_player(name: str) -> str:
    config = load_config()
    league = client.connect(config)
    player = league.player_info(name=name)
    if player is None:
        return f"No player found matching '{name}'."

    lines = [
        f"# {player.name}",
        f"**Position:** {player.position} ({player.proTeam})",
        f"**Injury status:** {pu.injury_status(player)}",
        f"**Season projected pts:** {pu.projected_points(player):.1f}",
        f"**Season avg pts/game:** {pu.points_per_game(player):.1f}",
    ]
    return "\n".join(lines) + "\n"


def run_freeagents(position: str, count: int, today_only: bool) -> str:
    config = load_config()
    league = client.connect(config)
    options = list_free_agents(league, position, count=count, today_only=today_only)

    if not options:
        scope = "playing today" if today_only else "available"
        return f"No free agent {position} options {scope} right now.\n"

    lines = [f"# Free Agent {position} Options" + (" (playing today)" if today_only else "")]
    for opt in options:
        kickoff = opt.game_date.strftime("%a %I:%M %p") if opt.game_date else "bye/unknown"
        lines.append(
            f"- **{opt.name}** ({opt.pro_team}) vs {opt.opponent} — "
            f"{opt.projected_points:.1f} proj. pts — {kickoff}"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="ESPN fantasy football assistant")
    subparsers = parser.add_subparsers(dest="command")

    report_parser = subparsers.add_parser("report", help="Generate the weekly report")
    report_parser.add_argument("--week", type=int, default=None, help="Week number (defaults to current week)")

    trade_parser = subparsers.add_parser("trade", help="Evaluate a proposed trade")
    trade_parser.add_argument("--receive", required=True, help="Comma-separated players you would receive")
    trade_parser.add_argument("--send", required=True, help="Comma-separated players you would send")

    player_parser = subparsers.add_parser("player", help="Look up a player's current status")
    player_parser.add_argument("--name", required=True, help="Player's full name, e.g. 'Zay Flowers'")

    fa_parser = subparsers.add_parser("freeagents", help="List top free agents at a position")
    fa_parser.add_argument("--position", required=True, help="e.g. 'D/ST', 'RB', 'WR', 'TE', 'QB', 'K'")
    fa_parser.add_argument("--count", type=int, default=10, help="How many to list (default 10)")
    fa_parser.add_argument("--today", action="store_true", help="Only show options whose pro team plays today")

    args = parser.parse_args()

    try:
        if args.command == "trade":
            output = run_trade(
                receive=[p.strip() for p in args.receive.split(",")],
                send=[p.strip() for p in args.send.split(",")],
            )
        elif args.command == "player":
            output = run_player(args.name)
        elif args.command == "freeagents":
            output = run_freeagents(args.position, args.count, args.today)
        else:
            output = run_report(getattr(args, "week", None))
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
