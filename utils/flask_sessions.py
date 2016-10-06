import pickle
from uuid import uuid4
from werkzeug.datastructures import CallbackDict
from flask.sessions import SessionInterface, SessionMixin
from itsdangerous import want_bytes, Signer, BadSignature

from utils.SessionManager import SessionManager
from domain.ServerSession import ServerSession
from datetime import datetime, timedelta

class PgSession(CallbackDict, SessionMixin):

    def __init__(self, initial=None, sid=None, new=False, permanent=None):
        def on_update(self):
            self.modified = True
        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        self.new = new
        self.modified = False
        if permanent:
            self.permanent = permanent

class PgSessionInterface(SessionInterface):
    serializer = pickle
    session_class = PgSession

    def _generate_sid(self):
        return str(uuid4())

    def _get_signer(self, app):
        if not app.secret_key:
            return None
        return Signer(app.secret_key, salt='flask-session', key_derivation='hmac')

    def open_session(self, app, request):
        sid = request.cookies.get(app.session_cookie_name)
        if not sid:
            sid = self._generate_sid()
            return self.session_class(sid=sid, permanent=True)

        signer = self._get_signer(app)
        if signer is None:
            return None
        try:
            sid_as_bytes = signer.unsign(sid)
            sid = sid_as_bytes.decode()
        except BadSignature:
            sid = self._generate_sid()
            return self.session_class(sid=sid, permanent=True)

        db_session = SessionManager.Session()
        saved_session = db_session.query(ServerSession).filter(ServerSession.session_id == sid).first()
        if saved_session and not saved_session.expiry and saved_session.expiry <= datetime.utcnow():
            # delete expired session
            db_session.delete(saved_session)
            db_session.commit()
            saved_session = None

        if saved_session:
            try:
                val = saved_session.data
                data = self.serializer.loads(want_bytes(val))
                return self.session_class(data, sid=sid)
            except:
                return self.session_class(sid=sid, permanent=True)

        return self.session_class(sid=sid, permanent=True)

    def save_session(self, app, session, response):
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        sid = session.sid

        db_session = SessionManager.Session()

        saved_session = db_session.query(ServerSession).filter(ServerSession.session_id == sid).first()

        if not session:
            if session.modified:
                if saved_session:
                    db_session.delete(saved_session)
                    db_session.commit()
                response.delete_cookie(app.session_cookie.name, domain=domain, path=path)

            return

        httponly = self.get_cookie_httponly(app)
        secure = self.get_cookie_secure(app)
        expires = self.get_expiration_time(app, session)
        # expires = datetime.utcnow() + timedelta(minutes=1)
        # if expires is None:
        #     expires = datetime.utcnow() + timedelta(days=1)
        val = self.serializer.dumps(dict(session))
        if saved_session:
            saved_session.data = val
            saved_session.expiry = expires
            db_session.commit()
        else:
            new_session = ServerSession(session_id=sid, data=val, expiry=expires)
            db_session.add(new_session)
            db_session.commit()

        session_id = self._get_signer(app).sign(want_bytes(session.sid))

        response.set_cookie(app.session_cookie_name,
                            session_id,
                            expires=expires,
                            httponly=httponly,
                            domain=domain,
                            path=path,
                            secure=secure)
