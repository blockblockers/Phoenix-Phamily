"""Phoenix Phamily v3: private ESPN league, historical results, owner reference, recap brief."""
import argparse
import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from espn_api.football import League
from legacy import rivalry_notes
from team_names import canonical_team_name

LEAGUE_ID = int(os.getenv("RECAP_LEAGUE_ID", "1106154"))
YEAR = int(os.getenv("RECAP_SEASON", "2026"))
LEAGUE_NAME = os.getenv("RECAP_LEAGUE_NAME", "Phoenix Phamily")
BONUS_ENABLED = os.getenv("RECAP_TOP_HALF_BONUS", "true").lower() == "true"
EXCLUDED = {'BE', 'IR'}


def num(v):
    try:
        return round(float(v), 2)
    except (ValueError, TypeError):
        return None


def clean_human_name(first=None, last=None, display=None):
    """Prefer verified ESPN first/last; reject handles, emails and generated names."""
    import re
    first, last = str(first or '').strip(), str(last or '').strip()
    name = ' '.join(x for x in (first, last) if x)
    if not name:
        name = str(display or '').strip()
    if not name or '@' in name or any(ch.isdigit() for ch in name):
        return None
    if re.search(r'(?i)(espnfan|^fan\b|^user\b|^team\b)', name):
        return None
    if not re.fullmatch(r"[\w .'-]+", name, re.UNICODE):
        return None
    # A single ESPN display name is often a handle, not a real name.
    if not first and not last and len(name.split()) < 2:
        return None
    return name[:80]


def member_directory(league):
    """Use authenticated ESPN mTeam member records when exposed by espn_api."""
    members = {}
    response = None
    try:
        response = league.espn_request.get_league(views=['mTeam'])
    except (AttributeError, TypeError, ValueError, KeyError) as exc:
        print('Member directory unavailable:', type(exc).__name__)
    except Exception as exc:
        print('Member directory request failed:', type(exc).__name__)
    if isinstance(response, list):
        response = response[0] if response else {}
    if isinstance(response, dict):
        for member in response.get('members', []):
            if not isinstance(member, dict):
                continue
            name = clean_human_name(member.get('firstName'), member.get('lastName'), member.get('displayName'))
            if name and member.get('id'):
                members[str(member['id']).strip().casefold()] = name
    return members


def owner_name(team, members):
    owners = getattr(team, 'owners', None) or getattr(team, 'owner', None) or []
    if not isinstance(owners, (list, tuple)):
        owners = [owners]
    names = []
    for owner in owners:
        if isinstance(owner, dict):
            owner_id = owner.get('id') or owner.get('ownerId') or owner.get('userId')
            name = members.get(str(owner_id).strip().casefold()) if owner_id else None
            name = name or clean_human_name(owner.get('firstName'), owner.get('lastName'), owner.get('displayName'))
        else:
            owner_id = getattr(owner, 'id', None) or getattr(owner, 'ownerId', None)
            name = members.get(str(owner_id).strip().casefold()) if owner_id else None
            name = name or clean_human_name(getattr(owner, 'firstName', None), getattr(owner, 'lastName', None))
        if name and name not in names:
            names.append(name)
    return ', '.join(names) if names else None


def player(p):
    return dict(name=getattr(p, 'name', 'Unknown'), position=getattr(p, 'position', None),
                pro_team=getattr(p, 'proTeam', None), points=num(getattr(p, 'points', None)),
                projected_points=num(getattr(p, 'projected_points', None)),
                slot=str(getattr(p, 'slot_position', '') or ''))


def weekly(league, week, team_names):
    boxes = league.box_scores(week=week)
    if not boxes:
        raise ValueError(f'No box scores for week {week}')
    scores, matchups = {}, []
    for box in boxes:
        h, a = box.home_team, box.away_team
        if not h or not a:
            raise ValueError(f'Week {week}: incomplete matchup')
        hid, aid = int(h.team_id), int(a.team_id)
        hs, aps = num(box.home_score), num(box.away_score)
        if hs is None or aps is None:
            raise ValueError(f'Week {week}: missing score')
        scores[hid], scores[aid] = hs, aps
        matchups.append(dict(home_id=hid, away_id=aid, home_score=hs, away_score=aps,
                             home_lineup=[player(p) for p in (box.home_lineup or [])],
                             away_lineup=[player(p) for p in (box.away_lineup or [])]))
    if set(scores) != set(team_names):
        raise ValueError(f'Week {week}: incomplete teams: {len(scores)}/{len(team_names)}')
    ranks = sorted(scores, key=lambda i: (-scores[i], team_names[i]))
    half = len(ranks) // 2
    if len(ranks) % 2 or (BONUS_ENABLED and scores[ranks[half-1]] == scores[ranks[half]]):
        raise ValueError(f'Week {week}: odd team count or bonus cutoff tie requires manual review')
    bonus = set(ranks[:half]) if BONUS_ENABLED else set()
    wins = {i: 0 for i in scores}
    ties = {i: 0 for i in scores}
    for m in matchups:
        h, a = m['home_id'], m['away_id']
        if m['home_score'] > m['away_score']:
            wins[h] += 1
        elif m['away_score'] > m['home_score']:
            wins[a] += 1
        else:
            ties[h] += 1; ties[a] += 1
    ranks_out = [dict(id=i, name=team_names[i], points=scores[i], scoring_rank=rank,
                      bonus_win=int(i in bonus), head_to_head_win=wins[i],
                      head_to_head_tie=ties[i], weekly_wins=wins[i]+int(i in bonus))
                 for rank, i in enumerate(ranks, 1)]
    return dict(week=week, scoring_ranks=ranks_out, matchups=matchups)


def load_overrides(path):
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding='utf-8'))
    return {int(k): str(v).strip() for k, v in raw.items() if str(v).strip()}


def summarize(weeks, teams):
    totals = {i: dict(id=i, team=teams[i]['name'], owner=teams[i]['owner'],
                      h2h_wins=0, h2h_losses=0, h2h_ties=0, bonus_wins=0,
                      total_wins=0, points_for=0., points_against=0., recent_wins=[]) for i in teams}
    for w in weeks:
        scores = {r['id']: r for r in w['scoring_ranks']}
        for i, r in scores.items():
            t = totals[i]
            t['points_for'] += r['points']
            t['h2h_wins'] += r['head_to_head_win']
            t['h2h_ties'] += r['head_to_head_tie']
            t['bonus_wins'] += r['bonus_win']
            t['total_wins'] += r['weekly_wins']
            t['recent_wins'].append(r['weekly_wins'])
        for m in w['matchups']:
            h, a = totals[m['home_id']], totals[m['away_id']]
            h['points_against'] += m['away_score']
            a['points_against'] += m['home_score']
            if m['home_score'] > m['away_score']:
                a['h2h_losses'] += 1
            elif m['away_score'] > m['home_score']:
                h['h2h_losses'] += 1
    for t in totals.values():
        t['points_for'] = round(t['points_for'], 2)
        t['points_against'] = round(t['points_against'], 2)
        t['average_points'] = round(t['points_for']/len(weeks), 2)
        t['last_three_weekly_wins'] = sum(t.pop('recent_wins')[-3:])
    return sorted(totals.values(), key=lambda t: (-t['total_wins'], -t['points_for'], t['team']))


def highlights(week, teams):
    results = []
    for m in week['matchups']:
        winner_id = m['home_id'] if m['home_score'] > m['away_score'] else m['away_id'] if m['away_score'] > m['home_score'] else None
        item = dict(winner=teams[winner_id]['name'] if winner_id is not None else 'TIE',
                    margin=round(abs(m['home_score']-m['away_score']), 2), teams=[])
        for side in ('home', 'away'):
            i = m[f'{side}_id']
            lineup = m[f'{side}_lineup']
            starters = sorted([p for p in lineup if p['slot'].upper() not in EXCLUDED and p['points'] is not None], key=lambda p: -p['points'])
            bench = sorted([p for p in lineup if p['slot'].upper() == 'BE' and p['points'] is not None], key=lambda p: -p['points'])
            item['teams'].append(dict(id=i, name=teams[i]['name'], owner=teams[i]['owner'], score=m[f'{side}_score'],
                                      top_starters=starters[:5], top_bench=bench[:3],
                                      underperformers=sorted([dict(**p, below_projection=round(p['projected_points']-p['points'], 2)) for p in starters if p['projected_points'] is not None], key=lambda p: -p['below_projection'])[:3]))
        results.append(item)
    return sorted(results, key=lambda x: x['margin'])


def markdown(output):
    w = output['week']; lines = [f'# {output["league"]} — Week {w} recap research brief', '',
       '## Season standings (through this week)', '',
       '| Rank | Team | Owner | H2H W-L-T | Bonus wins | Combined wins | Points for | Avg | Last 3 weeks wins |',
       '|---:|---|---|---|---:|---:|---:|---:|---:|']
    for n, t in enumerate(output['season_standings'], 1):
        lines.append(f"| {n} | {t['team']} | {t['owner'] or 'Not available'} | {t['h2h_wins']}-{t['h2h_losses']}-{t['h2h_ties']} | {t['bonus_wins']} | {t['total_wins']} | {t['points_for']:.2f} | {t['average_points']:.2f} | {t['last_three_weekly_wins']} |")
    lines += ['', '## Weekly scoring ranks (not editorial power rankings)', '', '| Rank | Team | Score | H2H | Bonus | Weekly wins |', '|---:|---|---:|---:|---:|---:|']
    for r in output['current_week']['scoring_ranks']:
        lines.append(f"| {r['scoring_rank']} | {r['name']} | {r['points']:.2f} | {r['head_to_head_win']} | {r['bonus_win']} | {r['weekly_wins']} |")
    lines += ['', '## Matchups and storyline leads', '']
    for m in output['storylines']:
        lines.append(f"### {m['teams'][0]['name']} {m['teams'][0]['score']:.2f} — {m['teams'][1]['name']} {m['teams'][1]['score']:.2f}")
        lines.append(f"Winner: {m['winner']} | Margin: {m['margin']:.2f}")
        for t in m['teams']:
            lines.append(f"- **{t['name']}** (owner: {t['owner'] or 'not available'}): starters: " + ', '.join(f"{p['name']} {p['points']:.2f}" for p in t['top_starters']))
            lines.append('  - Top bench scores (not automatically startable swaps): ' + (', '.join(f"{p['name']} {p['points']:.2f}" for p in t['top_bench']) or 'None'))
            lines.append('  - Below projection: ' + (', '.join(f"{p['name']} {p['below_projection']:.2f} below" for p in t['underperformers'] if p['below_projection'] > 0) or 'None'))
        lines.append('')
    lines += ['## Legacy rivalry callbacks (select 0–2, verified and relevant)', '']
    for r in output.get('legacy_rivalries', []):
        g = r['closest_recorded_game']
        lines.append(f"- {r['current_teams'][0]} vs {r['current_teams'][1]}: {r['recorded_meetings']} recorded meetings; closest {g['year']} W{g['week']}, {g['home_score']:.2f}–{g['away_score']:.2f}. Historical team names: {g['home_team_name']} vs {g['away_team_name']}. Historical stars: " + ', '.join(p['name'] + ' ' + str(p['points']) for p in (g.get('home_stars', []) + g.get('away_stars', []))[:4]))
    if output.get('legacy_warning'):
        lines.append(output['legacy_warning'])
    lines += ['', 'These are archive-covered meetings only, not guaranteed lifetime records. Do not infer historical owner identity without verification.', '']
    lines += ['## News research checklist', '', 'Research verified NFL game reports, injuries, usage and transactions for the exact ESPN scoring week. Include source URLs and dates. Do not claim an injury caused low fantasy points without verification. Never treat a Tuesday report as a Sunday event.', '', '## Recap instructions', '', 'Use `recap_instructions.md` for the fixed ~1,200-word format. Distinguish H2H and bonus wins; standings above are calculated from available weekly results. Do not call weekly scoring ranks editorial power rankings. Do not invent news, injuries, trades, playoff odds, or owner names.', '']
    lines += ['', '## Publication guardrails', '', 'Target 1,150–1,250 words, six matchups, all 12 power rankings. Use **team names** in headlines and prose. Owner real names only when verified; never print ESPN handles, login names, email addresses, member IDs or opaque franchise keys. NFL facts must be verified against dated sources for the scoring week; no news has been fetched by this collector.', '']
    return '\n'.join(lines)


def enrich_rivalry_labels(notes, teams):
    """Add present and historical team names; never publish opaque franchise IDs."""
    from legacy import read_json, IDENTITIES, ARCHIVE
    ids = read_json(IDENTITIES, {})
    archive = read_json(ARCHIVE, {})
    by_year = {int(season['year']): {int(t['team_id']): t['name'].strip() for t in season.get('teams', [])}
               for season in archive.get('seasons', [])}
    reverse = {v: teams[int(tid)]['name'] for tid, v in ids.get('seasons', {}).get(str(YEAR), {}).items()
               if int(tid) in teams}
    out = []
    for note in notes:
        g = note['closest_recorded_game']
        yr = int(g['year'])
        out.append({
            'current_teams': [reverse.get(fid, 'Unknown current team') for fid in note['franchises']],
            'recorded_meetings': note['recorded_meetings'],
            'recorded_wins': {reverse.get(fid, 'Unknown current team'): wins for fid, wins in note['recorded_wins'].items()},
            'closest_recorded_game': {**g, 'home_team_name': by_year.get(yr, {}).get(g['home_id'], 'Unknown historical team'),
                                     'away_team_name': by_year.get(yr, {}).get(g['away_id'], 'Unknown historical team')},
            'coverage_warning': note['coverage_warning']
        })
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--week', type=int, help='Completed week; default last completed ESPN week')
    args = parser.parse_args()
    s2, swid = os.getenv('ESPN_S2'), os.getenv('ESPN_SWID')
    if not s2 or not swid:
        raise SystemExit('Missing ESPN_S2 or ESPN_SWID secrets')
    league = League(league_id=LEAGUE_ID, year=YEAR, espn_s2=s2, swid=swid)
    current = int(league.current_week)
    target = args.week if args.week is not None else current-1
    if not 1 <= target < current:
        raise SystemExit(f'Week {target} not completed according to ESPN (current week {current})')
    overrides = load_overrides(Path('owner_overrides.json'))
    members = member_directory(league)
    config_path = Path('league.json')
    config = json.loads(config_path.read_text(encoding='utf-8')) if config_path.exists() else {}
    recap = config.get('recap', {})
    aliases = config.get('team_name_aliases', {})
    personalities = recap.get('team_personalities', {})
    teams = {int(t.team_id): {'id': int(t.team_id), 'name': canonical_team_name(t.team_name, aliases, personalities),
                              'owner': (clean_human_name(display=overrides.get(int(t.team_id))) if int(t.team_id) in overrides else owner_name(t, members)),
                              'owner_source': 'manual override' if int(t.team_id) in overrides and clean_human_name(display=overrides.get(int(t.team_id))) else 'ESPN verified name' if owner_name(t, members) else 'unavailable'} for t in league.teams}
    weeks = [weekly(league, w, {i: t['name'] for i, t in teams.items()}) for w in range(1, target+1)]
    legacy_notes, legacy_warning = rivalry_notes(weeks[-1], YEAR)
    legacy_notes = enrich_rivalry_labels(legacy_notes, teams)
    output = dict(legacy_rivalries=legacy_notes, legacy_warning=legacy_warning, league=LEAGUE_NAME, league_id=LEAGUE_ID, year=YEAR, week=target,
                  generated_utc=datetime.now(timezone.utc).isoformat(), owners=list(teams.values()),
                  season_standings=summarize(weeks, teams), current_week=weeks[-1],
                  storylines=highlights(weeks[-1], teams), historical_weeks=weeks,
                  notes=['Computed standings from weeks 1 through target; validate against ESPN league rules and score corrections.',
                         'Top bench scores are opportunities to investigate, not proof of legal substitutions.',
                         'Editorial power rankings and NFL news require separate research.',
                         'Top-half bonus enabled: ' + str(BONUS_ENABLED)])
    path = Path('reports'); path.mkdir(exist_ok=True)
    (path/f'week-{target:02d}.json').write_text(json.dumps(output, indent=2), encoding='utf-8')
    (path/f'week-{target:02d}.md').write_text(markdown(output), encoding='utf-8')
    print(f'Created week-{target:02d} JSON and Markdown; {len(teams)} teams, {len(weeks)} weeks, {len(weeks[-1]["matchups"])} matchups')
    missing = [t['name'] for t in teams.values() if not t['owner']]
    if missing:
        print('Owner names unavailable for: ' + ', '.join(missing) + '. Optionally populate owner_overrides.json.')


if __name__ == '__main__':
    main()
