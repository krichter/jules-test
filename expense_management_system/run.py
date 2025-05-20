from app import create_app, db
from app.models.user import User # Import User or any other model
from app.models.role import Role # Import Role
from app.models.expense_report import ExpenseReport
from app.models.expense import Expense


app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Role': Role, 'ExpenseReport': ExpenseReport, 'Expense': Expense}

if __name__ == '__main__':
    app.run()
