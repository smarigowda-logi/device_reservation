import jwt
import redis
import rq
from time import time
from app import db, login
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import UniqueConstraint
from flask_login import UserMixin
from datetime import datetime
from hashlib import md5
from app.search import add_to_index, remove_from_index, query_index

Session = sessionmaker(bind=db)


class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        return cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(when, value=cls.id)), total

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)


db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    reserve = db.relationship('Reservation', backref='reserve_user', lazy='dynamic')
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    administrator = db.Column(db.String(32))

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'],
            algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Reservation(db.Model):
    __searchable__ = ['body']
    id = db.Column(db.Integer, primary_key=True)
    env = db.Column(db.String(250))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    duration = db.Column(db.Integer)
    platform = db.Column(db.String(64))
    r_user = db.Column(db.String(64))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    __table_args__ = (UniqueConstraint('r_user', 'env', name='unique_agent_user'),
                      )

    def __repr__(self):
        return '<Reservation {}>'.format(self.timestamp)


class Agentprofile(db.Model):
    __searchable__ = ['body']
    id = db.Column(db.Integer, primary_key=True)
    a_name = db.Column(db.String(64), unique=True)
    a_platform = db.Column(db.String(64))
    a_user = db.Column(db.String(64))
    a_pass = db.Column(db.String(64))
    a_serial = db.Column(db.String(64))
    a_access = db.Column(db.String(64))
    a_env = db.Column(db.String(250))
    a_ipaddr = db.Column(db.String(32))
    a_location = db.Column(db.String(64))
    a_command_line = db.Column(db.String(32))
    a_duration = db.Column(db.Integer)
    a_owner = db.Column(db.String(64))
    a_last_reserved = db.Column(db.String(64))
    a_status = db.Column(db.String(64))

    def __repr__(self):
        return '<Agent {}>'.format(self.a_name)


class Rigdescriptor(db.Model):
    __searchable__ = ['body']
    id = db.Column(db.Integer, primary_key=True)
    rig = db.Column(db.String(64), unique=True)
    rig_desc = db.Column(db.String(128))

    def __repr__(self):
        return '<Rig {}>'.format(self.rig)


class History(db.Model):
    __searchable__ = ['body']
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(64))
    platform = db.Column(db.String(64))
    agent = db.Column(db.String(64))
    env = db.Column(db.String(128))
    duration = db.Column(db.Integer)
    reserved_time = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<history {}>'.format(self.agent)
