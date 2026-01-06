# Docker Guide

## Overview

Docker provides a consistent, isolated environment for running the scanner and all its dependencies (including Slither and Mythril) without local installation.

## Prerequisites

- **Docker Desktop** installed and running
- **~2GB** free disk space for images

## Quick Start

### Start Everything

```bash
docker-compose up --build
```

This will:
- Build Docker images for API, UI, and tools (Slither/Mythril)
- Start all services
- Make UI available at http://localhost:8501
- Make API available at http://localhost:8000

### Start in Background

```bash
docker-compose up -d --build
```

### Stop Everything

```bash
docker-compose down
```

## Docker Architecture

The project uses three Docker images:

1. **Main Application** (`Dockerfile`)
   - FastAPI backend
   - Streamlit UI
   - Python dependencies

2. **Slither** (`Dockerfile.slither`)
   - Static analysis tool
   - Runs on-demand via Docker

3. **Mythril** (`Dockerfile.mythril`)
   - Symbolic execution tool
   - Runs on-demand via Docker

## Common Commands

```bash
# View logs
docker-compose logs
docker-compose logs api      # Specific service
docker-compose logs -f       # Follow logs

# Check status
docker-compose ps

# Restart services
docker-compose restart
docker-compose restart api   # Specific service

# Rebuild after code changes
docker-compose up --build

# Stop and remove volumes
docker-compose down -v
```

## Why Docker?

### Benefits

✅ **No Local Installation** - Slither/Mythril run in containers  
✅ **Consistent Environment** - Same setup everywhere  
✅ **Isolated Dependencies** - No conflicts with system packages  
✅ **Production Ready** - Easy to deploy  

### When to Use Docker

- **Production deployments**
- **CI/CD pipelines**
- **When local tool installation is problematic**
- **Team environments** (consistent setup)

### When to Use Local Development

- **Faster iteration** during development
- **Easier debugging** (direct access to logs)
- **No Docker overhead**

## Troubleshooting

### Docker Desktop Not Running

**Symptoms:** `Cannot connect to Docker daemon`

**Solution:**
1. Start Docker Desktop application
2. Wait for whale icon 🐳 in menu bar to be steady
3. Verify: `docker ps` should show containers or empty list (not error)

**Alternative:** Use local development (see [INSTALL.md](INSTALL.md))

### Docker Timeout Error

**Symptoms:** `Docker daemon is not responding`

**Solution:**
1. Quit Docker Desktop completely
2. Wait 10 seconds
3. Restart: `open -a Docker` (macOS) or start Docker Desktop
4. Wait 30-60 seconds for full startup
5. Verify: `docker ps`
6. Try again: `docker-compose up --build`

**Alternative:** Use local development instead

### Port Already in Use

**Symptoms:** `Address already in use` on ports 8000 or 8501

**Solution:**
```bash
# Kill processes on ports
lsof -ti:8501 | xargs kill -9
lsof -ti:8000 | xargs kill -9

# Stop Docker containers
docker-compose down

# Start again
docker-compose up --build
```

**Alternative:** Change ports in `docker-compose.yml`:
```yaml
ports:
  - "8502:8501"  # Use 8502 instead
  - "8001:8000"  # Use 8001 instead
```

### Build Failures

**Symptoms:** `ERROR: failed to build`

**Solution:**
```bash
# Clean build
docker-compose down -v
docker system prune -f
docker-compose up --build
```

### Tools Not Available

**Symptoms:** Slither/Mythril show as "not installed" in UI

**Solution:**
- Tools run in separate containers
- Ensure `docker-compose.yml` includes tool services
- Check logs: `docker-compose logs`

## Local vs Docker Comparison

| Feature | Local | Docker |
|---------|-------|--------|
| Setup Speed | Fast | Slower (first build) |
| Startup Time | Instant | ~10-30 seconds |
| Tool Installation | Manual | Automatic |
| Debugging | Easy | Requires `docker-compose logs` |
| Consistency | Varies | Same everywhere |
| Production | Manual setup | Containerized |

## Next Steps

- **Installation**: See [INSTALL.md](INSTALL.md)
- **Usage**: See [USAGE.md](USAGE.md)
- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md)
