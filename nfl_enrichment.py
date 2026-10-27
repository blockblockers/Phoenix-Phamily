"""Public ESPN NFL box-score enrichment for a completed fantasy week.

Run after collector.py. Does not require ESPN login or touch legacy files.
Uses season/week from the generated report, NOT the current calendar week.
Only reports actual box-score stats, with ESPN game URLs and dates; no inferred injuries.
"""
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = 'https://site.api.espn.com/apis/site/v2/sports/football/nfl'


def fetch(path, params=None):
    url = BASE + path + ('?' + urlencode(params) if params else '')
    with urlopen(Request(url, headers={'User-Agent': 'PhoenixPhamilyRecap/3.2 (boxscore research)'}), timeout=18) as resp:
        return json.load(resp)


def norm(name):
    name = str(name or '').casefold()
    name = re.sub(r'\b(jr|sr|ii|iii|iv|v)\b', '', name)
    return re.sub(r'[^a-z0-9]', '', name)


def get_players(report):
    players = {}
    for matchup in report['current_week']['matchups']:
        for side in ('home', 'away'):
            team_id = matchup[f'{side}_id']
            for player in matchup.get(f'{side}_lineup', []):
                name = player.get('name')
                if name and player.get('position') != 'D/ST':
                    key = norm(name)
                    players.setdefault(key, []).append({'name': name, 'fantasy_team_id': team_id, 'slot': player.get('slot'), 'fantasy_points': player.get('points'), 'pro_team': player.get('pro_team')})
    return players


def boxscore_entries(summary):
    """Yield athlete stat rows with category, stat labels, and game team abbreviation."""
    for team in summary.get('boxscore', {}).get('players', []):
        abbrev = team.get('team', {}).get('abbreviation')
        for group in team.get('statistics', []):
            labels = group.get('labels') or []
            category = group.get('name') or group.get('type') or 'unknown'
            for item in group.get('athletes', []):
                athlete = item.get('athlete') or {}
                stats = item.get('stats') or []
                if athlete.get('displayName') and stats:
                    yield {'name': athlete['displayName'], 'athlete_id': str(athlete.get('id') or ''), 'pro_team': abbrev, 'category': category,
                           'stats': {str(k): str(v) for k, v in zip(labels, stats)}}


def enrich(report, fetcher=fetch):
    year, week = int(report['year']), int(report['week'])
    data = {'schema': 1, 'season': year, 'week': week, 'source': 'ESPN public NFL game box scores', 'generated_utc': datetime.now(timezone.utc).isoformat(),
            'games': [], 'players': [], 'warnings': [], 'news_verified': False}
    try:
        schedule = fetcher('/scoreboard', {'dates': year, 'seasontype': 2, 'week': week, 'limit': 100})
    except Exception as exc:
        data['warnings'].append(f'NFL scoreboard unavailable: {type(exc).__name__}: {exc}')
        return data
    events = schedule.get('events') or []
    if not events:
        data['warnings'].append('No NFL games returned for the fantasy scoring week; no game facts verified.')
        return data
    wanted = get_players(report)
    seen = set()
    for event in events:
        game_id = str(event.get('id') or '')
        if not game_id:
            continue
        competitions = event.get('competitions') or [{}]
        status = event.get('status', {}).get('type', {})
        if not status.get('completed'):
            data['warnings'].append(f'Game {game_id} not final; its statistics were skipped.')
            continue
        date = event.get('date')
        opponents = [c.get('team', {}).get('displayName', '') for c in competitions[0].get('competitors', [])]
        game_url = f'https://www.espn.com/nfl/boxscore/_/gameId/{game_id}'
        data['games'].append({'id': game_id, 'date_utc': date, 'teams': opponents, 'source_url': game_url})
        try:
            summary = fetcher('/summary', {'event': game_id})
        except Exception as exc:
            data['warnings'].append(f'Game {game_id} box score unavailable: {type(exc).__name__}: {exc}')
            continue
        for stat in boxscore_entries(summary):
            key = norm(stat['name'])
            if key not in wanted:
                continue
            for fp in wanted[key]:
                # Reject an ambiguous name if ESPN roster's team contradicts box-score team.
                if fp['pro_team'] and stat['pro_team'] and fp['pro_team'].upper() != stat['pro_team'].upper():
                    continue
                unique = (fp['fantasy_team_id'], key, game_id, stat['category'])
                if unique in seen:
                    continue
                seen.add(unique)
                data['players'].append({**fp, 'nfl_name': stat['name'], 'nfl_team': stat['pro_team'], 'category': stat['category'],
                                        'stats': stat['stats'], 'game_id': game_id, 'game_date_utc': date, 'source_url': game_url})
    if not data['players']:
        data['warnings'].append('No fantasy players matched verified NFL box-score rows; do not invent game-log facts.')
    return data


def to_markdown(report, context):
    lines = [f"# Sourced NFL game logs — {report['league']} Week {report['week']} ({report['year']})", '',
             'These are NFL box-score statistics, NOT fantasy points. Each stat has a dated game source. No injury, snap-count, or transaction claims have been verified.',
             'Only cite a row if the player and game match the fantasy week. If a source is missing, omit the claim.', '']
    by_team = {int(t['id']): t['name'] for t in report.get('owners', [])}
    for team_id, team_name in sorted(by_team.items(), key=lambda x:x[1]):
        rows = [p for p in context['players'] if p['fantasy_team_id'] == team_id]
        if not rows:
            continue
        lines.extend([f'## {team_name}', ''])
        for p in rows:
            stats = ', '.join(f'{k}: {v}' for k,v in p['stats'].items())
            lines.append(f"- **{p['name']}** ({p['slot']}; fantasy {p['fantasy_points']} pts) — {p['category']}: {stats}. Game: {p['game_date_utc']}. [ESPN box score]({p['source_url']})")
        lines.append('')
    lines.extend(['## Coverage and limitations', ''])
    lines.extend('- '+warning for warning in context['warnings'])
    lines.extend(['', f"Completed games found: {len(context['games'])}; matched stat rows: {len(context['players'])}.",
                  'This enrichment is not a news feed. For injuries, trades, and other developments, research dated reporting separately.', ''])
    return '\n'.join(lines)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--report', type=Path)
    ap.add_argument('--latest', action='store_true')
    args=ap.parse_args()
    path=args.report
    if path is None:
        candidates=sorted(Path('reports').glob('week-*.json'))
        if not args.latest or not candidates:
            ap.error('Use --report reports/week-06.json or --latest after running collector.py')
        path=candidates[-1]
    report=json.loads(path.read_text(encoding='utf-8'))
    context=enrich(report)
    stem=path.with_suffix('')
    stem.with_name(stem.name+'-nfl-context').with_suffix('.json').write_text(json.dumps(context, indent=2), encoding='utf-8')
    stem.with_name(stem.name+'-nfl-context').with_suffix('.md').write_text(to_markdown(report, context), encoding='utf-8')
    print(f"NFL enrichment: {len(context['games'])} games, {len(context['players'])} player-category rows, {len(context['warnings'])} warnings")

if __name__=='__main__':
    main()
