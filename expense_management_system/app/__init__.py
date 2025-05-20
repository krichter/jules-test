from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    # Import models here to ensure they are registered with SQLAlchemy
    from app.models.role import Role
    from app.models.user import User
    from app.models.expense_report import ExpenseReport
    from app.models.expense import Expense

    # Register blueprints here
    from app.routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # Placeholder for other blueprints
    from app.routes.reports import bp as reports_bp
    app.register_blueprint(reports_bp, url_prefix='/reports')
    
    from app.routes.approvals import bp as approvals_bp # New import
    app.register_blueprint(approvals_bp, url_prefix='/approvals') # New registration

    return app
