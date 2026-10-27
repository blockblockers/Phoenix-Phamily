"""One-time/on-demand ESPN historical archive rebuild; never runs in weekly collection."""
import os
import argparse
from espn_api.football import League
from legacy import build_archive

p = argparse.ArgumentParser()
p.add_argument('--through', type=int, default=2025)
a = p.parse_args()
if not 2013 <= a.through <= 2025:
    p.error('--through must be between 2013 and 2025')
s2, swid = os.getenv('ESPN_S2'), os.getenv('ESPN_SWID')
if not s2 or not swid:
    p.error('ESPN_S2 and ESPN_SWID environment variables required')
build_archive(lambda year: League(league_id=1106154, year=year, espn_s2=s2, swid=swid), a.through)
