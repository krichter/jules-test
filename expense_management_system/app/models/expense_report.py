from app import db
from datetime import datetime

class ExpenseReport(db.Model):
    __tablename__ = 'expense_reports'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(64), default='draft', nullable=False) # draft, submitted, approved, rejected, reimbursed
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at = db.Column(db.DateTime, nullable=True)
    
    expenses = db.relationship('Expense', backref='report', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<ExpenseReport {self.title}>'
