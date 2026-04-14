"""
Optional integrations with external security tools (Slither, Mythril).
Supports both local installation and Docker containers.

Installation Options:
1. Local: pip install slither-analyzer mythril
2. Docker: Use docker-compose (recommended for production)
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Tuple

# Check if Docker is available
def _docker_available() -> bool:
    """Check if Docker is available"""
    try:
        result = subprocess.run(
            ["docker", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=2
        )
        return result.returncode == 0
    except:
        return False

DOCKER_AVAILABLE = _docker_available()


def _run_cmd(cmd: list[str], timeout: int = 30) -> Tuple[bool, str]:
    """Run a command and capture stdout/stderr."""
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        output = proc.stdout.strip() if proc.stdout else ""
        return proc.returncode == 0, output or "No output"
    except FileNotFoundError:
        return False, "Tool not found on PATH. Please install it first."
    except subprocess.TimeoutExpired:
        return False, f"Analysis timed out after {timeout} seconds"
    except Exception as e:
        return False, f"Error: {str(e)}"


def check_slither_installed() -> Tuple[bool, str]:
    """Check if Slither is installed (local or Docker) and return status message."""
    # Check local installation
    if shutil.which("slither"):
        try:
            proc = subprocess.run(
                ["slither", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,
                text=True
            )
            version = proc.stdout.strip() or "installed"
            return True, f"Slither {version} (local)"
        except:
            return True, "Slither is installed (local)"
    
    # Check Docker availability
    if DOCKER_AVAILABLE:
        return True, "Slither available via Docker (use docker-compose)"
    
    return False, "Slither not installed. Options: pip install slither-analyzer OR use Docker"


def check_mythril_installed() -> Tuple[bool, str]:
    """Check if Mythril is installed (local or Docker) and return status message."""
    # Check local installation
    if shutil.which("myth"):
        try:
            proc = subprocess.run(
                ["myth", "version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,
                text=True
            )
            version = proc.stdout.strip() or "installed"
            return True, f"Mythril {version} (local)"
        except:
            return True, "Mythril is installed (local)"
    
    # Check Docker availability
    if DOCKER_AVAILABLE:
        return True, "Mythril available via Docker (use docker-compose)"
    
    return False, "Mythril not installed. Options: pip install mythril OR use Docker"


def run_slither(contract_code: str, filename: str = "Contract.sol", timeout: int = 45, use_docker: bool = None) -> Tuple[bool, str]:
    """
    Run Slither against provided Solidity code.
    Supports both local installation and Docker container.
    
    Args:
        contract_code: Solidity source code
        filename: Name for the contract file
        timeout: Analysis timeout in seconds
        use_docker: Force Docker usage (None = auto-detect)
    
    Returns:
        (success, output) tuple
    """
    # Auto-detect: prefer Docker if available, fallback to local
    if use_docker is None:
        use_docker = DOCKER_AVAILABLE and not shutil.which("slither")
    
    # Try Docker first if enabled
    if use_docker and DOCKER_AVAILABLE:
        return _run_slither_docker(contract_code, filename, timeout)
    
    # Fallback to local installation
    if not shutil.which("slither"):
        if DOCKER_AVAILABLE:
            return _run_slither_docker(contract_code, filename, timeout)
        return False, "❌ Slither not installed.\n\nInstallation options:\n  1. Local: pip install slither-analyzer\n  2. Docker: docker-compose up (recommended)\n\nOr visit: https://github.com/crytic/slither"

    from input_validator import sanitize_filename
    
    # Sanitize filename
    safe_filename = sanitize_filename(filename)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            path = Path(tmpdir) / safe_filename
            path.write_text(contract_code, encoding='utf-8')
            
            # Run slither with JSON output for better parsing
            result = _run_cmd(
                ["slither", str(path), "--json", "-"],
                timeout=timeout
            )
            
            if not result[0]:
                # Try without JSON if that fails
                result = _run_cmd(["slither", str(path)], timeout=timeout)
            
            return result
        except Exception as e:
            return False, f"Error running Slither: {str(e)}"


def _run_slither_docker(contract_code: str, filename: str, timeout: int) -> Tuple[bool, str]:
    """Run Slither using Docker container with secure file handling"""
    from input_validator import sanitize_filename
    
    # Sanitize filename to prevent path traversal and command injection
    safe_filename = sanitize_filename(filename)
    
    # Use secure temporary directory (auto-cleans up)
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write to secure temporary file
            temp_path = os.path.join(tmpdir, safe_filename)
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(contract_code)
            
            # Build Docker image if needed
            docker_image = "slither-scanner:latest"
            build_cmd = [
                "docker", "build", "-f", "Dockerfile.slither", 
                "-t", docker_image, "."
            ]
            subprocess.run(build_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
            
            # Run Slither in container with sanitized path
            # Use absolute path to prevent traversal
            container_path = f"/tmp/{safe_filename}"
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{temp_path}:{container_path}:ro",  # Read-only mount
                docker_image,
                container_path, "--json", "-"
            ]
            
            result = _run_cmd(cmd, timeout=timeout)
            if not result[0]:
                # Try without JSON
                cmd[-2:] = [container_path]
                result = _run_cmd(cmd, timeout=timeout)
            
            return result
            # Temporary directory auto-cleans up here
    except Exception as e:
        return False, f"Docker error: {str(e)}. Try local installation: pip install slither-analyzer"


def run_mythril(contract_code: str, filename: str = "Contract.sol", timeout: int = 90, use_docker: bool = None) -> Tuple[bool, str]:
    """
    Run Mythril against provided Solidity code.
    Supports both local installation and Docker container.
    
    Args:
        contract_code: Solidity source code
        filename: Name for the contract file
        timeout: Analysis timeout in seconds
        use_docker: Force Docker usage (None = auto-detect)
    
    Returns:
        (success, output) tuple
    """
    # Auto-detect: prefer Docker if available, fallback to local
    if use_docker is None:
        use_docker = DOCKER_AVAILABLE and not shutil.which("myth")
    
    # Try Docker first if enabled
    if use_docker and DOCKER_AVAILABLE:
        return _run_mythril_docker(contract_code, filename, timeout)
    
    # Fallback to local installation
    if not shutil.which("myth"):
        if DOCKER_AVAILABLE:
            return _run_mythril_docker(contract_code, filename, timeout)
        return False, "❌ Mythril not installed.\n\nInstallation options:\n  1. Local: pip install mythril\n  2. Docker: docker-compose up (recommended)\n\nOr visit: https://github.com/Consensys/mythril"

    from input_validator import sanitize_filename
    
    # Sanitize filename
    safe_filename = sanitize_filename(filename)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            path = Path(tmpdir) / safe_filename
            path.write_text(contract_code, encoding='utf-8')
            
            # Mythril analyze command
            result = _run_cmd(
                ["myth", "analyze", str(path), "--execution-timeout", "60", "--max-depth", "10"],
                timeout=timeout
            )
            
            return result
        except Exception as e:
            return False, f"Error running Mythril: {str(e)}"


def _run_mythril_docker(contract_code: str, filename: str, timeout: int) -> Tuple[bool, str]:
    """Run Mythril using Docker container with secure file handling"""
    from input_validator import sanitize_filename
    
    # Sanitize filename to prevent path traversal and command injection
    safe_filename = sanitize_filename(filename)
    
    # Use secure temporary directory (auto-cleans up)
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write to secure temporary file
            temp_path = os.path.join(tmpdir, safe_filename)
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(contract_code)
            
            # Build Docker image if needed
            docker_image = "mythril-scanner:latest"
            build_cmd = [
                "docker", "build", "-f", "Dockerfile.mythril",
                "-t", docker_image, "."
            ]
            subprocess.run(build_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
            
            # Run Mythril in container with sanitized path
            container_path = f"/tmp/{safe_filename}"
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{temp_path}:{container_path}:ro",  # Read-only mount
                docker_image,
                "analyze", container_path, "--execution-timeout", "60", "--max-depth", "10"
            ]
            
            return _run_cmd(cmd, timeout=timeout)
            # Temporary directory auto-cleans up here
    except Exception as e:
        return False, f"Docker error: {str(e)}. Try local installation: pip install mythril"

