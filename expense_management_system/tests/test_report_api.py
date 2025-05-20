import json
import pytest
from app.models.expense_report import ExpenseReport
from app.models.expense import Expense
from app import db
from datetime import datetime, timedelta
from decimal import Decimal

# Helper function to get token
def get_auth_token(test_client, username='testuser', password='password123'):
    response = test_client.post('/auth/login', json={'username': username, 'password': password})
    assert response.status_code == 200
    return response.json['token']

@pytest.fixture
def auth_headers(test_client, new_user): # new_user ensures 'testuser' is created
    token = get_auth_token(test_client)
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def new_report(new_user, init_database, auth_headers, test_client):
    # Create a report directly for testing specific GET/PUT/DELETE
    # For POST, we will use the endpoint
    report = ExpenseReport(title="Initial Report", user_id=new_user.id)
    db.session.add(report)
    db.session.commit()
    return report

def test_create_report(test_client, auth_headers, new_user): # new_user for user_id context
    response = test_client.post('/reports', json={
        'title': 'My First Report',
        'description': 'Expenses from the conference'
    }, headers=auth_headers)
    assert response.status_code == 201
    assert response.json['message'] == 'Expense report created'
    assert 'report_id' in response.json
    report = ExpenseReport.query.get(response.json['report_id'])
    assert report is not None
    assert report.title == 'My First Report'
    assert report.user_id == new_user.id

def test_list_reports(test_client, auth_headers, new_user, new_report): # new_report creates one report
    response = test_client.get('/reports', headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json['reports']) == 1
    assert response.json['reports'][0]['title'] == new_report.title

def test_get_report_details(test_client, auth_headers, new_report):
    response = test_client.get(f'/reports/{new_report.id}', headers=auth_headers)
    assert response.status_code == 200
    assert response.json['title'] == new_report.title
    assert response.json['id'] == new_report.id

def test_get_report_unauthorized_different_user(test_client, new_manager, new_report):
    # new_report is owned by 'testuser' (new_user fixture)
    # new_manager logs in as 'testmanager'
    manager_token = get_auth_token(test_client, 'testmanager', 'password123')
    manager_headers = {'Authorization': f'Bearer {manager_token}'}
    
    response = test_client.get(f'/reports/{new_report.id}', headers=manager_headers)
    assert response.status_code == 403 # Access denied

def test_update_report(test_client, auth_headers, new_report):
    response = test_client.put(f'/reports/{new_report.id}', json={
        'title': 'Updated Report Title',
        'description': 'Updated description'
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json['message'] == 'Report updated successfully'
    updated_report = ExpenseReport.query.get(new_report.id)
    assert updated_report.title == 'Updated Report Title'

def test_delete_report(test_client, auth_headers, new_report):
    report_id = new_report.id
    response = test_client.delete(f'/reports/{report_id}', headers=auth_headers)
    assert response.status_code == 200
    assert response.json['message'] == 'Report deleted successfully'
    assert ExpenseReport.query.get(report_id) is None

def test_submit_report_no_expenses(test_client, auth_headers, new_report):
    response = test_client.post(f'/reports/{new_report.id}/submit', headers=auth_headers)
    assert response.status_code == 400
    assert response.json['message'] == 'Cannot submit an empty report. Add at least one expense.'

def test_submit_report_with_expenses(test_client, auth_headers, new_report):
    # Add an expense first
    expense = Expense(report_id=new_report.id, category="Food", amount=Decimal("25.00"), date=datetime.utcnow())
    db.session.add(expense)
    db.session.commit()

    response = test_client.post(f'/reports/{new_report.id}/submit', headers=auth_headers)
    assert response.status_code == 200
    assert response.json['message'] == 'Report submitted successfully'
    submitted_report = ExpenseReport.query.get(new_report.id)
    assert submitted_report.status == 'submitted'
    assert submitted_report.submitted_at is not None

def test_update_submitted_report_fails(test_client, auth_headers, new_report):
    # Add an expense and submit the report
    expense = Expense(report_id=new_report.id, category="Food", amount=Decimal("25.00"), date=datetime.utcnow())
    db.session.add(expense)
    new_report.status = 'submitted'
    new_report.submitted_at = datetime.utcnow()
    db.session.commit()

    response = test_client.put(f'/reports/{new_report.id}', json={
        'title': 'Trying to update submitted'
    }, headers=auth_headers)
    assert response.status_code == 400
    assert response.json['message'] == 'Only draft reports can be updated'

def test_delete_submitted_report_fails(test_client, auth_headers, new_report):
    # Add an expense and submit the report
    expense = Expense(report_id=new_report.id, category="Food", amount=Decimal("25.00"), date=datetime.utcnow())
    db.session.add(expense)
    new_report.status = 'submitted'
    new_report.submitted_at = datetime.utcnow()
    db.session.commit()

    response = test_client.delete(f'/reports/{new_report.id}', headers=auth_headers)
    assert response.status_code == 400
    assert response.json['message'] == 'Only draft reports can be deleted'
