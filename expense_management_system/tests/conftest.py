import pytest
from app import create_app, db
from config import TestConfig
from app.models.role import Role
from app.models.user import User

@pytest.fixture(scope='session')
def test_app():
    app = create_app(TestConfig)
    app_context = app.app_context()
    app_context.push()
    db.create_all()

    # Pre-populate roles for tests
    admin_role = Role(name='admin')
    manager_role = Role(name='manager')
    employee_role = Role(name='employee')
    db.session.add_all([admin_role, manager_role, employee_role])
    db.session.commit()

    yield app # provide the app first
    
    db.session.remove()
    db.drop_all()
    app_context.pop()


@pytest.fixture(scope='session')
def test_client(test_app):
    return test_app.test_client()

@pytest.fixture(scope='function') # Use function scope for db to reset between tests
def init_database(test_app): # test_app fixture ensures db is created
    yield db # use the db session from app fixture

    # Clean up database tables after each test
    # This is a simple approach; for more complex scenarios, consider transaction rollbacks
    # or more specific cleaning strategies.
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        if table.name != 'roles': # Don't delete roles table data as it's session-scoped
             db.session.execute(table.delete())
    db.session.commit()


@pytest.fixture(scope='function')
def new_user(init_database): # Depends on init_database to ensure clean state
    employee_role = Role.query.filter_by(name='employee').first()
    user = User(username='testuser', email='test@example.com', role=employee_role)
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user
    
@pytest.fixture(scope='function')
def new_manager(init_database):
    manager_role = Role.query.filter_by(name='manager').first()
    user = User(username='testmanager', email='manager@example.com', role=manager_role)
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user
