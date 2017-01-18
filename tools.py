import argparse
from utils.SessionManager import SessionManager
from werkzeug.security import generate_password_hash
from domain.Bangumi import Bangumi
from domain.Episode import Episode
from domain.InviteCode import InviteCode
from domain.TorrentFile import TorrentFile
from domain.User import User
from domain.base import Base
from domain.Feed import Feed
from domain.Favorites import Favorites
from domain.ServerSession import ServerSession
from domain.WatchProgress import WatchProgress

from utils.http import FileDownloader
import yaml, os, errno, re
from urlparse import urlparse
from alembic import command
from alembic.config import Config
from StringIO import StringIO

parser = argparse.ArgumentParser(description='Tools for management database')
group = parser.add_mutually_exclusive_group()
group.add_argument('--invite', type=int, metavar=('NUMBER'), help='generate n invite codes')
group.add_argument('--user-add', nargs=2, metavar=('USERNAME', 'PASSWORD'), help='add an user')
group.add_argument('--user-del', nargs=1, metavar=('USERNAME'), help='delete an user')
group.add_argument('--user-promote', nargs=2, metavar=('USERNAME', 'LEVEL'), help='promote an user')
group.add_argument('--db-init', action='store_true', help='init database, if tables not exists, create it')
group.add_argument('--cover', action='store_true', help='scan bangumi, download missing cover')
group.add_argument('--bgm-reset', nargs=1, metavar=('BANGUMI_ID'), help='clear a bangumi\'s related table records')

args = parser.parse_args()

if args.invite is not None:
    session = SessionManager.Session()
    invite_code_list = []
    for i in range(args.invite):
        invite_code = InviteCode()
        invite_code_list.append(invite_code)
        session.add(invite_code)

    session.commit()

    for invite_code in invite_code_list:
        print(invite_code.code)

    SessionManager.Session.remove()

elif args.user_add is not None:
    session = SessionManager.Session()
    username = args.user_add[0]
    password = args.user_add[1]
    user = User(name=username, password=generate_password_hash(password), level=User.LEVEL_DEFAULT)
    session.add(user)
    session.commit()
    print('Successfully create user, id is %s' % user.id)
    SessionManager.Session.remove()

elif args.user_del is not None:
    session = SessionManager.Session()
    username = args.user_del[0]
    session.query(User).filter(User.name==username).delete()
    session.commit()
    print('Delete successfully')
    SessionManager.Session.remove()

elif args.user_promote is not None:
    session = SessionManager.Session()
    username = args.user_promote[0]
    level = int(args.user_promote[1])
    user = session.query(User).filter(User.name==username).one()
    user.level = level
    session.commit()
    print('Update successfully')
    SessionManager.Session.remove()

elif args.db_init:
    Base.metadata.create_all(SessionManager.engine)
    fp = StringIO()
    alembic_config = Config('./alembic.ini', stdout=fp)
    command.heads(alembic_config)
    content = fp.getvalue()
    fp.close()
    revision_hash = re.search('^([0-9a-f]+)\s\(head\)', content, re.U).group(1)
    print('set current revision {0}'.format(revision_hash))
    new_alembic_config = Config('./alembic.ini')
    command.stamp(new_alembic_config, revision=revision_hash)
    print('Database initialized')

elif args.cover:
    fr = open('./config/config.yml', 'r')
    config = yaml.load(fr)
    download_location = config['download']['location']
    session = SessionManager.Session()
    cur = session.query(Bangumi)
    resp_cookies = None
    file_downloader = FileDownloader()
    for bangumi in cur:
        if bangumi.image is not None:
            try:
                bangumi_dir = download_location + '/' + str(bangumi.id)
                # if bangumi folder is not existence create it
                if not os.path.exists(bangumi_dir):
                    os.makedirs(bangumi_dir)
                    print 'bangumi %s folder created' % (str(bangumi.id),)

                path = urlparse(bangumi.image).path
                extname = os.path.splitext(path)[1]
                bangumi_cover_path = bangumi_dir + '/cover' + extname
                if not os.path.exists(bangumi_cover_path):
                    # download bangumi image
                    print 'start to download bangumi cover of %s (%s)' % (bangumi.name, str(bangumi.id))
                    file_downloader.download_file(bangumi.image, bangumi_cover_path)
            except OSError as exception:
                if exception.errno == errno.EACCES:
                    # permission denied
                    raise exception
                else:
                    print exception
elif args.bgm_reset:
    session = SessionManager.Session()
    bangumi_id = args.bgm_reset[0]
    feed_list = session.query(Feed).filter(Feed.bangumi_id == bangumi_id).all()
    episode_list = session.query(Episode).filter(Episode.bangumi_id == bangumi_id).all()
    for feed in feed_list:
        if feed.torrent_file_id is not None:
            session.query(TorrentFile).filter(TorrentFile.id == feed.torrent_file_id).delete()
        session.delete(feed)

    for episode in episode_list:
        episode.status = Episode.STATUS_NOT_DOWNLOADED
    session.commit()
    print('cleared')
    SessionManager.Session.remove()



else:
    parser.print_help()
