# Expense Management System API

A Flask-based API for managing company expense reports. This system allows employees to create, manage, and submit expense reports, and for managers to review and approve/reject these reports.

## Table of Contents
- [Features](#features)
- [Setup and Installation](#setup-and-installation)
- [API Endpoints Documentation](#api-endpoints-documentation)
  - [Authentication](#authentication)
  - [Expense Reports](#expense-reports)
  - [Expenses within a Report](#expenses-within-a-report)
  - [Approvals](#approvals)
- [Database Initialization](#database-initialization)
- [Running Tests](#running-tests)

## Features
- User registration and JWT-based authentication.
- Role-based access control (employees, managers).
- CRUD operations for expense reports.
- CRUD operations for expenses within reports.
- Submission workflow for reports.
- Approval/rejection workflow for managers.

## Setup and Installation

### Prerequisites
- Python 3.7+
- PostgreSQL (or another SQLAlchemy-compatible database)
- `pip` for installing Python packages

### Steps

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd expense_management_system
    ```

2.  **Create a Virtual Environment:**
    It's highly recommended to use a virtual environment.
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Variable Setup:**
    The application uses a `.env` file to manage environment-specific variables. Create a `.env` file in the project root directory by copying the example:
    ```bash
    cp .env.example .env
    ```
    Now, edit the `.env` file with your actual configuration values:
    *   `FLASK_APP`: Should be `run.py`.
    *   `FLASK_ENV`: Set to `development` for development mode, `production` for production.
    *   `SECRET_KEY`: A strong, unique secret key used for session management and token signing. Generate one using `python -c 'import secrets; print(secrets.token_hex(24))'`.
    *   `DATABASE_URL`: The connection string for your database. For PostgreSQL, it typically looks like: `postgresql://your_db_user:your_db_password@your_db_host:your_db_port/your_db_name`.
    *   `TEST_DATABASE_URL` (Optional): If you want to use a persistent database for tests instead of the default in-memory SQLite.

    Example `.env` content:
    ```
    FLASK_APP=run.py
    FLASK_ENV=development
    SECRET_KEY=generated_secret_key_here
    DATABASE_URL=postgresql://user:password@localhost/expense_db
    ```

5.  **Database Setup:**
    *   Ensure your PostgreSQL server is running and you have created the database specified in `DATABASE_URL`.
    *   To create the necessary tables, you can use the Flask shell:
        ```bash
        flask shell
        ```
        Then, within the shell:
        ```python
        from app import db
        db.create_all()
        exit()
        ```
    *   **Initial Roles:** The system expects certain roles ('employee', 'manager', 'admin') to exist. These are currently created by the test fixtures or on-the-fly during registration if not found. For a production setup, a seed script would be ideal (e.g., `flask seed roles` - this command is hypothetical and would need to be implemented). See [Database Initialization](#database-initialization) for more details.

6.  **Running the Application:**
    ```bash
    flask run
    ```
    The application will typically be available at `http://127.0.0.1:5000/`.

## API Endpoints Documentation

All API endpoints require a `Content-Type: application/json` header for requests with a body.
Authentication is handled via Bearer Tokens in the `Authorization` header.

### Authentication (`/auth`)

#### 1. Register User
*   **Endpoint:** `POST /auth/register`
*   **Description:** Registers a new user. Assigns the 'employee' role by default.
*   **Required Roles:** None
*   **Sample Request Body:**
    ```json
    {
        "username": "newemployee",
        "email": "employee@example.com",
        "password": "securepassword123"
    }
    ```
*   **Sample Success Response (201 Created):**
    ```json
    {
        "message": "User registered successfully"
    }
    ```
*   **Sample Error Responses:**
    *   **400 Bad Request (Missing Fields):**
        ```json
        {
            "message": "Missing username, email, or password"
        }
        ```
    *   **400 Bad Request (Username/Email Exists):**
        ```json
        {
            "message": "Username already exists" 
        } 
        // or "Email already registered"
        ```

#### 2. Login User
*   **Endpoint:** `POST /auth/login`
*   **Description:** Authenticates an existing user and returns a JWT.
*   **Required Roles:** None
*   **Sample Request Body:**
    ```json
    {
        "username": "newemployee",
        "password": "securepassword123"
    }
    ```
*   **Sample Success Response (200 OK):**
    ```json
    {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c" 
    }
    ```
*   **Sample Error Responses:**
    *   **400 Bad Request (Missing Fields):**
        ```json
        {
            "message": "Missing username or password"
        }
        ```
    *   **401 Unauthorized (Invalid Credentials):**
        ```json
        {
            "message": "Invalid username or password"
        }
        ```

---

### Expense Reports (`/reports`)
Requires authentication for all endpoints.

#### 1. Create Expense Report
*   **Endpoint:** `POST /reports`
*   **Description:** Creates a new expense report for the authenticated user. Status defaults to 'draft'.
*   **Required Roles:** Authenticated user (e.g., 'employee')
*   **Sample Request Body:**
    ```json
    {
        "title": "Client Visit Q3",
        "description": "Expenses related to the client visit in New York."
    }
    ```
*   **Sample Success Response (201 Created):**
    ```json
    {
        "message": "Expense report created",
        "report_id": 1
    }
    ```
*   **Sample Error Response (400 Bad Request - Missing Title):**
    ```json
    {
        "message": "Title is required"
    }
    ```

#### 2. List Expense Reports
*   **Endpoint:** `GET /reports`
*   **Description:** Lists all expense reports for the authenticated user.
*   **Required Roles:** Authenticated user
*   **Sample Success Response (200 OK):**
    ```json
    {
        "reports": [
            {
                "id": 1,
                "title": "Client Visit Q3",
                "description": "Expenses related to the client visit in New York.",
                "status": "draft",
                "created_at": "2023-10-27T10:00:00Z",
                "updated_at": "2023-10-27T10:05:00Z",
                "submitted_at": null
            }
            // ... more reports
        ]
    }
    ```

#### 3. Get Expense Report Details
*   **Endpoint:** `GET /reports/{report_id}`
*   **Description:** Retrieves details of a specific expense report, including its associated expenses.
*   **Required Roles:** Owner of the report (or potentially 'manager'/'admin' - current setup is owner-only for this direct GET).
*   **Sample Success Response (200 OK):**
    ```json
    {
        "id": 1,
        "title": "Client Visit Q3",
        "description": "Expenses related to the client visit in New York.",
        "status": "draft",
        "user_id": 5,
        "created_at": "2023-10-27T10:00:00Z",
        "updated_at": "2023-10-27T10:05:00Z",
        "submitted_at": null,
        "expenses": [
            {
                "id": 101,
                "date": "2023-10-25T00:00:00Z",
                "category": "Travel",
                "amount": "250.00",
                "currency": "USD",
                "description": "Flight tickets"
            }
        ]
    }
    ```
*   **Sample Error Response (404 Not Found):**
    ```json
    {
        "message": "Report not found" // Or a generic 404 from get_or_404
    }
    ```
*   **Sample Error Response (403 Forbidden - Not Owner):**
    ```json
    {
        "message": "Access denied to this report"
    }
    ```

#### 4. Update Expense Report
*   **Endpoint:** `PUT /reports/{report_id}`
*   **Description:** Updates an existing expense report. Only 'draft' reports can be updated.
*   **Required Roles:** Owner of the report.
*   **Sample Request Body:**
    ```json
    {
        "title": "Updated: Client Visit Q3",
        "description": "Updated details for New York client visit."
    }
    ```
*   **Sample Success Response (200 OK):**
    ```json
    {
        "message": "Report updated successfully"
    }
    ```
*   **Sample Error Response (400 Bad Request - Not Draft):**
    ```json
    {
        "message": "Only draft reports can be updated"
    }
    ```

#### 5. Delete Expense Report
*   **Endpoint:** `DELETE /reports/{report_id}`
*   **Description:** Deletes an existing expense report. Only 'draft' reports can be deleted. Associated expenses are also deleted.
*   **Required Roles:** Owner of the report.
*   **Sample Success Response (200 OK):**
    ```json
    {
        "message": "Report deleted successfully"
    }
    ```
*   **Sample Error Response (400 Bad Request - Not Draft):**
    ```json
    {
        "message": "Only draft reports can be deleted"
    }
    ```

#### 6. Submit Expense Report
*   **Endpoint:** `POST /reports/{report_id}/submit`
*   **Description:** Submits a 'draft' expense report for approval. Report must contain at least one expense.
*   **Required Roles:** Owner of the report.
*   **Sample Success Response (200 OK):**
    ```json
    {
        "message": "Report submitted successfully"
    }
    ```
*   **Sample Error Responses:**
    *   **400 Bad Request (Not Draft):**
        ```json
        {
            "message": "Only draft reports can be submitted"
        }
        ```
    *   **400 Bad Request (Empty Report):**
        ```json
        {
            "message": "Cannot submit an empty report. Add at least one expense."
        }
        ```

---

### Expenses within a Report (`/reports/{report_id}/expenses`)
Requires authentication. Parent report's status and ownership rules apply.

#### 1. Add Expense to Report
*   **Endpoint:** `POST /reports/{report_id}/expenses`
*   **Description:** Adds a new expense item to a 'draft' expense report.
*   **Required Roles:** Owner of the parent report.
*   **Sample Request Body:**
    ```json
    {
        "date": "2023-10-25", 
        "category": "Meals",
        "amount": "45.50",
        "currency": "USD",
        "description": "Dinner with client"
    }
    ```
*   **Sample Success Response (201 Created):**
    ```json
    {
        "message": "Expense added to report",
        "expense_id": 102
    }
    ```
*   **Sample Error Responses:**
    *   **400 Bad Request (Parent Report Not Draft):**
        ```json
        {
            "message": "Expenses can only be added to draft reports"
        }
        ```
    *   **400 Bad Request (Missing Fields/Invalid Data):**
        ```json
        {
            "message": "Missing category or amount for expense" 
            // or "Invalid amount format"
            // or "Invalid date format. Use YYYY-MM-DD"
        }
        ```

#### 2. List Expenses for a Report
*   **Endpoint:** `GET /reports/{report_id}/expenses`
*   **Description:** Lists all expenses associated with a specific report.
*   **Required Roles:** Owner of the parent report.
*   **Sample Success Response (200 OK):**
    ```json
    {
        "expenses": [
            {
                "id": 101,
                "date": "2023-10-25T00:00:00Z",
                "category": "Travel",
                "amount": "250.00",
                "currency": "USD",
                "description": "Flight tickets",
                "created_at": "2023-10-27T10:01:00Z",
                "updated_at": "2023-10-27T10:01:00Z"
            },
            {
                "id": 102,
                "date": "2023-10-25T00:00:00Z",
                "category": "Meals",
                "amount": "45.50",
                "currency": "USD",
                "description": "Dinner with client",
                "created_at": "2023-10-27T10:05:00Z",
                "updated_at": "2023-10-27T10:05:00Z"
            }
        ]
    }
    ```

#### 3. Get Expense Details
*   **Endpoint:** `GET /reports/{report_id}/expenses/{expense_id}`
*   **Description:** Retrieves details of a specific expense within a report.
*   **Required Roles:** Owner of the parent report.
*   **Sample Success Response (200 OK):**
    ```json
    {
        "id": 102,
        "date": "2023-10-25T00:00:00Z",
        "category": "Meals",
        "amount": "45.50",
        "currency": "USD",
        "description": "Dinner with client",
        "report_id": 1,
        "created_at": "2023-10-27T10:05:00Z",
        "updated_at": "2023-10-27T10:05:00Z"
    }
    ```
*   **Sample Error Response (404 Not Found - Expense not in Report):**
    ```json
    {
        "message": "Expense not found in this report"
    }
    ```

#### 4. Update Expense in Report
*   **Endpoint:** `PUT /reports/{report_id}/expenses/{expense_id}`
*   **Description:** Updates an existing expense within a 'draft' report.
*   **Required Roles:** Owner of the parent report.
*   **Sample Request Body:**
    ```json
    {
        "amount": "50.00",
        "description": "Updated: Dinner with client and colleague"
    }
    ```
*   **Sample Success Response (200 OK):**
    ```json
    {
        "message": "Expense updated successfully"
    }
    ```
*   **Sample Error Response (400 Bad Request - Parent Report Not Draft):**
    ```json
    {
        "message": "Expenses can only be updated in draft reports"
    }
    ```

#### 5. Delete Expense from Report
*   **Endpoint:** `DELETE /reports/{report_id}/expenses/{expense_id}`
*   **Description:** Deletes an expense from a 'draft' report.
*   **Required Roles:** Owner of the parent report.
*   **Sample Success Response (200 OK):**
    ```json
    {
        "message": "Expense deleted successfully"
    }
    ```
*   **Sample Error Response (400 Bad Request - Parent Report Not Draft):**
    ```json
    {
        "message": "Expenses can only be deleted from draft reports"
    }
    ```

---

### Approvals (`/approvals`)
Requires 'manager' role for all endpoints.

#### 1. List Pending Reports for Approval
*   **Endpoint:** `GET /approvals/pending`
*   **Description:** Lists all expense reports with 'submitted' status, excluding those submitted by the manager themselves.
*   **Required Roles:** 'manager'
*   **Sample Success Response (200 OK):**
    ```json
    {
        "pending_reports": [
            {
                "id": 2,
                "title": "Employee Conference Travel",
                "description": "Expenses for attending tech conference",
                "status": "submitted",
                "submitted_at": "2023-10-28T09:00:00Z",
                "updated_at": "2023-10-28T09:00:00Z",
                "user_id": 10,
                "author_username": "employee_user",
                "total_amount": "350.75" 
            }
            // ... more reports
        ]
    }
    ```

#### 2. Approve Expense Report
*   **Endpoint:** `POST /approvals/reports/{report_id}/approve`
*   **Description:** Approves a 'submitted' expense report.
*   **Required Roles:** 'manager'
*   **Sample Success Response (200 OK):**
    ```json
    {
        "message": "Report ID 2 approved successfully"
    }
    ```
*   **Sample Error Responses:**
    *   **400 Bad Request (Report Not Submitted):**
        ```json
        {
            "message": "Report is not in a submitted state for approval"
        }
        ```
    *   **403 Forbidden (Manager Approving Own Report):**
        ```json
        {
            "message": "Managers cannot approve their own reports through this endpoint"
        }
        ```

#### 3. Reject Expense Report
*   **Endpoint:** `POST /approvals/reports/{report_id}/reject`
*   **Description:** Rejects a 'submitted' expense report.
*   **Required Roles:** 'manager'
*   **Sample Request Body (Optional Reason):**
    ```json
    {
        "reason": "Exceeded budget for meals."
    }
    ```
*   **Sample Success Response (200 OK):**
    ```json
    {
        "message": "Report ID 2 rejected successfully",
        "reason": "Exceeded budget for meals." // if reason was provided
    }
    ```
*   **Sample Error Response (400 Bad Request - Report Not Submitted):**
    ```json
    {
        "message": "Report is not in a submitted state for rejection"
    }
    ```

## Database Initialization

### Initial Roles
The system relies on predefined roles: `employee`, `manager`, and `admin`.
-   During user registration (`/auth/register`), if the `employee` role does not exist, an attempt is made to create it. This is a fallback and not ideal for production.
-   Test fixtures (`tests/conftest.py`) explicitly create `employee`, `manager`, and `admin` roles when the test application context is initialized.

For a production environment, it's recommended to have a dedicated seeding mechanism to pre-populate the `roles` table. This could be a custom Flask CLI command (e.g., `flask seed init-roles`).

**Example of manual role creation via Flask Shell (if needed):**
```bash
flask shell
```
```python
from app import db
from app.models.role import Role

# Check if roles exist, create if not
if not Role.query.filter_by(name='employee').first():
    db.session.add(Role(name='employee'))
if not Role.query.filter_by(name='manager').first():
    db.session.add(Role(name='manager'))
if not Role.query.filter_by(name='admin').first():
    db.session.add(Role(name='admin'))

db.session.commit()
print("Roles checked/created.")
exit()
```

## Running Tests
The project uses `pytest` for running unit and integration tests.

1.  Ensure you have installed development dependencies:
    ```bash
    pip install -r requirements.txt 
    # (pytest and pytest-flask are included)
    ```
2.  Make sure your `.env` file is configured, or that `TestConfig` in `config.py` is set up for your testing database (defaults to SQLite in-memory).
3.  Run tests from the project root directory:
    ```bash
    pytest
    ```
    Or with more verbose output:
    ```bash
    pytest -v
    ```

The tests are located in the `tests/` directory and cover models, authentication API, report API, expense API, and approval API. Fixtures in `tests/conftest.py` set up the test environment.
