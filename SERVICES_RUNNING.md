# 🚀 Services Running Guide

## Quick Start

### Option 1: Using the Service Manager (Recommended)
```bash
python3 run_services.py
```

### Option 2: Using the Shell Script
```bash
./start_all_services.sh
```

### Option 3: Manual Start

**Terminal 1 - API Server:**
```bash
cd /Users/yusaf/Desktop/solidity-vuln-scanner
source venv/bin/activate
python fastapi_api.py
```

**Terminal 2 - Streamlit UI:**
```bash
cd /Users/yusaf/Desktop/solidity-vuln-scanner
source venv/bin/activate
streamlit run streamlit_ui.py
```

**Terminal 3 - Celery Worker (Optional, requires Redis):**
```bash
cd /Users/yusaf/Desktop/solidity-vuln-scanner
source venv/bin/activate
celery -A queue_system.celery_app worker --loglevel=info
```

## Service URLs

- **API Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Streamlit UI**: http://localhost:8501
- **Metrics**: http://localhost:8000/metrics
- **Health Check**: http://localhost:8000/health

## Stop Services

```bash
# Stop all services
pkill -f "fastapi_api.py"
pkill -f "streamlit.*streamlit_ui.py"
pkill -f "celery.*queue_system"

# Or use the PID files
kill $(cat api.pid) 2>/dev/null
kill $(cat ui.pid) 2>/dev/null
```

## Check Status

```bash
# Check if services are running
curl http://localhost:8000/health
curl http://localhost:8501

# Check processes
ps aux | grep -E "(fastapi|streamlit|celery)"
```

## Docker Alternative

```bash
docker-compose up
```

This starts:
- API server on port 8000
- Streamlit UI on port 8501
- Optional: Slither and Mythril containers
