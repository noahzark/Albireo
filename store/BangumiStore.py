from utils.DBManager import getConn, putConn


class BangumiStore:

    STATUS_UNSTARTED = 0
    STATUS_ONAIR = 1
    STATUS_FINISHED = 2

    def __init__(self, bgm_dict):
        for k, v in bgm_dict.items():
            setattr(self, k, v)

    @classmethod
    def fromId(cls, id):
        conn = getConn()
        cur = conn.cursor()
        cur.execute("select * from bangumi where id = %s", (id,))
        result = cur.fetchone()
        column_definition = [desc[0] for desc in cur.description]
        # build data dict from cursor
        bgm_dict = {}
        for index, column in enumerate(column_definition):
            bgm_dict[column] = result[index]

        # return connection to pool
        putConn(conn)

        return cls(bgm_dict)

    @classmethod
    def from_dict(cls, bgm_dict):
        return cls(bgm_dict)

    def save(self):
        conn = getConn()
        cur = conn.cursor()
        try:
            attr_tuples = self.__dict__.items()
            if not hasattr(self, 'id'):
                insert_sql = """insert into bangumi %s
                            values(%s)""" % (
                    ', '.join(k for k, v in attr_tuples),
                    ', '.join('%(' + k +')s' for k, v in attr_tuples))
                cur.execute(insert_sql,
                        self.__dict__)
            else:
                update_sql ="""update bangumi
                                set %s
                                where id = %(id)s""" % (
                    ', '.join(k + ' = %(' + k + ')s' for k, v in attr_tuples)
                )
                cur.execute(update_sql,
                        self.__dict__)
            conn.commit()
        except:
            return False
        finally:
            putConn(conn)

        return True

    def get_pending_episodes(self):
        pass