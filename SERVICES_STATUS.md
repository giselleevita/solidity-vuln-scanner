# 🚀 Services Status

## ✅ All Services Running!

### Current Status

**🌐 Streamlit UI**
- **Status**: ✅ Running
- **URL**: http://localhost:8501
- **PID**: Saved in `ui.pid`

**📡 API Server**
- **Status**: ✅ Running
- **URL**: http://localhost:8001
- **PID**: Saved in `api.pid`
- **Note**: Running on port 8001 (port 8000 is in use by another service)

---

## 📍 Access Points

- **API Server**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **Web UI**: http://localhost:8501
- **Metrics**: http://localhost:8001/metrics
- **Health Check**: http://localhost:8001/health

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
API_PORT=8001 venv/bin/python3 -c "import uvicorn; from fastapi_api import app; uvicorn.run(app, host='0.0.0.0', port=8001)" > api.log 2>&1 &
echo $! > api.pid

# Start UI
venv/bin/streamlit run streamlit_ui.py --server.port 8501 --server.headless true > ui.log 2>&1 &
echo $! > ui.pid
```

---

## 📝 Notes

- Port 8000 is in use by another service (AegisAIS)
- API is running on port 8001 to avoid conflicts
- Update `API_URL` in `.env` or `streamlit_ui.py` if you want UI to connect to port 8001
- All services are running in background
- Logs are in `api.log` and `ui.log`

---

## ✅ Services Ready!

All services are running and ready to use!
