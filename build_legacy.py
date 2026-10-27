"""One-time/on-demand ESPN historical archive rebuild; never runs in weekly collection."""
import os
import argparse
from espn_api.football import League
from legacy import build_archive, extract_owner_ids, ARCHIVE
import json

p = argparse.ArgumentParser()
p.add_argument('--through', type=int, default=2025)
p.add_argument('--from-year', type=int, default=int(os.getenv('RECAP_ARCHIVE_START_YEAR', '2013')))
a = p.parse_args()
if not 2000 <= a.from_year <= a.through <= int(os.getenv('RECAP_SEASON', '2026')) - 1:
    p.error('Archive range must be from 2000 through the year before the current season')
s2, swid = os.getenv('ESPN_S2'), os.getenv('ESPN_SWID')
if not s2 or not swid:
    p.error('ESPN_S2 and ESPN_SWID environment variables required')
factory = lambda year: League(league_id=int(os.getenv("RECAP_LEAGUE_ID", "1106154")), year=year, espn_s2=s2, swid=swid)
archive = build_archive(factory, a.through, start_year=a.from_year)
try:
    current = factory(int(os.getenv("RECAP_SEASON", "2026")))
    archive['current_teams'] = [
        {'team_id': int(t.team_id), 'name': t.team_name, 'owner_ids': extract_owner_ids(t)}
        for t in current.teams
    ]
except Exception as exc:
    archive.setdefault('warnings', []).append({'year': int(os.getenv('RECAP_SEASON', '2026')), 'error': 'Current owner snapshot: ' + str(exc)[:200]})
ARCHIVE.write_text(json.dumps(archive, indent=2), encoding='utf-8')
