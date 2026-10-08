# Student Management API

A REST API for managing student records, built with Python and FastAPI.

## Features

* Student CRUD operations
* SQLite database
* SQLAlchemy ORM
* User registration and login
* Password hashing with Argon2
* JWT authentication
* Role-based authorization
* Alembic database migrations
* Automated testing with pytest
* Interactive Swagger API documentation

## Technologies

* Python
* FastAPI
* SQLAlchemy
* SQLite
* Pydantic
* PyJWT
* pwdlib
* Alembic
* pytest
* Uvicorn

## Project Structure

```text
student-api/
│
├── main.py
├── database.py
├── models.py
├── schemas.py
│
├── routers/
│   ├── __init__.py
│   ├── auth.py
│   └── students.py
│
├── tests/
│   ├── conftest.py
│   └── test_students.py
│
├── alembic/
│   ├── README
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── f8fdb94d842b_add_user_role.py
│
├── alembic.ini
├── pytest.ini
├── requirements.txt
├── .gitignore
└── README.md
```

## Setup

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd student-api
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Create `.env`

Create a `.env` file in the project root:

```text
SECRET_KEY=your-secret-key
```

The `.env` file should not be uploaded to GitHub.

### 6. Run the API

```bash
uvicorn main:app --reload
```

The API will run at:

```text
http://127.0.0.1:8000
```

## API Documentation

FastAPI provides interactive API documentation through Swagger UI.

Open:

```text
http://127.0.0.1:8000/docs
```

## Authentication

### Register

```text
POST /auth/register
```

Creates a new user.

### Login

```text
POST /auth/login
```

Returns a JWT access token after successful login.

Protected requests use:

```text
Authorization: Bearer <access_token>
```

## User Roles

### User

A normal user can:

* View students

### Admin

An admin can:

* View students
* Create students
* Update students
* Delete students

## Student Endpoints

| Method | Endpoint                 | Purpose                    |
| ------ | ------------------------ | -------------------------- |
| GET    | `/students/`             | Get all students           |
| GET    | `/students/{student_id}` | Get one student            |
| POST   | `/students/`             | Create a student           |
| PUT    | `/students/{student_id}` | Update a student           |
| PATCH  | `/students/{student_id}` | Partially update a student |
| DELETE | `/students/{student_id}` | Delete a student           |

## Testing

The project uses pytest for automated testing.

Run:

```bash
pytest
```

Current tests verify:

* Home endpoint
* Unauthorized access to protected students endpoint
* Successful login
* Access to protected endpoint using JWT

## Database Migrations

The project uses Alembic for database migrations.

Create a migration:

```bash
alembic revision --autogenerate -m "description"
```

Apply migrations:

```bash
alembic upgrade head
```

Check the current migration:

```bash
alembic current
```

## Environment and Ignored Files

The following files are kept local and are not uploaded to GitHub:

```text
.env
students.db
.venv/
__pycache__/
.pytest_cache/
```

## Future Improvements

* Build a frontend
* Connect the frontend to the FastAPI backend
* Add more automated tests
* Improve validation and error handling
* Add pagination and search
* Add user management
* Deploy the application

## Author

Built as a learning project to understand backend development with Python and FastAPI.
