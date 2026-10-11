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
├── initialize_database.py
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
│   ├── test_auth.py
│   ├── test_cors.py
│   ├── test_database_migrations.py
│   └── test_students.py
│
├── alembic/
│   ├── README
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── f8fdb94d842b_add_user_role.py
│       ├── f16e6f5db93c_initial_schema.py
│       └── 27e3a8b8ec85_add_student_user_ownership.py
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

### 5. Configure `.env`

Create a `.env` file in the project root. Generate a random signing key
locally; do not use a sample or guessable value. `DATABASE_URL` defaults to
the SQLite file `students.db` in the project root when omitted. Set it here
if you want another database:

```text
SECRET_KEY=<paste-a-random-key-generated-locally>
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=sqlite:///./students.db
FRONTEND_ORIGIN=http://127.0.0.1:5500
```

For example, generate a key with Python:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

The API refuses to start if `SECRET_KEY` is missing or shorter than 32 bytes.
Access tokens expire after 30 minutes by default. Set
`ACCESS_TOKEN_EXPIRE_MINUTES` to a positive whole number to change the lifetime.

The `.env` file should not be uploaded to GitHub.

### 6. Initialize or update the database

From the project root, run this before starting the API:

```bash
python initialize_database.py
```

This is the supported setup command for both a fresh database and an older
database created by this application. It uses the same `.env` and
`DATABASE_URL` as the API. For an existing unversioned database, it checks
that the `users` and `students` columns match a known project schema before
recording an Alembic revision. An unexpected or partial schema stops with an
error; it is not blindly stamped. Existing rows are retained.

After initialization, start the API:

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

The project uses pytest for automated testing. Tests use isolated in-memory or
temporary databases, not the development `students.db`.

Run the complete suite:

```bash
pytest -q
```

The suite covers authentication, registration and password hashing, CORS,
student CRUD and authorization, ownership rules, and temporary-database
migration setup and downgrade behavior.

## Database Migrations

Alembic is the schema-change mechanism; the application does not create tables
on startup. Run `python initialize_database.py` after installing dependencies
and configuring `.env`, and whenever a new migration is added.

To create a migration after changing SQLAlchemy models:

```bash
alembic revision --autogenerate -m "description"
```

Review the generated file, then run the initialization command above to apply
it to the configured database. `alembic current` can be used to inspect the
revision after initialization. Do not manually stamp an existing database
unless its schema has been independently verified.

The published `f8fdb94d842b` migration remains unchanged. The new baseline
conditionally creates the original tables when absent, and the ownership
migration joins the baseline and published migration branches. The baseline
downgrade intentionally leaves the tables in place because it cannot know
whether it created them or adopted tables containing user data. The ownership
migration's downgrade removes its foreign-key constraint but keeps the
`students.user_id` column and values.

The published user-role migration is preserved as-is; its downgrade removes
the `users.role` column. Avoid downgrading past that migration if you need to
retain role values.

## Admin Provisioning

Registration creates a normal user; there is no public admin-registration
endpoint or default admin account. Register the account through `/auth/register`
and then, using a trusted SQL client connected to the same `DATABASE_URL`, set
the role for that exact username:

```sql
UPDATE users SET role = 'admin' WHERE username = '<registered-username>';
```

Check that exactly one row was updated. Never put a real password or signing
key in this SQL command or in source control. Do not expose a production
database to the public API just to perform this one-time role change.

## Environment and Ignored Files

Local environment files, SQLite databases and backups, virtual environments,
Python caches, test caches, and common private-key files are ignored by Git.
Do not force-add secrets or database files.

```text
.env*
*.db
*.db.bak
*.sqlite*
.venv/
__pycache__/
.pytest_cache/
*.pem
*.key
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
