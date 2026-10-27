import os
"""Infer stable identities from ESPN owner IDs; avoid guesses based on team ID/name."""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path('legacy')

def owner_tokens(team):
    tokens = team.get('owner_ids') or []
    return sorted(set(str(x).strip().casefold() for x in tokens if str(x).strip()))

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--archive', default=str(ROOT / 'archive.json'))
    p.add_argument('--output', default=str(ROOT / 'identities.json'))
    p.add_argument('--review', default=str(ROOT / 'identity_review.json'))
    args = p.parse_args()
    archive = json.loads(Path(args.archive).read_text(encoding='utf-8'))
    old = json.loads(Path(args.output).read_text(encoding='utf-8')) if Path(args.output).exists() else {}
    old_seasons = old.get('seasons', {})
    old_franchises = old.get('franchises', {})
    entries = [(str(s['year']), t) for s in archive.get('seasons', []) for t in s.get('teams', [])]
    entries += [(os.getenv('RECAP_SEASON', '2026'), t) for t in archive.get('current_teams', [])]
    owner_to_entries = defaultdict(list)
    review = {'unresolved': [], 'multiple_owners': [], 'conflicts': [], 'summary': {}}
    for year, t in entries:
        toks = owner_tokens(t)
        if len(toks) == 1:
            owner_to_entries[toks[0]].append((year, t))
        elif len(toks) > 1:
            review['multiple_owners'].append({'year': year, 'team_id': t['team_id'], 'name': t['name'], 'owner_ids': toks})
        else:
            review['unresolved'].append({'year': year, 'team_id': t['team_id'], 'name': t['name'], 'reason': 'ESPN owner ID missing'})
    seasons = {str(y): dict(m) for y, m in old_seasons.items()}
    franchises = dict(old_franchises)
    for owner, group in sorted(owner_to_entries.items()):
        # Never override manually assigned mappings or merge conflicting established franchises.
        existing = {old_seasons.get(year, {}).get(str(t['team_id'])) for year, t in group}
        existing.discard(None)
        if len(existing) > 1:
            review['conflicts'].append({'owner_id': owner, 'existing_franchises': sorted(existing), 'entries': [{'year': y, 'team_id': t['team_id']} for y, t in group]})
            continue
        slug = re.sub(r'[^a-z0-9]+', '-', owner).strip('-')[:55]
        fid = next(iter(existing)) if existing else f'espn-owner-{slug}'
        franchises.setdefault(fid, {'label': group[-1][1]['name'], 'owner_id': owner, 'source': 'ESPN account handle (review continuity)' if owner.startswith('handle:') else 'ESPN stable owner ID'})
        for year, t in group:
            tid = str(t['team_id'])
            prior = seasons.setdefault(year, {}).get(tid)
            if prior and prior != fid:
                review['conflicts'].append({'year': year, 'team_id': tid, 'manual_franchise': prior, 'suggested_franchise': fid})
                continue
            seasons[year][tid] = fid
    result = {'franchises': franchises, 'seasons': dict(sorted(seasons.items()))}
    review['summary'] = {'season_team_entries': len(entries), 'mapped_entries': sum(len(v) for v in seasons.values()), 'franchises': len(franchises), 'unresolved': len(review['unresolved']), 'multiple_owner_entries': len(review['multiple_owners']), 'conflicts': len(review['conflicts'])}
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    Path(args.review).write_text(json.dumps(review, indent=2) + '\n', encoding='utf-8')
    print('Identity inference:', review['summary'])

if __name__ == '__main__':
    main()
