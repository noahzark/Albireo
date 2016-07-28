from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import scoped_session, sessionmaker
from yaml import load


class SessionManager:

    __fr = open('./config/config.yml', 'r')
    __config = load(__fr)

    __dbConfig = __config['database']
    # dsn = ' '.join('%s=%s' % (k,v) for k,v in dbConfig.items())

    __engine_url = URL('postgresql', **__dbConfig)
    engine = create_engine(__engine_url, client_encoding='utf8')
    __session_factory = sessionmaker(bind=engine)

    Session = scoped_session(__session_factory)

