from flask import Blueprint, request, jsonify, g
from app import db
from app.models.expense_report import ExpenseReport
from app.models.user import User # Though g.current_user is used, having User might be useful for other checks if needed
from app.models.expense import Expense # Add Expense model import
from app.services.auth_decorator import token_required # Import the decorator
from datetime import datetime
from decimal import Decimal # For handling expense amount

bp = Blueprint('reports', __name__)

@bp.route('', methods=['POST'])
@token_required
def create_report():
    data = request.get_json()
    if not data or not data.get('title'):
        return jsonify({'message': 'Title is required'}), 400

    new_report = ExpenseReport(
        title=data['title'],
        description=data.get('description', ''),
        user_id=g.current_user.id, # User ID from token
        status='draft' # Default status
    )
    db.session.add(new_report)
    db.session.commit()
    return jsonify({'message': 'Expense report created', 'report_id': new_report.id}), 201

@bp.route('', methods=['GET'])
@token_required
def list_reports():
    # Only list reports for the current user
    user_reports = ExpenseReport.query.filter_by(user_id=g.current_user.id).order_by(ExpenseReport.created_at.desc()).all()
    output = []
    for report in user_reports:
        output.append({
            'id': report.id,
            'title': report.title,
            'description': report.description,
            'status': report.status,
            'created_at': report.created_at.isoformat() if report.created_at else None,
            'updated_at': report.updated_at.isoformat() if report.updated_at else None,
            'submitted_at': report.submitted_at.isoformat() if report.submitted_at else None
        })
    return jsonify({'reports': output}), 200

@bp.route('/<int:report_id>', methods=['GET'])
@token_required
def get_report(report_id):
    report = ExpenseReport.query.get_or_404(report_id)
    if report.user_id != g.current_user.id:
        # Add role-based access check here if managers/admins can view any report
        # For now, only the owner can view.
        return jsonify({'message': 'Access denied to this report'}), 403
    
    return jsonify({
        'id': report.id,
        'title': report.title,
        'description': report.description,
        'status': report.status,
        'user_id': report.user_id,
        'created_at': report.created_at.isoformat() if report.created_at else None,
        'updated_at': report.updated_at.isoformat() if report.updated_at else None,
        'submitted_at': report.submitted_at.isoformat() if report.submitted_at else None,
        'expenses': [{'id': exp.id, 'date': exp.date.isoformat(), 'category': exp.category, 'amount': str(exp.amount), 'currency': exp.currency, 'description': exp.description} for exp in report.expenses]
    }), 200

@bp.route('/<int:report_id>', methods=['PUT'])
@token_required
def update_report(report_id):
    report = ExpenseReport.query.get_or_404(report_id)
    if report.user_id != g.current_user.id:
        return jsonify({'message': 'Access denied to this report'}), 403
    if report.status != 'draft':
        return jsonify({'message': 'Only draft reports can be updated'}), 400

    data = request.get_json()
    report.title = data.get('title', report.title)
    report.description = data.get('description', report.description)
    report.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'message': 'Report updated successfully'}), 200

@bp.route('/<int:report_id>', methods=['DELETE'])
@token_required
def delete_report(report_id):
    report = ExpenseReport.query.get_or_404(report_id)
    if report.user_id != g.current_user.id:
        return jsonify({'message': 'Access denied to this report'}), 403
    if report.status != 'draft':
        return jsonify({'message': 'Only draft reports can be deleted'}), 400
            
    # Expenses associated with this report are deleted due to cascade="all, delete-orphan"
    # defined in the ExpenseReport model's relationship to Expense.
    db.session.delete(report)
    db.session.commit()
    return jsonify({'message': 'Report deleted successfully'}), 200

@bp.route('/<int:report_id>/submit', methods=['POST'])
@token_required
def submit_report(report_id):
    report = ExpenseReport.query.get_or_404(report_id)
    if report.user_id != g.current_user.id:
        return jsonify({'message': 'Access denied to this report'}), 403
    if report.status != 'draft':
        return jsonify({'message': 'Only draft reports can be submitted'}), 400
    if not report.expenses.first(): # Check if there are any expenses associated
        return jsonify({'message': 'Cannot submit an empty report. Add at least one expense.'}), 400

    report.status = 'submitted'
    report.submitted_at = datetime.utcnow()
    report.updated_at = datetime.utcnow() # Also update the updated_at timestamp
    db.session.commit()
    return jsonify({'message': 'Report submitted successfully'}), 200

# POST /reports/{report_id}/expenses
@bp.route('/<int:report_id>/expenses', methods=['POST'])
@token_required
def add_expense_to_report(report_id):
    report = ExpenseReport.query.get_or_404(report_id)
    if report.user_id != g.current_user.id:
        return jsonify({'message': 'Access denied to report'}), 403
    if report.status != 'draft':
        return jsonify({'message': 'Expenses can only be added to draft reports'}), 400

    data = request.get_json()
    if not data or not data.get('category') or not data.get('amount'):
        return jsonify({'message': 'Missing category or amount for expense'}), 400

    try:
        amount = Decimal(data['amount'])
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except (ValueError, TypeError):
        return jsonify({'message': 'Invalid amount format'}), 400

    new_expense = Expense(
        report_id=report.id,
        date=datetime.strptime(data['date'], '%Y-%m-%d') if data.get('date') else datetime.utcnow(),
        category=data['category'],
        amount=amount,
        currency=data.get('currency', 'USD'),
        description=data.get('description', '')
        # receipt_filename will be handled later if file uploads are implemented
    )
    db.session.add(new_expense)
    report.updated_at = datetime.utcnow() # Update parent report's timestamp
    db.session.commit()
    return jsonify({'message': 'Expense added to report', 'expense_id': new_expense.id}), 201

# GET /reports/{report_id}/expenses
@bp.route('/<int:report_id>/expenses', methods=['GET'])
@token_required
def list_expenses_for_report(report_id):
    report = ExpenseReport.query.get_or_404(report_id)
    if report.user_id != g.current_user.id:
        # Consider if managers/admins should access this
        return jsonify({'message': 'Access denied to report'}), 403

    expenses_output = []
    for exp in report.expenses.order_by(Expense.date.asc()).all(): # Order by date, for example
        expenses_output.append({
            'id': exp.id,
            'date': exp.date.isoformat(),
            'category': exp.category,
            'amount': str(exp.amount), # Convert Decimal to string for JSON
            'currency': exp.currency,
            'description': exp.description,
            'created_at': exp.created_at.isoformat(),
            'updated_at': exp.updated_at.isoformat()
        })
    return jsonify({'expenses': expenses_output}), 200
    
# GET /reports/{report_id}/expenses/{expense_id}
@bp.route('/<int:report_id>/expenses/<int:expense_id>', methods=['GET'])
@token_required
def get_expense_details(report_id, expense_id):
    report = ExpenseReport.query.get_or_404(report_id)
    if report.user_id != g.current_user.id:
        return jsonify({'message': 'Access denied to report'}), 403

    expense = Expense.query.get_or_404(expense_id)
    if expense.report_id != report.id: # Ensure expense belongs to the specified report
        return jsonify({'message': 'Expense not found in this report'}), 404
        
    return jsonify({
        'id': expense.id,
        'date': expense.date.isoformat(),
        'category': expense.category,
        'amount': str(expense.amount),
        'currency': expense.currency,
        'description': expense.description,
        'report_id': expense.report_id,
        'created_at': expense.created_at.isoformat(),
        'updated_at': expense.updated_at.isoformat()
    }), 200

# PUT /reports/{report_id}/expenses/{expense_id}
@bp.route('/<int:report_id>/expenses/<int:expense_id>', methods=['PUT'])
@token_required
def update_expense_in_report(report_id, expense_id):
    report = ExpenseReport.query.get_or_404(report_id)
    if report.user_id != g.current_user.id:
        return jsonify({'message': 'Access denied to report'}), 403
    if report.status != 'draft':
        return jsonify({'message': 'Expenses can only be updated in draft reports'}), 400

    expense = Expense.query.get_or_404(expense_id)
    if expense.report_id != report.id:
        return jsonify({'message': 'Expense not found in this report'}), 404

    data = request.get_json()
    
    if 'date' in data:
        try:
            expense.date = datetime.strptime(data['date'], '%Y-%m-%d')
        except ValueError:
            return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    expense.category = data.get('category', expense.category)
    
    if 'amount' in data:
        try:
            amount = Decimal(data['amount'])
            if amount <= 0:
                raise ValueError("Amount must be positive")
            expense.amount = amount
        except (ValueError, TypeError):
            return jsonify({'message': 'Invalid amount format or value'}), 400
            
    expense.currency = data.get('currency', expense.currency)
    expense.description = data.get('description', expense.description)
    expense.updated_at = datetime.utcnow()
    report.updated_at = datetime.utcnow() # Update parent report's timestamp

    db.session.commit()
    return jsonify({'message': 'Expense updated successfully'}), 200

# DELETE /reports/{report_id}/expenses/{expense_id}
@bp.route('/<int:report_id>/expenses/<int:expense_id>', methods=['DELETE'])
@token_required
def delete_expense_from_report(report_id, expense_id):
    report = ExpenseReport.query.get_or_404(report_id)
    if report.user_id != g.current_user.id:
        return jsonify({'message': 'Access denied to report'}), 403
    if report.status != 'draft':
        return jsonify({'message': 'Expenses can only be deleted from draft reports'}), 400

    expense = Expense.query.get_or_404(expense_id)
    if expense.report_id != report.id:
        return jsonify({'message': 'Expense not found in this report'}), 404

    db.session.delete(expense)
    report.updated_at = datetime.utcnow() # Update parent report's timestamp
    db.session.commit()
    return jsonify({'message': 'Expense deleted successfully'}), 200
