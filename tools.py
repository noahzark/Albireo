import argparse
from utils.SessionManager import SessionManager
from werkzeug.security import generate_password_hash
from domain.Bangumi import Bangumi
from domain.Episode import Episode
from domain.InviteCode import InviteCode
from domain.TorrentFile import TorrentFile
from domain.User import User
from domain.base import Base

parser = argparse.ArgumentParser(description='Tools for management database')
group = parser.add_mutually_exclusive_group()
group.add_argument('--invite', type=int, metavar=('NUMBER'), help='generate n invite codes')
group.add_argument('--user-add', nargs=2, metavar=('USERNAME', 'PASSWORD'), help='add an user')
group.add_argument('--user-del', nargs=1, metavar=('USERNAME'), help='delete an user')
group.add_argument('--user-promote', nargs=2, metavar=('USERNAME', 'LEVEL'), help='promote an user')
group.add_argument('--db-init', action='store_true', help='init database, if tables not exists, create it')

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
    print('table initialized')

else:
    parser.print_help()
