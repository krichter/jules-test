from app.models.user import User
from app.models.role import Role
from app.models.expense_report import ExpenseReport
from app.models.expense import Expense
from app import db # Import db instance
import pytest

def test_new_user(new_user): # Uses the new_user fixture
    assert new_user.username == 'testuser'
    assert new_user.email == 'test@example.com'
    assert new_user.check_password('password123')
    assert not new_user.check_password('wrongpassword')
    assert new_user.role is not None
    assert new_user.role.name == 'employee'

def test_new_role(test_client, init_database): # test_client ensures app context, init_database ensures clean db
    role = Role.query.filter_by(name='employee').first()
    assert role is not None
    assert role.name == 'employee'

def test_expense_report_creation(new_user, init_database):
    report = ExpenseReport(title="Test Report", description="My test report", author=new_user)
    db.session.add(report)
    db.session.commit()
    assert report.id is not None
    assert report.title == "Test Report"
    assert report.author == new_user
    assert report.status == 'draft'

def test_expense_creation(new_user, init_database):
    report = ExpenseReport(title="Report For Expenses", author=new_user)
    db.session.add(report)
    db.session.commit()

    expense = Expense(category="Travel", amount=100.50, currency="USD", report_id=report.id)
    db.session.add(expense)
    db.session.commit()
    assert expense.id is not None
    assert expense.category == "Travel"
    assert expense.amount == 100.50
    assert expense.report_id == report.id
    assert report.expenses.count() == 1
    assert report.expenses.first().category == "Travel"
