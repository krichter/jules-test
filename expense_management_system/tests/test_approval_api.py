import json
import pytest
from app.models.expense_report import ExpenseReport
from app.models.user import User
from app.models.expense import Expense
from app import db
from datetime import datetime, timedelta
from decimal import Decimal

# Helper function to get token
def get_auth_token(test_client, username, password='password123'):
    response = test_client.post('/auth/login', json={'username': username, 'password': password})
    assert response.status_code == 200
    return response.json['token']

@pytest.fixture
def manager_auth_headers(test_client, new_manager): # new_manager fixture from conftest
    token = get_auth_token(test_client, new_manager.username)
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def employee_auth_headers(test_client, new_user): # new_user fixture from conftest
    token = get_auth_token(test_client, new_user.username)
    return {'Authorization': f'Bearer {token}'}
    
@pytest.fixture
def submitted_report_by_employee(new_user, init_database):
    report = ExpenseReport(
        title="Employee Submitted Report", 
        user_id=new_user.id, 
        status='submitted',
        submitted_at=datetime.utcnow()
    )
    # Add an expense to make it a valid submittable report
    expense = Expense(report=report, category="Travel", amount=Decimal("100.00"), date=datetime.utcnow())
    db.session.add_all([report, expense])
    db.session.commit()
    return report

@pytest.fixture
def draft_report_by_employee(new_user, init_database):
    report = ExpenseReport(
        title="Employee Draft Report", 
        user_id=new_user.id, 
        status='draft'
    )
    db.session.add(report)
    db.session.commit()
    return report

def test_list_pending_reports_as_manager(test_client, manager_auth_headers, submitted_report_by_employee, new_manager):
    # Ensure the submitted report is not by the manager themselves
    assert submitted_report_by_employee.user_id != new_manager.id

    response = test_client.get('/approvals/pending', headers=manager_auth_headers)
    assert response.status_code == 200
    assert len(response.json['pending_reports']) >= 1 # Can be more if other tests created some
    
    found = False
    for rep in response.json['pending_reports']:
        if rep['id'] == submitted_report_by_employee.id:
            found = True
            assert rep['author_username'] == submitted_report_by_employee.author.username
            assert rep['total_amount'] == "100.00" # Sum of expenses
            break
    assert found, "Submitted report not found in pending list for manager"

def test_list_pending_reports_as_employee_fails(test_client, employee_auth_headers, submitted_report_by_employee):
    response = test_client.get('/approvals/pending', headers=employee_auth_headers)
    assert response.status_code == 403 # Access denied due to role

def test_approve_report_as_manager(test_client, manager_auth_headers, submitted_report_by_employee):
    report_id = submitted_report_by_employee.id
    response = test_client.post(f'/approvals/reports/{report_id}/approve', headers=manager_auth_headers)
    assert response.status_code == 200
    assert response.json['message'] == f'Report ID {report_id} approved successfully'
    
    approved_report = ExpenseReport.query.get(report_id)
    assert approved_report.status == 'approved'

def test_approve_report_not_submitted_fails(test_client, manager_auth_headers, draft_report_by_employee):
    report_id = draft_report_by_employee.id
    response = test_client.post(f'/approvals/reports/{report_id}/approve', headers=manager_auth_headers)
    assert response.status_code == 400
    assert response.json['message'] == 'Report is not in a submitted state for approval'

def test_manager_approve_own_report_fails(test_client, new_manager, manager_auth_headers):
    # Create a report submitted by the manager
    manager_report = ExpenseReport(
        title="Manager's Own Report", 
        user_id=new_manager.id, 
        status='submitted',
        submitted_at=datetime.utcnow()
    )
    expense = Expense(report=manager_report, category="Training", amount=Decimal("200.00"), date=datetime.utcnow())
    db.session.add_all([manager_report, expense])
    db.session.commit()

    report_id = manager_report.id
    response = test_client.post(f'/approvals/reports/{report_id}/approve', headers=manager_auth_headers)
    assert response.status_code == 403
    assert response.json['message'] == 'Managers cannot approve their own reports through this endpoint'


def test_reject_report_as_manager(test_client, manager_auth_headers, submitted_report_by_employee):
    report_id = submitted_report_by_employee.id
    response = test_client.post(f'/approvals/reports/{report_id}/reject', json={'reason': 'Out of policy'}, headers=manager_auth_headers)
    assert response.status_code == 200
    assert response.json['message'] == f'Report ID {report_id} rejected successfully'
    assert response.json['reason'] == 'Out of policy'
    
    rejected_report = ExpenseReport.query.get(report_id)
    assert rejected_report.status == 'rejected'
    # If a 'rejection_reason' field were added to the model, test for it here.

def test_reject_report_not_submitted_fails(test_client, manager_auth_headers, draft_report_by_employee):
    report_id = draft_report_by_employee.id
    response = test_client.post(f'/approvals/reports/{report_id}/reject', json={'reason': 'Test'}, headers=manager_auth_headers)
    assert response.status_code == 400
    assert response.json['message'] == 'Report is not in a submitted state for rejection'

def test_approve_report_as_employee_fails(test_client, employee_auth_headers, submitted_report_by_employee):
    report_id = submitted_report_by_employee.id
    response = test_client.post(f'/approvals/reports/{report_id}/approve', headers=employee_auth_headers)
    assert response.status_code == 403 # Access denied due to role
    
    report = ExpenseReport.query.get(report_id) # Ensure status didn't change
    assert report.status == 'submitted'

def test_reject_report_as_employee_fails(test_client, employee_auth_headers, submitted_report_by_employee):
    report_id = submitted_report_by_employee.id
    response = test_client.post(f'/approvals/reports/{report_id}/reject', headers=employee_auth_headers)
    assert response.status_code == 403 # Access denied due to role

    report = ExpenseReport.query.get(report_id) # Ensure status didn't change
    assert report.status == 'submitted'
