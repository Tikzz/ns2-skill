import config

if config.DATABASE == 'SQLITE':
    import sqlite3

    DB = config.SQLITE_FILE


    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d


    class Database():
        def __init__(self):
            self.db = DB

        def __enter__(self):
            self.conn = sqlite3.connect(self.db)
            self.conn.row_factory = dict_factory
            return self.conn.cursor()

        def __exit__(self, type, value, traceback):
            self.conn.commit()
            self.conn.close()


    QUERY = 'select prs.roundId, prs.steamId, ps.hiveSkill, prs.playerName, prs.lastTeam, ' \
            'CASE WHEN prs.lastTeam=winningTeam THEN 1 ELSE 0 END as wins, ' \
            'CASE WHEN prs.lastTeam=winningTeam THEN 0 ELSE 1 END as losses ' \
            'from PlayerRoundStats prs inner join RoundInfo ri on ri.roundId = prs.roundId ' \
            'inner join PlayerStats ps on ps.steamId = prs.steamId'
if config.DATABASE == 'MYSQL':
    import pymysql.cursors


    class Database():
        def __enter__(self):
            self.conn = pymysql.connect(host=config.MYSQL_HOST, user=config.MYSQL_USER, password=config.MYSQL_PASS,
                                        db=config.MYSQL_DB)
            self.cursor = self.conn.cursor()
            return self

        def execute(self, query):
            class Wrapper():
                def __init__(self, cursor, query):
                    self.cursor = cursor
                    self.cursor.execute(query)

                def fetchall(self):
                    columns = [col[0] for col in self.cursor.description]
                    return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

            return Wrapper(self.cursor, query)

        def __exit__(self, type, value, traceback):
            self.conn.close()


    QUERY = 'select prs.roundId, prs.steamId, ps.hiveSkill, prs.playerName, prs.lastTeam, ' \
            'if(prs.lastTeam=winningTeam,1,0) wins, if(prs.lastTeam=winningTeam,0,1) losses from PlayerRoundStats prs' \
            ' inner join RoundInfo ri on ri.roundId = prs.roundId inner join PlayerStats ps on ps.steamId = prs.steamId'
