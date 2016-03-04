from utils.DBManager import getConn, putConn
from store.BangumiStore import BangumiStore
from feed.FeedFromDMHY import FeedFromDMHY

class Scheduler:

    def scan_bangumi(self):
        conn = getConn()
        cur = conn.cursor()

        cur.execute('select * from bangumi where status != %s and rss is not null')
        bgm_list = []
        column_definition = [desc[0] for desc in cur.description]
        for record in cur:
            bgm = {}
            for index, column in enumerate(column_definition):
                bgm[column] = record[index]

            bgm_list.append(bgm)

        putConn(conn)

        for bgm in bgm_list:
            bangumi = BangumiStore(bgm)
            pending_episodes = bangumi.get_pending_episodes()
            task = FeedFromDMHY(bangumi, pending_episodes)

            task.parse_feed()

