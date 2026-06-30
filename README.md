# NRVS - Network Recon & Vulnerability Scanner

A full-stack vulnerability assessment platform that automates network discovery, service enumeration, CVE correlation, and risk scoring — with a real-time React dashboard and professional reporting output.

Built for authorized internal assessments, defensive security workflows, and structured security education. Does not perform exploitation.

---

## What It Does

| Capability | Description |
|---|---|
| Host & Port Discovery | Nmap-powered scanning across single hosts, target lists, or CIDR ranges |
| Service & Version Detection | Identifies running services with version strings for accurate CVE matching |
| CVE Correlation | Maps detected versions to published vulnerabilities with CVSS scoring |
| Risk Scoring | Computes per-asset risk scores from severity distribution and exposure profile |
| MITRE ATT&CK Mapping | Connects findings to adversary technique context for prioritization |
| Historical Comparison | Diffs scan results over time — surfaces new findings and resolved issues |
| Screenshot Evidence | Captures web service screenshots automatically at scan time |
| Reporting | Exports HTML, PDF, and JSON reports for stakeholder distribution |
| Real-Time Progress | WebSocket-driven scan updates streamed live to the dashboard |
| Authentication | JWT-secured API with hashed password storage |

---

## Stack

**Backend** — Python, FastAPI, SQLAlchemy, PostgreSQL, python-nmap, WebSockets, JWT  
**Frontend** — React, Tailwind CSS, Chart.js, Axios  
**Infra** — Docker, Docker Compose

---

## Workflow

```
Login → Select Target → Run Scan → Service Enumeration → CVE Mapping → Risk Score → Dashboard → Export Report
```

Scan progress streams in real time. Results persist to PostgreSQL for historical comparison across assessment cycles. Reports are formatted for direct stakeholder distribution.

---

# Local Setup Guide

## Prerequisites

Before running the project, ensure the following dependencies are installed:

- Python 3.12+
- Node.js 18+ and npm
- PostgreSQL 16+
- Nmap
- Git

Install Nmap (Ubuntu/Debian):

```bash
sudo apt install nmap
```

---

## 1. Clone the Repository

```bash
git clone https://github.com/heetgohil28-dev/NRVS--Project.git
cd NRVS--Project
```

---

## 2. Backend Setup

Navigate to the backend directory and create a Python virtual environment.

```bash
cd backend

python3 -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

pip install -r requirements.txt --break-system-packages
```

---

## 3. Configure Environment Variables

Create a `.env` file inside the `backend/` directory.

```env
DATABASE_URL=postgresql://nrvs_user:nrvs_pass@localhost:5432/nrvs_db
SECRET_KEY=<YOUR_SECRET_KEY>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

NVD_API_KEY=<YOUR_NVD_API_KEY>
NVD_BASE_URL=https://services.nvd.nist.gov/rest/json/cves/2.0

CORS_ORIGINS=http://localhost:3000
ALLOWED_HOSTS=localhost,127.0.0.1

REPORT_OUTPUT_DIR=/tmp/nrvs_reports
```

### Generate a Secure Secret Key

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Generate an NVD API Key

Request a free API key from:

https://nvd.nist.gov/developers/request-an-api-key

---

## 4. Database Setup

Start PostgreSQL and open the PostgreSQL shell.

```bash
sudo -u postgres psql
```

Create the application database and user.

```sql
CREATE USER nrvs_user WITH PASSWORD 'nrvs_pass';
CREATE DATABASE nrvs_db OWNER nrvs_user;

\q
```

> **Note:** Database tables are created automatically during the first backend startup.

---

## 5. Run the Backend

```bash
cd backend

source venv/bin/activate

uvicorn app.main:app --reload
```

Backend URL:

```
http://localhost:8000
```

API Documentation:

```
http://localhost:8000/api/docs
```

---

## 6. Frontend Setup

Open a new terminal.

```bash
cd frontend

npm install

npm run dev
```

Frontend URL:

```
http://localhost:3000
```

The Vite development server automatically proxies the following endpoints to the FastAPI backend:

- `/api`
- `/ws`

---

## 7. First-Time Usage

Once both the frontend and backend are running:

1. Open `http://localhost:3000`
2. Register a new account.
3. Log in.
4. Start a scan against:

```
127.0.0.1
```

using the **Quick** scan profile to verify that the application is working correctly.

---

# Running with Docker

Start all services using Docker Compose.

```bash
docker compose up -d --build
```

This command starts:

- PostgreSQL
- FastAPI Backend
- React Frontend
- Nginx Reverse Proxy

The frontend will be served on **port 80**, while `/api` and `/ws` requests are automatically routed to the backend.

Before deploying to production, ensure your `.env` file contains:

- A strong `SECRET_KEY`
- A valid `NVD_API_KEY`
- Correct `CORS_ORIGINS`
- Production database credentials

---

# Security Notes

- JWT authentication protects all API endpoints except:
  - `POST /auth/register`
  - `POST /auth/login`
- Custom Nmap flags are validated server-side to prevent command injection.
- CIDR scans are restricted to `/24` or smaller networks to prevent accidental large-scale scans.
- Passwords must contain:
  - At least 8 characters
  - One uppercase letter
  - One lowercase letter
  - One digit
  - One special character
- Never commit your `.env` file. It is excluded via `.gitignore`.

---

## Use Cases

- Internal vulnerability assessments and network auditing
- Homelab and controlled lab environments
- Security awareness training and education
- Asset discovery and inventory
- Cybersecurity portfolio demonstration

---

## Disclaimer

NRVS is intended only for systems you own or have explicit written authorization to assess. Unauthorized scanning is illegal in most jurisdictions. The authors assume no liability for misuse. Users bear full legal and ethical responsibility for all scanning activity.

---

## Authors

**Heet Gohil** - Scan Engine, Asset Inventory, Risk Scoring, WebSocket Manager, Screenshot Service  
Heet's LinkedIn - https://www.linkedin.com/in/heetgohil/ 
Github - https://github.com/heetgohil28-dev 

**Maitrey Suthar** - Auth, CVE Engine, MITRE Mapping, Reports  
Maitrey's LinkedIn - https://www.linkedin.com/in/maitrey-suthar-210639315/ 
GitHub - https://github.com/paradoxialcode 


*Cybersecurity Engineering Students | Offensive Security & Red Teaming*

