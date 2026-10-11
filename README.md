# Student Management API

A simple student management application built with FastAPI. It provides secure login, user roles, and student record management through a web frontend and REST API.

## Features

* User registration and login
* JWT authentication
* Admin and regular user roles
* Add, view, update, and delete student records
* Responsive web frontend
* Automated tests

## Technologies

* Python and FastAPI
* SQLAlchemy and SQLite
* Alembic
* JWT authentication
* HTML, CSS, and JavaScript
* Pytest

## Getting Started

### 1. Clone the Project

```bash
git clone https://github.com/sangamdkl75/student-management-api.git
cd student-management-api
```

### 2. Set Up Python

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file if required by your project. Use the variable names expected by the application.

**Note:** Never share passwords, secret keys, or your `.env` file publicly.

### 4. Initialize the Database

Follow the database initialization instructions in the project. If you already have a database containing data, check the configuration before initializing it.

### 5. Run the Backend

```powershell
uvicorn main:app --reload
```

Backend: http://127.0.0.1:8000

### 6. Run the Frontend

Open a second terminal:

```powershell
cd frontend
python -m http.server 5500
```

Frontend: http://localhost:5500

### 7. API Documentation

Open http://127.0.0.1:8000/docs to explore and test API endpoints.

### 8. Run Tests

From the project root, run:

```powershell
pytest -q
```

## Project Structure

```text
student-management-api/
├── alembic/       # Database migrations
├── frontend/      # Web interface
├── routers/       # API endpoints
├── tests/         # Automated tests
├── main.py        # Application entry point
├── models.py      # Database models
├── schemas.py     # Data validation
├── database.py    # Database configuration
└── requirements.txt
```
