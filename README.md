# Student Management API

A student-record app with a FastAPI backend and a small browser frontend.
Users can register and sign in; student access is controlled by roles and
record ownership.

## Project layout

```text
student-api/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── initialize_database.py
│   ├── routers/
│   ├── alembic/       # Database migrations
│   ├── tests/
│   └── requirements.txt
├── frontend/          # HTML, CSS, and JavaScript
├── .env               # Local settings; do not commit
└── README.md
```

## Windows setup

Run these commands in PowerShell from the repository root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
```

Create `.env` in the repository root:

```text
SECRET_KEY=<random-secret-key>
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=sqlite:///./students.db
FRONTEND_ORIGIN=http://127.0.0.1:5500
```

Generate a private key locally with:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

`SECRET_KEY` must be at least 32 bytes. Tokens expire after 30 minutes by
default; set `ACCESS_TOKEN_EXPIRE_MINUTES` to a positive whole number to
change the lifetime. `DATABASE_URL` defaults to SQLite. Relative SQLite paths
are resolved from the repository root, regardless of the command's working
directory. `FRONTEND_ORIGIN` is optional; the local frontend origin is allowed
by default.

## Initialize and run

Initialize or update the database from the `backend` folder:

```powershell
cd backend
python initialize_database.py
uvicorn main:app --reload
```

The API is at <http://127.0.0.1:8000>. Swagger documentation is at
<http://127.0.0.1:8000/docs>.

In a second PowerShell window, start the frontend from the repository root:

```powershell
python -m http.server 5500 --bind 127.0.0.1 --directory frontend
```

Open <http://127.0.0.1:5500>.

## Migrations and tests

The initializer runs Alembic migrations safely and refuses unsupported
database schemas. To create a migration after changing a model, run from
`backend`:

```powershell
alembic revision --autogenerate -m "describe the change"
```

Review the generated migration, then run `python initialize_database.py` to
apply it. Run tests from `backend`:

```powershell
pytest -q
```

Tests use isolated databases.

## Security

- Keep `.env`, database files, passwords, and access tokens private.
- Use a unique, strong `SECRET_KEY`; never commit it or put it in frontend code.
- Use HTTPS when deploying.
- New registrations are regular users. Grant admin access only through a
  trusted database connection.
