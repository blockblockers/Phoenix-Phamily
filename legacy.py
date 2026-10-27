"""Opt-in, conservative league legacy archive and current-week rivalry snippets."""
import json
from collections import defaultdict
from pathlib import Path

START_YEAR = 2013
ARCHIVE = Path('legacy/archive.json')
IDENTITIES = Path('legacy/identities.json')


def read_json(path, default):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default


def franchise_key(year, team_id, identities):
    # Explicit season-to-franchise mapping ONLY; no unsafe inference from reused IDs.
    return identities.get('seasons', {}).get(str(year), {}).get(str(team_id))


def build_archive(league_factory, end_year=2025):
    identities = read_json(IDENTITIES, {'franchises': {}, 'seasons': {}})
    archive = {'schema': 1, 'start_year': START_YEAR, 'end_year': end_year,
               'seasons': [], 'warnings': [], 'identity_policy': 'explicit season+team mapping only'}
    for year in range(START_YEAR, end_year + 1):
        try:
            league = league_factory(year)
            season = {'year': year, 'teams': [], 'matchups': [], 'errors': []}
            teams = {int(t.team_id): t for t in league.teams}
            for tid, t in teams.items():
                season['teams'].append({'team_id': tid, 'name': t.team_name,
                    'franchise_id': franchise_key(year, tid, identities)})
            # Historical box-score support varies by season/API. Try each regular-season week;
            # failed weeks are recorded, never fabricated or treated as a complete record.
            max_week = int(getattr(league.settings, 'reg_season_count', 14) or 14)
            for week in range(1, max_week + 1):
                try:
                    boxes = league.box_scores(week=week)
                    for box in boxes:
                        h, a = box.home_team, box.away_team
                        if not h or not a or h.team_id == a.team_id:
                            continue
                        hs, ass = float(box.home_score), float(box.away_score)
                        if hs == 0 and ass == 0:
                            continue  # missing/incomplete historical score
                        record = {'week': week, 'home_id': int(h.team_id), 'away_id': int(a.team_id),
                                  'home_score': round(hs, 2), 'away_score': round(ass, 2)}
                        for side in ('home', 'away'):
                            lineup = getattr(box, f'{side}_lineup', None) or []
                            record[f'{side}_stars'] = sorted([
                                {'name': p.name, 'points': round(float(p.points), 2)}
                                for p in lineup if getattr(p, 'points', None) is not None
                                and str(getattr(p, 'slot_position', '')).upper() not in ('BE', 'IR')
                            ], key=lambda p: -p['points'])[:3]
                        season['matchups'].append(record)
                except Exception as exc:
                    season['errors'].append({'week': week, 'error': str(exc)[:240]})
            archive['seasons'].append(season)
            print(f'{year}: {len(teams)} teams, {len(season["matchups"])} matchups, {len(season["errors"])} missing weeks')
        except Exception as exc:
            archive['warnings'].append({'year': year, 'error': str(exc)[:240]})
            print(f'{year}: unavailable ({exc})')
    ARCHIVE.parent.mkdir(exist_ok=True)
    ARCHIVE.write_text(json.dumps(archive, indent=2), encoding='utf-8')
    return archive


def rivalry_notes(current_week, year=2026):
    if not ARCHIVE.exists():
        return [], 'Legacy archive not installed; run legacy workflow and commit archive.'
    archive = read_json(ARCHIVE, {})
    identities = read_json(IDENTITIES, {})
    notes = []
    for matchup in current_week['matchups']:
        left = franchise_key(year, matchup['home_id'], identities)
        right = franchise_key(year, matchup['away_id'], identities)
        if not left or not right or left == right:
            continue
        games = []
        for season in archive.get('seasons', []):
            yr = season['year']
            for game in season.get('matchups', []):
                a = franchise_key(yr, game['home_id'], identities)
                b = franchise_key(yr, game['away_id'], identities)
                if {a, b} == {left, right}:
                    games.append((yr, game, a, b))
        if not games:
            continue
        games.sort(key=lambda x: (x[0], x[1]['week']))
        wins = defaultdict(int)
        for yr, g, a, b in games:
            if g['home_score'] > g['away_score']: wins[a] += 1
            elif g['away_score'] > g['home_score']: wins[b] += 1
        yr, g, a, b = min(games, key=lambda x: abs(x[1]['home_score']-x[1]['away_score']))
        notes.append({'franchises': [left, right], 'recorded_meetings': len(games),
            'recorded_wins': {left: wins[left], right: wins[right]},
            'closest_recorded_game': {'year': yr, **g},
            'coverage_warning': 'Only successfully fetched regular-season games with explicitly mapped franchise identities; not necessarily lifetime record.'})
    return notes, None
