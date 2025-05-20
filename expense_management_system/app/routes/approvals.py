from flask import Blueprint, request, jsonify, g
from app import db
from app.models.expense_report import ExpenseReport
from app.models.user import User # Import User if needed for checks
from app.services.auth_decorator import token_required # Already checks for login
from app.services.role_decorator import role_required # For role specific access
from datetime import datetime

bp = Blueprint('approvals', __name__)

@bp.route('/pending', methods=['GET'])
@role_required('manager') # Only managers can access this
def list_pending_reports():
    # For now, a manager sees all reports with 'submitted' status
    # not authored by themselves.
    # A more complex system would have specific manager-employee relationships.
    pending_reports = ExpenseReport.query.filter(
        ExpenseReport.status == 'submitted',
        ExpenseReport.user_id != g.current_user.id # Managers don't approve their own reports via this
    ).order_by(ExpenseReport.submitted_at.asc()).all()
    
    output = []
    for report in pending_reports:
        author = User.query.get(report.user_id) # Get author details
        output.append({
            'id': report.id,
            'title': report.title,
            'description': report.description,
            'status': report.status,
            'submitted_at': report.submitted_at.isoformat() if report.submitted_at else None,
            'updated_at': report.updated_at.isoformat(),
            'user_id': report.user_id,
            'author_username': author.username if author else 'Unknown',
            'total_amount': sum(expense.amount for expense in report.expenses) # Calculate total amount
        })
    return jsonify({'pending_reports': output}), 200

@bp.route('/reports/<int:report_id>/approve', methods=['POST'])
@role_required('manager')
def approve_report(report_id):
    report = ExpenseReport.query.get_or_404(report_id)
    
    if report.user_id == g.current_user.id:
        return jsonify({'message': 'Managers cannot approve their own reports through this endpoint'}), 403

    if report.status != 'submitted':
        return jsonify({'message': 'Report is not in a submitted state for approval'}), 400

    report.status = 'approved'
    report.updated_at = datetime.utcnow()
    # Potentially add an approver_id field to the report
    # report.approver_id = g.current_user.id 
    db.session.commit()
    # TODO: Add notification logic here in a real system
    return jsonify({'message': f'Report ID {report.id} approved successfully'}), 200

@bp.route('/reports/<int:report_id>/reject', methods=['POST'])
@role_required('manager')
def reject_report(report_id):
    report = ExpenseReport.query.get_or_404(report_id)

    if report.user_id == g.current_user.id:
        return jsonify({'message': 'Managers cannot reject their own reports through this endpoint'}), 403
        
    if report.status != 'submitted':
        return jsonify({'message': 'Report is not in a submitted state for rejection'}), 400

    data = request.get_json()
    rejection_reason = data.get('reason', '') if data else ''

    report.status = 'rejected'
    report.updated_at = datetime.utcnow()
    # Store rejection_reason if a field is added to the model
    # report.rejection_reason = rejection_reason
    db.session.commit()
    # TODO: Add notification logic here
    return jsonify({'message': f'Report ID {report.id} rejected successfully', 'reason': rejection_reason}), 200
