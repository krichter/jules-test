from app import db
from datetime import datetime

class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    category = db.Column(db.String(128), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default='USD') # Assuming USD as default
    description = db.Column(db.Text, nullable=True)
    receipt_filename = db.Column(db.String(256), nullable=True) # Stores path or filename of the uploaded receipt
    report_id = db.Column(db.Integer, db.ForeignKey('expense_reports.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Expense {self.category} - {self.amount}>'
