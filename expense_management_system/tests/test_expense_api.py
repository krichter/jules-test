import json
import pytest
from app.models.expense_report import ExpenseReport
from app.models.expense import Expense
from app import db
from datetime import datetime, timedelta
from decimal import Decimal

# Helper function to get token (can be moved to a common test utility if used widely)
def get_auth_token(test_client, username='testuser', password='password123'):
    response = test_client.post('/auth/login', json={'username': username, 'password': password})
    assert response.status_code == 200
    return response.json['token']

@pytest.fixture
def auth_headers(test_client, new_user): # new_user fixture from conftest
    token = get_auth_token(test_client, new_user.username, 'password123')
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def report_for_expenses(new_user, init_database):
    # Create a report to which expenses can be added
    report = ExpenseReport(title="Report for Expense API Tests", user_id=new_user.id, status='draft')
    db.session.add(report)
    db.session.commit()
    return report

@pytest.fixture
def existing_expense(report_for_expenses, init_database):
    expense = Expense(
        report_id=report_for_expenses.id,
        date=datetime.utcnow() - timedelta(days=1),
        category="Office Supplies",
        amount=Decimal("50.00"),
        currency="USD",
        description="Pens and paper"
    )
    db.session.add(expense)
    db.session.commit()
    return expense

def test_add_expense_to_report(test_client, auth_headers, report_for_expenses):
    report_id = report_for_expenses.id
    response = test_client.post(f'/reports/{report_id}/expenses', json={
        'date': '2023-10-26',
        'category': 'Meals',
        'amount': '75.50',
        'currency': 'USD',
        'description': 'Client lunch'
    }, headers=auth_headers)
    
    assert response.status_code == 201
    assert response.json['message'] == 'Expense added to report'
    assert 'expense_id' in response.json
    
    expense = Expense.query.get(response.json['expense_id'])
    assert expense is not None
    assert expense.category == 'Meals'
    assert expense.amount == Decimal("75.50")
    assert expense.report_id == report_id
    
    # Check if parent report's updated_at was modified
    updated_report = ExpenseReport.query.get(report_id)
    assert updated_report.updated_at > report_for_expenses.updated_at # Assuming time moves forward

def test_add_expense_invalid_amount(test_client, auth_headers, report_for_expenses):
    report_id = report_for_expenses.id
    response = test_client.post(f'/reports/{report_id}/expenses', json={
        'date': '2023-10-26',
        'category': 'Meals',
        'amount': 'invalid-amount', # Invalid amount
        'currency': 'USD'
    }, headers=auth_headers)
    assert response.status_code == 400
    assert response.json['message'] == 'Invalid amount format'

def test_add_expense_to_submitted_report_fails(test_client, auth_headers, report_for_expenses):
    report_for_expenses.status = 'submitted' # Change status
    db.session.commit()
    report_id = report_for_expenses.id
    
    response = test_client.post(f'/reports/{report_id}/expenses', json={
        'date': '2023-10-27', 'category': 'Travel', 'amount': '100'
    }, headers=auth_headers)
    assert response.status_code == 400
    assert response.json['message'] == 'Expenses can only be added to draft reports'

def test_list_expenses_for_report(test_client, auth_headers, report_for_expenses, existing_expense):
    report_id = report_for_expenses.id
    response = test_client.get(f'/reports/{report_id}/expenses', headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json['expenses']) == 1
    assert response.json['expenses'][0]['id'] == existing_expense.id
    assert response.json['expenses'][0]['category'] == existing_expense.category

def test_get_expense_details(test_client, auth_headers, report_for_expenses, existing_expense):
    report_id = report_for_expenses.id
    expense_id = existing_expense.id
    response = test_client.get(f'/reports/{report_id}/expenses/{expense_id}', headers=auth_headers)
    assert response.status_code == 200
    assert response.json['id'] == expense_id
    assert response.json['category'] == "Office Supplies"
    assert Decimal(response.json['amount']) == Decimal("50.00")

def test_get_expense_from_wrong_report_fails(test_client, auth_headers, report_for_expenses, existing_expense, new_user):
    # Create another report
    other_report = ExpenseReport(title="Other Report", user_id=new_user.id, status='draft')
    db.session.add(other_report)
    db.session.commit()
    
    expense_id = existing_expense.id # This expense belongs to report_for_expenses
    
    response = test_client.get(f'/reports/{other_report.id}/expenses/{expense_id}', headers=auth_headers)
    assert response.status_code == 404 # Expense not found in this report

def test_update_expense_in_report(test_client, auth_headers, report_for_expenses, existing_expense):
    report_id = report_for_expenses.id
    expense_id = existing_expense.id
    
    response = test_client.put(f'/reports/{report_id}/expenses/{expense_id}', json={
        'category': 'Updated Category',
        'amount': '55.25',
        'description': 'Updated item'
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json['message'] == 'Expense updated successfully'
    
    updated_expense = Expense.query.get(expense_id)
    assert updated_expense.category == 'Updated Category'
    assert updated_expense.amount == Decimal("55.25")
    assert updated_expense.description == 'Updated item'

def test_update_expense_in_submitted_report_fails(test_client, auth_headers, report_for_expenses, existing_expense):
    report_for_expenses.status = 'submitted'
    db.session.commit()
    report_id = report_for_expenses.id
    expense_id = existing_expense.id
    
    response = test_client.put(f'/reports/{report_id}/expenses/{expense_id}', json={
        'category': 'Trying to update'
    }, headers=auth_headers)
    assert response.status_code == 400
    assert response.json['message'] == 'Expenses can only be updated in draft reports'

def test_delete_expense_from_report(test_client, auth_headers, report_for_expenses, existing_expense):
    report_id = report_for_expenses.id
    expense_id = existing_expense.id
    
    response = test_client.delete(f'/reports/{report_id}/expenses/{expense_id}', headers=auth_headers)
    assert response.status_code == 200
    assert response.json['message'] == 'Expense deleted successfully'
    assert Expense.query.get(expense_id) is None

def test_delete_expense_from_submitted_report_fails(test_client, auth_headers, report_for_expenses, existing_expense):
    report_for_expenses.status = 'submitted'
    db.session.commit()
    report_id = report_for_expenses.id
    expense_id = existing_expense.id
    
    response = test_client.delete(f'/reports/{report_id}/expenses/{expense_id}', headers=auth_headers)
    assert response.status_code == 400
    assert response.json['message'] == 'Expenses can only be deleted from draft reports'
