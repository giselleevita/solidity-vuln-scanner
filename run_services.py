#!/usr/bin/env python3
"""
Service Manager - Start all services for Solidity Vuln Scanner
Runs API, UI, and optional services (Redis, Celery)
"""

import subprocess
import sys
import time
import signal
import os
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    RED = '\033[0;31m'
    NC = '\033[0m'  # No Color

def print_status(message, color=Colors.NC):
    print(f"{color}{message}{Colors.NC}")

def check_port(port):
    """Check if a port is in use"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0

def kill_process_on_port(port):
    """Kill process using a port"""
    try:
        if sys.platform == "darwin":  # macOS
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True,
                text=True
            )
            if result.stdout.strip():
                pid = result.stdout.strip().split('\n')[0]
                subprocess.run(["kill", "-9", pid], check=False)
                return True
    except:
        pass
    return False

def start_api():
    """Start FastAPI server"""
    print_status("🌐 Starting FastAPI server...", Colors.BLUE)
    
    if check_port(8000):
        print_status("⚠️  Port 8000 is in use, attempting to free it...", Colors.YELLOW)
        kill_process_on_port(8000)
        time.sleep(1)
    
    # Use venv if available
    python_cmd = "venv/bin/python3" if Path("venv/bin/python3").exists() else "python3"
    
    try:
        proc = subprocess.Popen(
            [python_cmd, "fastapi_api.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path.cwd()
        )
        time.sleep(3)
        
        # Check if it's still running
        if proc.poll() is None:
            print_status(f"✅ FastAPI server started (PID: {proc.pid})", Colors.GREEN)
            print_status("   📍 API: http://localhost:8000", Colors.BLUE)
            print_status("   📚 Docs: http://localhost:8000/docs", Colors.BLUE)
            return proc
        else:
            stdout, stderr = proc.communicate()
            print_status(f"❌ FastAPI failed to start", Colors.RED)
            if stderr:
                print(stderr.decode()[:500])
            return None
    except Exception as e:
        print_status(f"❌ Failed to start API: {e}", Colors.RED)
        return None

def start_ui():
    """Start Streamlit UI"""
    print_status("🎨 Starting Streamlit UI...", Colors.BLUE)
    
    if check_port(8501):
        print_status("⚠️  Port 8501 is in use, attempting to free it...", Colors.YELLOW)
        kill_process_on_port(8501)
        time.sleep(1)
    
    # Use venv if available
    streamlit_cmd = "venv/bin/streamlit" if Path("venv/bin/streamlit").exists() else "streamlit"
    
    try:
        proc = subprocess.Popen(
            [streamlit_cmd, "run", "streamlit_ui.py", 
             "--server.port", "8501", 
             "--server.headless", "true",
             "--server.address", "localhost"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path.cwd()
        )
        time.sleep(4)
        
        if proc.poll() is None:
            print_status(f"✅ Streamlit UI started (PID: {proc.pid})", Colors.GREEN)
            print_status("   🌐 UI: http://localhost:8501", Colors.BLUE)
            return proc
        else:
            stdout, stderr = proc.communicate()
            print_status(f"❌ Streamlit failed to start", Colors.RED)
            if stderr:
                print(stderr.decode()[:500])
            return None
    except Exception as e:
        print_status(f"❌ Failed to start UI: {e}", Colors.RED)
        return None

def start_celery():
    """Start Celery worker (if Redis available)"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        
        print_status("⚙️  Starting Celery worker...", Colors.BLUE)
        celery_cmd = "venv/bin/celery" if Path("venv/bin/celery").exists() else "celery"
        
        proc = subprocess.Popen(
            [celery_cmd, "-A", "queue_system.celery_app", "worker", 
             "--loglevel=info", "--logfile=celery.log"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path.cwd()
        )
        time.sleep(2)
        
        if proc.poll() is None:
            print_status(f"✅ Celery worker started (PID: {proc.pid})", Colors.GREEN)
            return proc
        else:
            return None
    except:
        print_status("⚠️  Celery worker not started (Redis not available)", Colors.YELLOW)
        return None

def main():
    """Main function to start all services"""
    print_status("═══════════════════════════════════════════════════════════", Colors.GREEN)
    print_status("🚀 Starting Solidity Vuln Scanner Services", Colors.GREEN)
    print_status("═══════════════════════════════════════════════════════════", Colors.GREEN)
    print()
    
    processes = []
    
    # Start API
    api_proc = start_api()
    if api_proc:
        processes.append(("API", api_proc))
    
    # Start UI
    ui_proc = start_ui()
    if ui_proc:
        processes.append(("UI", ui_proc))
    
    # Start Celery (optional)
    celery_proc = start_celery()
    if celery_proc:
        processes.append(("Celery", celery_proc))
    
    if not processes:
        print_status("❌ No services started successfully", Colors.RED)
        sys.exit(1)
    
    print()
    print_status("═══════════════════════════════════════════════════════════", Colors.GREEN)
    print_status("✅ Services Running!", Colors.GREEN)
    print_status("═══════════════════════════════════════════════════════════", Colors.GREEN)
    print()
    print_status("📍 Access Points:", Colors.BLUE)
    print_status("   • API Server:    http://localhost:8000", Colors.BLUE)
    print_status("   • API Docs:      http://localhost:8000/docs", Colors.BLUE)
    print_status("   • Web UI:        http://localhost:8501", Colors.BLUE)
    print_status("   • Metrics:       http://localhost:8000/metrics", Colors.BLUE)
    print_status("   • Health Check:  http://localhost:8000/health", Colors.BLUE)
    print()
    print_status("📝 CLI Usage:", Colors.BLUE)
    print_status("   python3 cli.py contract.sol --llm --format markdown", Colors.BLUE)
    print()
    print_status("Press Ctrl+C to stop all services", Colors.YELLOW)
    print()
    
    # Wait for processes
    try:
        while True:
            # Check if processes are still running
            for name, proc in processes[:]:
                if proc.poll() is not None:
                    print_status(f"⚠️  {name} process stopped", Colors.YELLOW)
                    processes.remove((name, proc))
            
            if not processes:
                print_status("❌ All processes stopped", Colors.RED)
                break
            
            time.sleep(1)
    except KeyboardInterrupt:
        print()
        print_status("🛑 Shutting down services...", Colors.YELLOW)
        for name, proc in processes:
            print_status(f"   Stopping {name}...", Colors.YELLOW)
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        print_status("✅ All services stopped", Colors.GREEN)

if __name__ == "__main__":
    main()
