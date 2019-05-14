from settings import db
from datetime import datetime
from flask_login import UserMixin

from passlib.apps import custom_app_context as pwd_context
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import config


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(32))
    password = db.Column(db.String(128))
    register_date = db.Column(db.DateTime)
    email = db.Column(db.String(32))
    phone = db.Column(db.String(32))
    is_admin = db.Column(db.Boolean)

    def __init__(self, username):
        self.username = username
        self.register_date = datetime.utcnow()
        self.is_admin = False

    def hash_password(self, password):
        self.password = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password)

    def admin(self):
        return self.is_admin

    # default expiration 3600s = 1 hour
    def generate_auth_token(self, expiration=3600 * 7):
        s = Serializer(config.SECRET_KEY, expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(config.SECRET_KEY)
        try:
            data = s.loads(token)
        # except SignatureExpired:
        #     return None  # valid token, but expired
        # except BadSignature:
        #     return None  # invalid token
        except Exception:
            return None
        user = User.query.get(data['id'])
        return user

    def __repr__(self):
        return 'User name=%s' % self.username


def import_user():
    for i in range(1000, 3000, 3):
        user = User('jobs' + str(i) + '@gmail.com')
        user.hash_password('1')
        user.email = 'jobs' + str(i) + '@gmail.com'
        user.phone = '1786678' + str(i)
        db.session.add(user)
    db.session.commit()


if __name__ == '__main__':
    db.drop_all()
    db.create_all()
    db.session.commit()
    import_user()
