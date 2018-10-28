import itertools
import logging
import math
import time

import numpy as np
import pandas as pd

import config
from db import Database, QUERY

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class Stats():
    def __init__(self):
        self.update()

    def update(self):
        start = time.time()

        with Database() as db:
            data = db.execute(QUERY).fetchall()
            prs = pd.DataFrame(data)

        logging.info(f'SQL fetched in {time.time()-start:.3f} secs ({len(prs)} round players)')

        n = config.N

        start = time.time()
        self.df = prs.groupby(['steamId', 'lastTeam']).tail(n)
        self.df = self.df.groupby(['steamId', 'lastTeam']).agg(
            {'wins': ['sum'], 'losses': ['sum'], 'hiveSkill': ['last'], 'playerName': ['first']})

        n_x = self.df[('wins', 'sum')] + self.df[('losses', 'sum')]
        self.df['winrate'] = self.df[('wins', 'sum')] / n_x
        self.df['P_X'] = (n_x / n) ** 3

        # Final multiplier of hive skill per team
        self.df['M_X'] = (self.df['winrate'] * 2 * self.df['P_X'] + (1 - self.df['P_X']))

        # Get the proportion of games played per team, of last n_weight matches.
        # This is used for shuffle purposes to avoid putting the same players in a same team a lot.
        n_weight = config.N_WEIGHT
        self.df_weight = prs.groupby(['steamId']).tail(n_weight)
        self.df_weight = self.df_weight.groupby(['steamId', 'lastTeam']).agg({'lastTeam': ['count']})
        self.df_weight['p'] = self.df_weight[('lastTeam', 'count')] / n_weight

        self.df['p'] = self.df_weight['p']
        self.df['p'] = self.df['p'].fillna(0)

        logging.info(f'Hive per team updated in {(time.time()-start)*1000:.0f} ms ({len(self.df)} unique players)')


stats = Stats()


class Player():
    def __init__(self, ns2id, hiveskill):
        self.ns2id = ns2id
        self.hs = hiveskill

        try:
            self.name = str(stats.df.loc[ns2id][('playerName', 'first')][1])
        except:
            self.name = '<New Player>'
            self.marine_hs = self.hs
            self.alien_hs = self.hs
            self.marine_p = 0
            self.alien_p = 0
        else:
            try:
                self.marine_hs = float(self.hs * stats.df.loc[ns2id]['M_X'][1])
            except:
                self.marine_hs = self.hs

            try:
                self.alien_hs = float(self.hs * stats.df.loc[ns2id]['M_X'][2])
            except:
                self.alien_hs = self.hs

            try:
                self.marine_p = float(stats.df.loc[ns2id]['p'][1])
            except:
                self.marine_p = 0

            try:
                self.alien_p = float(stats.df.loc[ns2id]['p'][2])
            except:
                self.alien_p = 0

    @property
    def json(self):
        response = {'ns2id': self.ns2id, 'marine_skill': self.marine_hs, 'alien_skill': self.alien_hs}

        return response

    def __eq__(self, other):
        return self.ns2id == other.ns2id

    def __repr__(self):
        return '<Player {} - H:{:.2f} M:{:.2f} A:{:.2f}>'.format(self.name, self.hs, self.marine_hs, self.alien_hs)


class TeamComp():
    def __init__(self, team1, team2):
        self.marine_players = team1
        self.alien_players = team2

        self.marines_hs = [p.marine_hs for p in self.marine_players]
        self.aliens_hs = [p.alien_hs for p in self.alien_players]

        self.marines_avg = np.mean(self.marines_hs)
        self.aliens_avg = np.mean(self.aliens_hs)
        self.delta_avg = abs(self.marines_avg - self.aliens_avg)

        self.marines_std = np.std(self.marines_hs)
        self.aliens_std = np.std(self.aliens_hs)
        self.delta_std = abs(self.marines_std - self.aliens_std)

        # Team comp score for the combination (less is better).
        self.score = (self.delta_avg ** 2 + self.delta_std ** 2) ** 0.5

        # Player team repeat score for the combination (less is better).
        self.score_tr = sum([p.marine_p for p in self.marine_players]) + sum([p.alien_p for p in self.alien_players])

    def __eq__(self, other):
        for m in other.marine_players:
            if m not in self.marine_players:
                return False

        for a in other.alien_players:
            if a not in self.alien_players:
                return False

        return True

    def __repr__(self):
        return f'<TeamComp {len(self.marine_players)}v{len(self.alien_players)}' \
               f' - M:{self.marines_avg:.2f} A:{self.aliens_avg:.2f}' \
               f' (Score: {self.score:.2f}, RScore: {self.score_tr:.2f})>'


class Shuffle():
    def __init__(self, ns2ids, hiveskills):
        logging.info(f'Requested shuffle with {len(ns2ids)} players.')

        stats.update()

        if len(ns2ids) >= 2:
            self.ns2ids = ns2ids
            self.players = [Player(x, hiveskills[i]) for i, x in enumerate(ns2ids)]

            self.shuffle()

    def shuffle(self):
        start = time.time()
        team_size = int(math.floor(len(self.players) / 2))
        group_combs = list(itertools.combinations(self.players, team_size))

        matchups = []

        for team in group_combs:
            t1, t2 = team, []

            for player in self.players:
                if player not in t1:
                    t2.append(player)

            for team_pairs in [[t1, t2], [t2, t1]]:
                matchups.append(TeamComp(*team_pairs))

        matchups_score_cutoff = [m for m in matchups if m.score < config.SCORE_CUTOFF]

        self.best = min(matchups_score_cutoff, key=lambda x: x.score_tr)

        logging.info(f'Done with {len(matchups)} possible combinations in {time.time() - start:.3f} secs')
        logging.info(f'Best combination: {self.best}')

    @property
    def json(self):
        response = {
            'team1': [p.ns2id for p in self.best.marine_players],
            'team2': [p.ns2id for p in self.best.alien_players],
            'diagnostics': {
                'Score': self.best.score,
                'RScore': self.best.score_tr
            }}

        return response


Shuffle([1291449, 3869225, 34583831, 41727273, 44513487, 44618947, 54888603, 55422011, 57378783, 79089452, 81009203,
         98383317, 139217532, 333858003, 356935348, 393094819], [11, 22, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
