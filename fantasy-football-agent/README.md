# ESPN Fantasy Football Agent

An all-in-one assistant for a private ESPN fantasy football league. Each week it:

- **Previews your matchup** — projected score for you vs. your opponent, top projected scorers on both sides, injury flags on your roster.
- **Recommends lineup swaps** — flags bench players projected to outscore a starter, and starters who are Out/Doubtful.
- **Suggests waiver-wire pickups** — compares available free agents against your weakest bench players at the same position.
- **Evaluates trades on demand** — `python main.py trade --receive "..." --send "..."` compares points-per-game value on both sides of a proposed trade.

It runs automatically via GitHub Actions (`.github/workflows/fantasy-weekly-report.yml`) every Wednesday during the NFL season and posts the report as a GitHub issue in this repo. You can also run it manually, locally or via the Actions tab ("Run workflow").

## Setup

### 1. Install dependencies (for local runs)

```bash
cd fantasy-football-agent
pip install -r requirements.txt
cp .env.example .env
```

### 2. Find your league ID and team ID

- **League ID**: open your league on ESPN in a browser; the URL contains `leagueId=XXXXXXX`.
- **Team ID**: click into "My Team"; the URL contains `teamId=X`.

Fill these into `.env` as `ESPN_LEAGUE_ID` and `ESPN_TEAM_ID`.

### 3. Getting your ESPN cookies (required for private leagues)

ESPN's fantasy API isn't public for private leagues, so the agent authenticates using two cookies from your browser session:

1. Log in to [fantasy.espn.com](https://fantasy.espn.com) in your browser.
2. Open DevTools (F12) → **Application** (Chrome) or **Storage** (Firefox) tab → **Cookies** → `https://fantasy.espn.com`.
3. Copy the values of:
   - `espn_s2` → set as `ESPN_S2`
   - `SWID` → set as `ESPN_SWID` (keep the curly braces, e.g. `{ABCD1234-...}`)

These cookies expire periodically (typically after a year or on logout) — if the agent starts failing to authenticate, repeat this step.

**Never commit `.env` or these values to git.** `.gitignore` already excludes `.env`.

### 4. Run it locally

```bash
python main.py report                # generate this week's report -> reports/latest.md
python main.py report --week 5       # generate for a specific week
python main.py trade --receive "Ja'Marr Chase" --send "DK Metcalf,James Cook"
```

### 5. Set up the scheduled automation

In the GitHub repo, go to **Settings → Secrets and variables → Actions** and add these repository secrets:

| Secret | Value |
|---|---|
| `ESPN_LEAGUE_ID` | your league ID |
| `ESPN_TEAM_ID` | your team ID |
| `ESPN_SEASON_YEAR` | *(optional)* season year, e.g. `2026`; auto-detected if omitted |
| `ESPN_S2` | your `espn_s2` cookie value |
| `ESPN_SWID` | your `SWID` cookie value |

The workflow runs every Wednesday at 12:00 UTC during the season (Sept–Jan) and opens a GitHub issue with the report. You'll get a notification the same way you get notified for any GitHub issue (check your GitHub notification settings for email delivery). You can also trigger it manually from the **Actions** tab via "Run workflow".

## Project layout

```
fantasy-football-agent/
  main.py                 CLI entry point (report / trade commands)
  espn_agent/
    config.py              env var loading
    client.py               ESPN League connection wrapper
    player_util.py          defensive accessors for espn_api's Player fields
    lineup.py                start/sit recommendations
    waivers.py                free-agent pickup suggestions
    matchup.py                 weekly matchup projection
    trades.py                   trade value evaluator
    report.py                    combines everything into the markdown report
```

## Notes / limitations

- Built on the community [`espn_api`](https://github.com/cwendt94/espn-api) package, which reverse-engineers ESPN's private endpoints — it can break if ESPN changes its API. If `pip install -r requirements.txt` gives you a working-but-stale version, try `pip install --upgrade espn_api`.
- Waiver suggestions and trade value use projected points / points-per-game as a simple proxy for player value — they're a starting point for your own judgment, not gospel.
- Trade evaluation isn't part of the automated weekly report since trade offers are ad hoc; run it manually when you have an offer to check.
