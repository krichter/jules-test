from app import db
from datetime import datetime
# It's good practice to handle password hashing in the model or a service
from passlib.hash import pbkdf2_sha256 as sha256

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    expense_reports = db.relationship('ExpenseReport', backref='author', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = sha256.hash(password)

    def check_password(self, password):
        return sha256.verify(password, self.password_hash)

    def __repr__(self):
        return f'<User {self.username}>'
