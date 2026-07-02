# Starting Vigilance Operations

This document provides step-by-step procedures to start the Vigilance Operations AI Agent Proxy application locally.

## Prerequisites

Before starting, ensure you have the following installed on your system:
- **Docker & Docker Compose** (Required for Method 1)
- **Node.js 20+** (Required for Method 2)
- **Python 3.11+** (Required for Method 2)
- **Git**

---

## Method 1: Docker Compose (Recommended)

The easiest way to run the entire stack locally is using Docker Compose. This will automatically provision and connect the PostgreSQL database, Redis instance, backend API, and frontend dashboard.

**Step 1: Clone the repository**
```bash
git clone https://github.com/your-org/AgentAdmin.git
cd AgentAdmin
```

**Step 2: Configure Environment Variables**
```bash
cp .env.example .env
```
*Note: Open `.env` in a text editor to fill in any required keys such as `OPENAI_API_KEY` or custom database credentials if needed.*

**Step 3: Start the Docker Stack**
```bash
docker compose up -d --build
```

**Step 4: Access the Application**
- The **Backend API** will be available at: `http://localhost:8000`
- The **Frontend Dashboard** will be available at: `http://localhost:3000`

To stop the application later, run `docker-compose down`.

---

## Method 2: Manual Startup

If you prefer to run the services outside of Docker, you can start them manually.

**Step 1: Configure Environments**
Make sure you have cloned the repository and navigated to the `AgentAdmin` directory.
```bash
cp .env.example .env
```
*Note: You must edit `.env`. Make sure `DATABASE_URL` uses the `postgresql+asyncpg://` driver rather than just `postgresql://`, and ensure `REDIS_URL` points to your Redis instance.*

**Step 2: Start the Required Services**
If you don't have PostgreSQL and Redis running locally, you can start them from the root directory using the existing compose configuration:
```bash
docker compose up -d db redis
```

**Step 3: Start the Backend Proxy**
Open a terminal in the root directory and run:
```bash
cd backend

# Create and activate a Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Load environment variables and start the FastAPI proxy server
set -a && source ../.env && set +a
uvicorn main:app --reload --port 8000
```
*The backend API is now running at `http://localhost:8000`.*

**Step 4: Start the Frontend Dashboard**
Open a **new** terminal window (keep the backend running in the first terminal), navigate to the root directory, and ensure Node.js v20+ is installed (you can use `nvm install 20 && nvm use 20`). Then run:
```bash
cd frontend

# Install Node modules
npm install

# Start the Next.js development server
npm run dev
```
*The frontend dashboard is now running at `http://localhost:3000`.*
