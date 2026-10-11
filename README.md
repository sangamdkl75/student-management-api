# Student Management API

A FastAPI app for registering users and managing student records. It includes
JWT login, role-based permissions, student ownership, and a small browser
frontend.

## Technologies

Python, FastAPI, SQLAlchemy, SQLite, Alembic, JWT, pytest, HTML, CSS, and
JavaScript.

## Project structure

```text
student-api/
├── main.py
├── database.py
├── initialize_database.py
├── models.py
├── schemas.py
├── routers/             # Authentication and student API routes
├── alembic/versions/    # Database migrations
├── frontend/            # Static web interface
└── tests/               # API and migration tests
```

## Setup on Windows

Open PowerShell in the project folder. Create and activate a virtual
environment, then install the dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create a `.env` file in the project folder:

```text
SECRET_KEY=<your-random-secret-key>
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=sqlite:///./students.db
FRONTEND_ORIGIN=http://127.0.0.1:5500
```

Generate a strong key locally; do not copy a real key into this README:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

`SECRET_KEY` must be at least 32 bytes. Access tokens expire after 30 minutes
by default; set `ACCESS_TOKEN_EXPIRE_MINUTES` to another positive whole number
to change that. `DATABASE_URL` defaults to the SQLite database shown above.
`FRONTEND_ORIGIN` is optional and must be one HTTP(S) origin without a path.

Initialize or update the database before starting the API:

```powershell
python initialize_database.py
```

The initializer uses `DATABASE_URL` from `.env`, preserves supported existing
data, and refuses unrecognized or inconsistent database schemas. Do not
manually stamp a database or run migrations against an unintended database.

## Run the app

In one PowerShell window, start the API from the project folder:

```powershell
uvicorn main:app --reload
```

In a second window, also from the project folder, serve the frontend:

```powershell
python -m http.server 5500 --bind 127.0.0.1 --directory frontend
```

Open the frontend at <http://127.0.0.1:5500>. The API runs at
<http://127.0.0.1:8000>.

Swagger API documentation: <http://127.0.0.1:8000/docs>

## Migrations and tests

`python initialize_database.py` safely initializes or upgrades the database.
After changing a model, generate a migration with:

```powershell
alembic revision --autogenerate -m "describe the change"
```

Review generated migrations before applying them with the initializer.

Run the test suite with:

```powershell
pytest -q
```

Tests use isolated databases.

## Security

- Keep `.env`, database files, passwords, and access tokens private. Do not
  commit them or place secrets in frontend files.
- Use a unique, strong `SECRET_KEY`; never use a sample value in deployment.
- Use HTTPS when deploying the API or frontend.
- New registrations are regular users. Grant an admin role only through a
  trusted database connection, and verify that the intended account alone is
  updated.
