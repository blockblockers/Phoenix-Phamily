import json,unittest,sys,types
try:
 import espn_api.football
except ImportError:
 mock_espn=types.ModuleType("espn_api")
 mock_football=types.ModuleType("espn_api.football")
 mock_football.League=object
 mock_espn.football=mock_football
 sys.modules["espn_api"]=mock_espn
 sys.modules["espn_api.football"]=mock_football
from pathlib import Path
from unittest.mock import patch
import collector
import run_leagues
from team_names import canonical_team_name, team_key
class MultiLeagueTests(unittest.TestCase):
 def test_two_configs(self):
  a=list(run_leagues.configs());self.assertEqual(len(a),4)
  self.assertEqual([x[1]['slug'] for x in a if x[1]['enabled']],['phoenix-phamily'])
 def test_configs_valid(self):
  for p,d in run_leagues.configs():run_leagues.validate(d)
 def test_team_normalization(self):
  config=json.loads((run_leagues.ROOT/'leagues/phoenix-phamily/league.json').read_text())
  self.assertEqual(canonical_team_name('TD  Law  firm Jackson, McConkey',config['team_name_aliases'],config['recap']['team_personalities']),'TD Law Firm Jackson, McConkey')
  self.assertEqual(team_key('  Rice  and  Shine '),team_key('rice and shine'))
 def test_bonus_toggle(self):
  class Team:
   def __init__(self,i):self.team_id=i
  class Box:
   home_team=Team(1);away_team=Team(2);home_score=100;away_score=90;home_lineup=[];away_lineup=[]
  class League:
   def box_scores(self,week):return [Box()]
  with patch.object(collector,'BONUS_ENABLED',False):
   result=collector.weekly(League(),1,{1:'A',2:'B'});self.assertEqual(sum(x['bonus_win'] for x in result['scoring_ranks']),0)
  with patch.object(collector,'BONUS_ENABLED',True):
   result=collector.weekly(League(),1,{1:'A',2:'B'});self.assertEqual(sum(x['bonus_win'] for x in result['scoring_ranks']),1)
if __name__=='__main__':unittest.main()
