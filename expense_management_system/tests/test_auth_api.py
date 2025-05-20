import json
import pytest
from app.models.user import User
from app.models.role import Role # Ensure Role is importable and created by fixtures
from app import db

def test_register_user(test_client, init_database): # init_database for clean state
    # Ensure 'employee' role exists from conftest
    response = test_client.post('/auth/register', json={
        'username': 'newuser',
        'email': 'new@example.com',
        'password': 'password123'
    })
    assert response.status_code == 201
    assert response.json['message'] == 'User registered successfully'
    
    user = User.query.filter_by(username='newuser').first()
    assert user is not None
    assert user.email == 'new@example.com'
    assert user.role.name == 'employee'

def test_register_user_missing_fields(test_client, init_database):
    response = test_client.post('/auth/register', json={
        'username': 'missingemail'
        # Missing email and password
    })
    assert response.status_code == 400
    assert 'Missing username, email, or password' in response.json['message']

def test_register_user_duplicate_username(test_client, new_user): # new_user fixture creates 'testuser'
    response = test_client.post('/auth/register', json={
        'username': 'testuser', # This username already exists from new_user fixture
        'email': 'another@example.com',
        'password': 'password123'
    })
    assert response.status_code == 400
    assert response.json['message'] == 'Username already exists'

def test_login_user(test_client, new_user): # new_user fixture creates 'testuser' with 'password123'
    response = test_client.post('/auth/login', json={
        'username': 'testuser',
        'password': 'password123'
    })
    assert response.status_code == 200
    assert 'token' in response.json

def test_login_user_invalid_credentials(test_client, new_user):
    response = test_client.post('/auth/login', json={
        'username': 'testuser',
        'password': 'wrongpassword'
    })
    assert response.status_code == 401
    assert response.json['message'] == 'Invalid username or password'
    
def test_login_user_not_exist(test_client, init_database):
    response = test_client.post('/auth/login', json={
        'username': 'nonexistentuser',
        'password': 'password'
    })
    assert response.status_code == 401
    assert response.json['message'] == 'Invalid username or password'
