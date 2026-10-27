"""Run one or all configured leagues with isolated outputs and historical files."""
import argparse,json,os,subprocess,sys,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def configs():
    for p in sorted((ROOT/'leagues').glob('*/league.json')):
        d=json.loads(p.read_text(encoding='utf-8')); yield p.parent,d

def validate(d):
    if not isinstance(d.get('espn_league_id'),int) or d['espn_league_id']<=0: raise ValueError('Invalid ESPN league ID')
    if not isinstance(d.get('season'),int): raise ValueError('Invalid season')
    if not isinstance(d.get('scoring',{}).get('top_half_bonus_win'),bool): raise ValueError('Specify boolean top_half_bonus_win')
    if not d.get('league_name'): raise ValueError('Missing league_name')
    if not isinstance(d.get('archive_start_year',2013),int) or not 2000 <= d.get('archive_start_year',2013) < d['season']: raise ValueError('Invalid archive_start_year')
    if not isinstance(d.get('team_name_aliases',{}),dict): raise ValueError('team_name_aliases must be a dictionary')

def run_one(folder,d,args):
    validate(d)
    env=os.environ.copy();env.update(RECAP_LEAGUE_ID=str(d['espn_league_id']),RECAP_SEASON=str(d['season']),RECAP_LEAGUE_NAME=d['league_name'],RECAP_TOP_HALF_BONUS=str(d['scoring']['top_half_bonus_win']).lower(),RECAP_ARCHIVE_START_YEAR=str(d.get('archive_start_year',2013)))
    if not env.get('ESPN_S2') or not env.get('ESPN_SWID'): raise RuntimeError('Set ESPN_S2 and ESPN_SWID as GitHub Secrets')
    if args.mode=='weekly':
        cmd=[sys.executable,str(ROOT/'collector.py')]+(['--week',str(args.week)] if args.week else [])
        subprocess.run(cmd,cwd=folder,env=env,check=True)
        shutil.copy2(folder/"league.json",folder/"reports"/"league.json")
        shutil.copy2(ROOT/"recap_instructions.md",folder/"reports"/"recap_instructions.md")
        # NFL enrichment is best-effort, not a condition of fantasy score success.
        result=subprocess.run([sys.executable,str(ROOT/'nfl_enrichment.py'),'--latest'],cwd=folder,env=env)
        if result.returncode: print('WARNING: NFL enrichment failed for',d['league_name'],file=sys.stderr)
    else:
        through=args.through if args.through else d['season']-1
        subprocess.run([sys.executable,str(ROOT/'build_legacy.py'),'--through',str(through),'--from-year',str(d.get('archive_start_year',2013))],cwd=folder,env=env,check=True)
        subprocess.run([sys.executable,str(ROOT/'infer_identities.py')],cwd=folder,env=env,check=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['weekly','archive'],default='weekly');ap.add_argument('--league',default='all');ap.add_argument('--week',type=int);ap.add_argument('--through',type=int);args=ap.parse_args()
    selected=[(p,d) for p,d in configs() if d.get('enabled') and (args.league=='all' or d['slug']==args.league)]
    if not selected: ap.error('No enabled matching league found')
    failed=[]
    for folder,d in selected:
        print('\n===',d['league_name'],'===',flush=True)
        try:run_one(folder,d,args)
        except Exception as exc:failed.append((d['league_name'],str(exc)));print('ERROR:',d['league_name'],exc,file=sys.stderr)
    if failed:raise SystemExit(f'{len(failed)} league(s) failed: '+', '.join(x[0] for x in failed))
if __name__=='__main__':main()
