import argparse
from utils.SessionManager import SessionManager
from domain.InviteCode import InviteCode

parser = argparse.ArgumentParser(description='Tools for management database')
parser.add_argument('--invite', type=int)

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