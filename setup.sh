#!/bin/bash
# Quick setup script for Solidity Vuln Scanner

echo "🔐 Solidity Vuln Scanner - Setup"
echo "==========================================="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python $python_version detected"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file
echo ""
echo "⚙️  Setting up configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "📝 IMPORTANT: Edit .env and add your LLM_API_KEY"
    echo "   Get it from: https://platform.openai.com/api-keys"
else
    echo "✅ .env file already exists"
fi

# Create .gitignore
if [ ! -f .gitignore ]; then
    cp .gitignore .gitignore
    echo "✅ Created .gitignore"
fi

echo ""
echo "==========================================="
echo "✨ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your LLM_API_KEY"
echo "2. Run the API server:"
echo "   python fastapi_api.py"
echo ""
echo "3. In another terminal, run Streamlit UI:"
echo "   streamlit run streamlit_ui.py"
echo ""
echo "4. Open browser to http://localhost:8501"
echo ""
