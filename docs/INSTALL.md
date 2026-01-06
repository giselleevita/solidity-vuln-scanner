# Installation Guide

## Prerequisites

- **Python 3.10+** (3.11 recommended)
- **Git**
- **~500MB** free disk space
- (Optional) **OpenAI API Key** or **Claude API Key** for AI features
- (Optional) **Docker Desktop** for containerized deployment

## Quick Installation

### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/solidity-vuln-scanner.git
cd solidity-vuln-scanner

# Run setup script
chmod +x setup.sh
./setup.sh
```

### Option 2: Manual Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
```

### Option 3: Using Makefile

```bash
make install
```

## Configuration

### Free Mode (Static Analysis Only)

Edit `.env`:
```env
USE_LLM=false
```

No API key needed - works immediately!

### Full Mode (Static + AI Analysis)

Edit `.env`:
```env
USE_LLM=true
LLM_PROVIDER=openai  # or "anthropic"
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini  # or "claude-3-sonnet-20240229"
```

## Verify Installation

```bash
python verify_setup.py
```

You should see: ✅ All checks passed!

## Optional: Install External Tools

For cross-validation with Slither and Mythril:

### Local Installation

```bash
pip install slither-analyzer mythril
```

### Docker (Recommended)

No installation needed - tools run in containers. See [DOCKER.md](DOCKER.md).

## Next Steps

- **Quick Start**: See [README.md](../README.md#-quick-start)
- **Usage Examples**: See [USAGE.md](USAGE.md)
- **Docker Setup**: See [DOCKER.md](DOCKER.md)
