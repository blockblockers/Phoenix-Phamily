"""Phoenix Phamily ESPN weekly recap collector. No credentials written to disk."""
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from espn_api.football import League

LEAGUE_ID = 1106154
YEAR = 2026


def number(value):
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


def player_details(player):
    return {
        "name": getattr(player, "name", "Unknown"),
        "position": getattr(player, "position", None),
        "pro_team": getattr(player, "proTeam", None),
        "points": number(getattr(player, "points", None)),
        "projected_points": number(getattr(player, "projected_points", None)),
        "slot": getattr(player, "slot_position", None),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--week", type=int, help="Week to export; defaults to last completed week")
    args = parser.parse_args()
    s2 = os.environ.get("ESPN_S2")
    swid = os.environ.get("ESPN_SWID")
    if not s2 or not swid:
        raise SystemExit("Missing ESPN_S2 or ESPN_SWID environment secret")
    league = League(league_id=LEAGUE_ID, year=YEAR, espn_s2=s2, swid=swid)
    current_week = int(league.current_week)
    week = args.week if args.week is not None else current_week - 1
    if week < 1 or week >= current_week:
        raise SystemExit(f"Week {week} not completed according to ESPN (current week: {current_week}). Try --week for a completed week.")
    boxes = league.box_scores(week=week)
    if not boxes:
        raise SystemExit(f"No box scores returned for week {week}; not publishing empty results")
    teams = {}
    matches = []
    for box in boxes:
        home, away = box.home_team, box.away_team
        if not home or not away:
            raise SystemExit("Missing matchup team; refusing to publish partial results")
        hs, aws = number(box.home_score), number(box.away_score)
        if hs is None or aws is None:
            raise SystemExit("Missing score; refusing to publish partial results")
        hid, aid = int(home.team_id), int(away.team_id)
        teams[hid] = {"id": hid, "name": home.team_name, "points": hs}
        teams[aid] = {"id": aid, "name": away.team_name, "points": aws}
        matches.append({"home_id": hid, "away_id": aid, "home_score": hs, "away_score": aws,
                        "home_lineup": [player_details(p) for p in (box.home_lineup or [])],
                        "away_lineup": [player_details(p) for p in (box.away_lineup or [])]})
    if len(teams) != len(league.teams):
        raise SystemExit(f"Only {len(teams)} of {len(league.teams)} teams represented; refusing partial report")
    ranked = sorted(teams.values(), key=lambda t: (-t["points"], t["name"]))
    # Equal scores straddling the halfway cutoff require manual adjudication.
    half = len(ranked) // 2
    if len(ranked) % 2 or (half and ranked[half - 1]["points"] == ranked[half]["points"]):
        raise SystemExit("Odd team count or bonus cutoff tie: manual review required")
    bonus_ids = {t["id"] for t in ranked[:half]}
    for t in ranked:
        t["bonus_win"] = int(t["id"] in bonus_ids)
        t["head_to_head_win"] = 0
        t["head_to_head_tie"] = 0
    for m in matches:
        h, a = teams[m["home_id"]], teams[m["away_id"]]
        if m["home_score"] > m["away_score"]:
            h["head_to_head_win"] = 1
        elif m["away_score"] > m["home_score"]:
            a["head_to_head_win"] = 1
        else:
            h["head_to_head_tie"] = a["head_to_head_tie"] = 1
    for t in ranked:
        t["weekly_wins"] = t["bonus_win"] + t["head_to_head_win"]
    output = {"league": "Phoenix Phamily", "league_id": LEAGUE_ID, "year": YEAR, "week": week,
              "generated_utc": datetime.now(timezone.utc).isoformat(),
              "note": "Scoring ranks are weekly point ranks, not editorial power rankings. Review lineup slots and ESPN score corrections.",
              "scoring_ranks": ranked, "matchups": matches}
    path = Path("reports")
    path.mkdir(exist_ok=True)
    json_file = path / f"week-{week:02d}.json"
    json_file.write_text(json.dumps(output, indent=2), encoding="utf-8")
    lines = [f"# Phoenix Phamily — Week {week} stats", "", "## Weekly scoring ranks and wins", "",
             "| Rank | Team | Points | H2H win | Bonus win | Total weekly wins |",
             "|---:|---|---:|---:|---:|---:|"]
    for i, t in enumerate(ranked, 1):
        lines.append(f"| {i} | {t['name']} | {t['points']:.2f} | {t['head_to_head_win']} | {t['bonus_win']} | {t['weekly_wins']} |")
    lines += ["", "## Matchups", ""]
    for m in matches:
        h, a = teams[m["home_id"]], teams[m["away_id"]]
        lines.append(f"### {a['name']} {m['away_score']:.2f} — {h['name']} {m['home_score']:.2f}")
        lines.append(f"Margin: {abs(m['home_score'] - m['away_score']):.2f}")
        for label in ("away", "home"):
            lineup = m[f"{label}_lineup"]
            # Bench and IR players are excluded from scoring standout analysis.
            starters = [p for p in lineup if str(p['slot']).upper() not in ("BE", "IR") and p['points'] is not None]
            starters.sort(key=lambda p: -p["points"])
            lines.append(f"{label.title()} starter highlights: " + (", ".join(f"{p['name']} ({p['points']:.2f})" for p in starters[:5]) or "not available"))
        lines.append("")
    lines += ["## Recap instructions", "", "Write ~1,200 words with an intro, every matchup, scoring bonuses, power rankings, and team-name-specific trash talk. Never confuse head-to-head wins with bonus wins. Scoring rank is not the same as a subjective power ranking. Do not invent injury, transaction, season record, or player data absent from this report."]
    md_file = path / f"week-{week:02d}.md"
    md_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Created {json_file} and {md_file}")


if __name__ == "__main__":
    main()
