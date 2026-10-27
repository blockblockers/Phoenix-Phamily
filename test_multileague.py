import json,unittest
from pathlib import Path
from unittest.mock import patch
import collector
import run_leagues
class MultiLeagueTests(unittest.TestCase):
 def test_two_configs(self):
  a=list(run_leagues.configs());self.assertEqual(len(a),2)
  self.assertEqual([x[1]['slug'] for x in a if x[1]['enabled']],['phoenix-phamily'])
 def test_configs_valid(self):
  for p,d in run_leagues.configs():run_leagues.validate(d)
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
