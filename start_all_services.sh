#!/bin/bash
# Start all services for Solidity Vuln Scanner

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting Solidity Vuln Scanner Services..."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo -e "${BLUE}📦 Activating virtual environment...${NC}"
    source venv/bin/activate
else
    echo -e "${YELLOW}⚠️  Virtual environment not found. Using system Python.${NC}"
fi

# Check Redis (optional for queue system)
if command -v redis-server &> /dev/null; then
    echo -e "${GREEN}✅ Redis detected${NC}"
    REDIS_RUNNING=$(pgrep -f redis-server || echo "")
    if [ -z "$REDIS_RUNNING" ]; then
        echo -e "${BLUE}🔄 Starting Redis...${NC}"
        redis-server --daemonize yes 2>/dev/null || echo "Redis already running or failed to start"
        sleep 1
    else
        echo -e "${GREEN}✅ Redis already running${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Redis not installed (optional for queue system)${NC}"
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down services...${NC}"
    kill $API_PID $UI_PID $CELERY_PID 2>/dev/null || true
    wait $API_PID $UI_PID $CELERY_PID 2>/dev/null || true
    echo -e "${GREEN}✅ Services stopped${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start FastAPI server
echo -e "${BLUE}🌐 Starting FastAPI server...${NC}"
python3 fastapi_api.py &
API_PID=$!
sleep 3

# Check if API started successfully
if ps -p $API_PID > /dev/null; then
    echo -e "${GREEN}✅ FastAPI server started (PID: $API_PID)${NC}"
    echo -e "   📍 API: http://localhost:8000"
    echo -e "   📚 Docs: http://localhost:8000/docs"
else
    echo -e "${YELLOW}⚠️  FastAPI server may have failed to start${NC}"
fi

# Start Streamlit UI
echo -e "${BLUE}🎨 Starting Streamlit UI...${NC}"
streamlit run streamlit_ui.py --server.port 8501 --server.headless true &
UI_PID=$!
sleep 3

if ps -p $UI_PID > /dev/null; then
    echo -e "${GREEN}✅ Streamlit UI started (PID: $UI_PID)${NC}"
    echo -e "   🌐 UI: http://localhost:8501"
else
    echo -e "${YELLOW}⚠️  Streamlit UI may have failed to start${NC}"
fi

# Start Celery worker (if Redis is available)
if command -v celery &> /dev/null && pgrep -f redis-server > /dev/null; then
    echo -e "${BLUE}⚙️  Starting Celery worker...${NC}"
    celery -A queue_system.celery_app worker --loglevel=info --logfile=celery.log &
    CELERY_PID=$!
    sleep 2
    if ps -p $CELERY_PID > /dev/null; then
        echo -e "${GREEN}✅ Celery worker started (PID: $CELERY_PID)${NC}"
    else
        echo -e "${YELLOW}⚠️  Celery worker may have failed to start${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Celery worker not started (Redis or Celery not available)${NC}"
    CELERY_PID=""
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ All services started!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}📍 Services:${NC}"
echo -e "   • API Server:    http://localhost:8000"
echo -e "   • API Docs:      http://localhost:8000/docs"
echo -e "   • Web UI:        http://localhost:8501"
echo -e "   • Metrics:       http://localhost:8000/metrics"
echo -e "   • Health Check:  http://localhost:8000/health"
echo ""
echo -e "${BLUE}📝 CLI Usage:${NC}"
echo -e "   python3 cli.py contract.sol --llm --format markdown"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Wait for all processes
wait
