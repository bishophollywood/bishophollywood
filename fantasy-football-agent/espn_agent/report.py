"""Builds the combined markdown weekly report."""
from .lineup import SwapRecommendation
from .matchup import MatchupPreview
from .waivers import WaiverSuggestion


def build_report(
    week: int,
    team_name: str,
    matchup: MatchupPreview | None,
    lineup_recs: list[SwapRecommendation],
    waiver_suggestions: list[WaiverSuggestion],
) -> str:
    lines = [f"# Fantasy Football Weekly Report — Week {week}", f"**Team:** {team_name}", ""]

    lines.append("## Matchup Preview")
    if matchup is None:
        lines.append("No matchup found for this week (bye week or season not started).")
    else:
        lines.append(f"**{matchup.my_team_name}**: {matchup.my_projected:.1f} projected pts")
        lines.append(f"**{matchup.opponent_name}**: {matchup.opponent_projected:.1f} projected pts")
        margin = matchup.my_projected - matchup.opponent_projected
        verb = "favored by" if margin >= 0 else "underdog by"
        lines.append(f"Projected margin: {verb} {abs(margin):.1f} pts")
        if matchup.injury_flags:
            lines.append("")
            lines.append("**Injury flags on your roster:** " + ", ".join(matchup.injury_flags))
        lines.append("")
        lines.append("**Your top projected scorers:**")
        for name, pts in matchup.my_top_players:
            lines.append(f"- {name}: {pts:.1f}")
        lines.append("")
        lines.append(f"**{matchup.opponent_name}'s top projected scorers:**")
        for name, pts in matchup.opponent_top_players:
            lines.append(f"- {name}: {pts:.1f}")
    lines.append("")

    lines.append("## Lineup Recommendations")
    if not lineup_recs:
        lines.append("Your projected-optimal starters are already in the lineup. No changes suggested.")
    else:
        for rec in lineup_recs:
            lines.append(
                f"- **Start {rec.bench_player}** over **{rec.starter_player}** at {rec.slot} "
                f"— {rec.reason} ({rec.projected_gain:+.1f} proj. pts)"
            )
    lines.append("")

    lines.append("## Waiver Wire Suggestions")
    if not waiver_suggestions:
        lines.append("No clear upgrades found on the waiver wire this week.")
    else:
        for s in waiver_suggestions:
            lines.append(
                f"- **Add {s.add_player}** ({s.position}, {s.add_projected:.1f} proj.) "
                f"→ **Drop {s.drop_player}** ({s.drop_projected:.1f} proj.)"
            )
    lines.append("")

    lines.append("## Trade Evaluator")
    lines.append(
        "Run on demand: `python main.py trade --receive \"Player A\" --send \"Player B,Player C\"`"
    )

    return "\n".join(lines) + "\n"
