# ✅ All Services Running!

## Current Status

**🌐 Streamlit UI**
- ✅ **Running** on http://localhost:8501
- Status: 200 OK
- PID: Saved in `ui.pid`

**📡 API Server**
- ✅ **Running** on http://localhost:8001
- Health: ✅ Healthy
- Version: 1.0.0
- PID: Saved in `api.pid`
- **Note**: Running on port 8001 (port 8000 is in use by another service)

---

## 📍 Access Points

- **API Server**: http://localhost:8001 ✅
- **API Documentation**: http://localhost:8001/docs ✅
- **Web UI**: http://localhost:8501 ✅
- **Metrics**: http://localhost:8001/metrics
- **Health Check**: http://localhost:8001/health ✅

---

## 🛑 Stop Services

```bash
# Stop all services
kill $(cat api.pid) $(cat ui.pid)

# Or individually
kill $(cat api.pid)  # Stop API
kill $(cat ui.pid)   # Stop UI
```

---

## 🔄 Restart Services

```bash
# Stop first
kill $(cat api.pid) $(cat ui.pid) 2>/dev/null

# Start API (port 8001)
nohup venv/bin/uvicorn fastapi_api:app --host 0.0.0.0 --port 8001 > api.log 2>&1 &
echo $! > api.pid

# Start UI
nohup venv/bin/streamlit run streamlit_ui.py --server.port 8501 --server.headless true > ui.log 2>&1 &
echo $! > ui.pid
```

---

## 📝 Quick Commands

### Check Status
```bash
# API health
curl http://localhost:8001/health

# UI status
curl -I http://localhost:8501
```

### View Logs
```bash
# API logs
tail -f api.log

# UI logs
tail -f ui.log
```

### Test API
```bash
# Analyze a contract
curl -X POST http://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "contract_code": "pragma solidity ^0.8.0; contract Test {}",
    "contract_name": "Test",
    "use_llm_audit": false
  }'
```

---

## ✅ All Services Ready!

Both API and UI are running and ready to use!
