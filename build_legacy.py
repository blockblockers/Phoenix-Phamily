"""One-time/on-demand ESPN historical archive rebuild; never runs in weekly collection."""
import os
import argparse
from espn_api.football import League
from legacy import build_archive, extract_owner_ids, ARCHIVE
import json

p = argparse.ArgumentParser()
p.add_argument('--through', type=int, default=2025)
a = p.parse_args()
if not 2013 <= a.through <= 2025:
    p.error('--through must be between 2013 and 2025')
s2, swid = os.getenv('ESPN_S2'), os.getenv('ESPN_SWID')
if not s2 or not swid:
    p.error('ESPN_S2 and ESPN_SWID environment variables required')
factory = lambda year: League(league_id=1106154, year=year, espn_s2=s2, swid=swid)
archive = build_archive(factory, a.through)
try:
    current = factory(2026)
    archive['current_teams'] = [
        {'team_id': int(t.team_id), 'name': t.team_name, 'owner_ids': extract_owner_ids(t)}
        for t in current.teams
    ]
except Exception as exc:
    archive.setdefault('warnings', []).append({'year': 2026, 'error': 'Current owner snapshot: ' + str(exc)[:200]})
ARCHIVE.write_text(json.dumps(archive, indent=2), encoding='utf-8')
