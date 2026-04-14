#!/bin/bash
# Installation script for external security tools (Slither, Mythril)

echo "🔧 Installing External Security Tools"
echo "======================================"
echo ""

# Check if Python/pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 not found. Please install Python 3 first."
    exit 1
fi

# Install Slither
echo "📦 Installing Slither..."
if pip3 install slither-analyzer 2>/dev/null; then
    echo "✅ Slither installed successfully"
    slither --version 2>/dev/null || echo "   (Note: Verify installation with 'slither --version')"
else
    echo "⚠️  Slither installation failed. You may need to install dependencies:"
    echo "   sudo apt-get install python3-pip python3-dev"
    echo "   OR on macOS: brew install python3"
fi

echo ""

# Install Mythril
echo "📦 Installing Mythril..."
if pip3 install mythril 2>/dev/null; then
    echo "✅ Mythril installed successfully"
    myth version 2>/dev/null || echo "   (Note: Verify installation with 'myth version')"
else
    echo "⚠️  Mythril installation failed."
    echo "   Alternative: brew install mythril (macOS)"
fi

echo ""
echo "======================================"
echo "✅ Installation complete!"
echo ""
echo "Verify installation:"
echo "  slither --version"
echo "  myth version"
echo ""
echo "If tools are not found, you may need to add them to your PATH."

