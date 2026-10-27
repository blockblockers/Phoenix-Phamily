import unittest
from nfl_enrichment import enrich, norm, to_markdown

class Tests(unittest.TestCase):
    def test_name(self):
        self.assertEqual(norm('James Cook III'), norm('James Cook'))
    def test_boxscore_matching_and_week(self):
        report={'league':'Phoenix Phamily','year':2026,'week':6,'owners':[{'id':1,'name':'Test Team'}],
                'current_week':{'matchups':[{'home_id':1,'away_id':2,'home_lineup':[{'name':'James Cook III','position':'RB','slot':'RB','points':24.3,'pro_team':'BUF'}], 'away_lineup':[]}]}}
        calls=[]
        def fake(path, params):
            calls.append((path,params))
            if path=='/scoreboard':
                return {'events':[{'id':'123','date':'2026-10-11T17:00Z','status':{'type':{'completed':True}},'competitions':[{'competitors':[{'team':{'displayName':'Buffalo Bills'}}]}]}]}
            return {'boxscore':{'players':[{'team':{'abbreviation':'BUF'},'statistics':[{'name':'rushing','labels':['CAR','YDS','TD'],'athletes':[{'athlete':{'displayName':'James Cook'},'stats':['18','103','2']}]}]}]}}
        context=enrich(report,fake)
        self.assertEqual(calls[0][1]['week'],6)
        self.assertEqual(context['players'][0]['stats']['YDS'],'103')
        self.assertIn('https://www.espn.com/nfl/boxscore/_/gameId/123',to_markdown(report,context))
        self.assertFalse(context['news_verified'])
if __name__=='__main__': unittest.main()
