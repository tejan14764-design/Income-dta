# INCOME – School Student Information and Financial Management System

**Version:** 1.0.0  
**Technology:** Electron · React · TypeScript · Django · PostgreSQL

---

## What INCOME Does

INCOME is a desktop-first school management system that handles:

- **Student Information Management** — registration, profiles, guardians, enrollment history, disability records
- **Financial Management** — individual fee structures, discounts, waivers, payment tracking with full audit trails
- **Payment Processing** — cash, mobile money, and bank transfer with mandatory verification workflow
- **Receipt Generation** — 80mm thermal receipt printing and PDF download
- **Financial Reporting** — class-level reports and CSV exports
- **Role-Based Access** — six system roles with fine-grained permissions
- **Audit Logs** — immutable record of all significant actions

---

## Quick Start (Development)

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.14+ | Backend |
| Node.js | 18+ | Frontend |
| PostgreSQL | 14+ | Database |
| Git | Any | Version control |

### 1. Clone and configure

```bash
git clone <repo-url>
cd Income
cp .env.example backend/.env
# Edit backend/.env with your DB credentials
```

### 2. Database setup

Run the PowerShell setup script (requires PostgreSQL postgres superuser password):

```powershell
.\scripts\setup_database.ps1 -PostgresPassword "your_postgres_password"
```

Or create the database manually:

```sql
CREATE USER income_user WITH PASSWORD 'Income@2024!';
CREATE DATABASE income_db OWNER income_user;
GRANT ALL PRIVILEGES ON DATABASE income_db TO income_user;
```

Then set `USE_SQLITE=False` in `backend/.env` and add your PostgreSQL credentials.

### 3. Backend setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_initial_data
```

Default admin credentials after seeding:
- **Username:** `admin`
- **Password:** `Admin@12345!`
- **⚠️ Change this password immediately after first login.**

### 4. Frontend setup

```bash
cd apps/web
npm install
npm run dev
```

The frontend runs on http://localhost:5173

### 5. Run the backend server

```bash
cd backend
venv\Scripts\python manage.py runserver
```

The API runs on http://localhost:8000  
API documentation: http://localhost:8000/api/docs/

---

## Running Tests

```bash
cd backend
$env:DJANGO_SETTINGS_MODULE = "config.settings"
.\venv\Scripts\python -m pytest ..\tests\backend\ -v
```

Expected: **55 tests pass**

---

## Building the Windows Installer

```bash
# 1. Build the React frontend
cd apps/web
npm run build

# 2. Copy dist to desktop app
xcopy /E /I /Y dist ..\desktop\dist

# 3. Compile Electron TypeScript
cd ../desktop
npx tsc -p tsconfig.electron.json

# 4. Build the installer
npx electron-builder --win nsis --x64 --publish never
```

Output: `apps/desktop/release/INCOME Setup 1.0.0.exe`

---

## Production Deployment

INCOME uses a **client-server** architecture in production:

```
[Windows Desktop App] ──HTTPS──▶ [Django API Server] ──▶ [PostgreSQL]
[Android PWA]         ──HTTPS──▶ [Django API Server]
```

### Server setup (Ubuntu/Debian)

```bash
# Install dependencies
sudo apt install python3 python3-pip postgresql nginx gunicorn

# Configure PostgreSQL, create DB
sudo -u postgres createuser income_user
sudo -u postgres createdb income_db -O income_user

# Deploy Django
git clone <repo> /opt/income
cd /opt/income/backend
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_initial_data
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### Configure the desktop app API URL

The installed desktop app reads the API URL from its local config store. After installation:

1. Launch INCOME
2. Go to **Settings → Application Settings**
3. Enter your production API URL (e.g., `https://api.yourschool.edu/api/v1`)

Alternatively, set the environment variable before packaging:
```
ELECTRON_API_URL=https://api.yourschool.edu/api/v1
```

### ⚠️ Code Signing Note

The installer `INCOME Setup 1.0.0.exe` is **unsigned**. Windows Defender SmartScreen will display a warning on first run. Click **"More info" → "Run anyway"** to proceed.

For production distribution, obtain a code signing certificate and configure in `electron-builder`:
```json
"win": { "certificateFile": "cert.pfx", "certificatePassword": "..." }
```

---

## Project Structure

```
Income/
├── apps/
│   ├── web/                # React + TypeScript frontend (Vite)
│   └── desktop/            # Electron wrapper + NSIS installer
├── backend/                # Django REST API
│   ├── accounts/           # Users, roles, permissions
│   ├── schools/            # Multi-tenant school management
│   ├── students/           # Student registration and profiles
│   ├── academics/          # Academic years, classes, enrollment
│   ├── finance/            # Fee categories, templates, charges
│   ├── payments/           # Payment recording, verification, reversal
│   ├── receipts/           # Receipt generation and thermal printing
│   ├── reports/            # Financial reports and CSV exports
│   └── audit/              # Immutable audit log
├── tests/backend/          # Pytest test suite (55 tests)
├── scripts/                # Setup and utility scripts
└── documentation/          # Technical documentation
```

---

## Default Roles and Permissions

| Role | Key Permissions |
|------|----------------|
| Super Administrator | Full system access |
| School Administrator | Full school access |
| Registrar | Student registration, academic records |
| Bursar / Cashier | Record payments, generate receipts |
| Financial Officer | Verify payments, manage fees, reports |
| Auditor | Read-only: payments, reports, audit logs |

**Separation of duties:** A cashier cannot verify their own payment submission.

---

## Currency

Primary currency: **Sierra Leonean New Leones (NLe)**  
All monetary values use `NUMERIC(14,2)` in PostgreSQL — never floating-point.

---

## API Documentation

After starting the backend, visit:
- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/
- OpenAPI schema: http://localhost:8000/api/schema/
