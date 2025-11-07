#!/bin/bash
# Quick start script for RedisVL Classifier Router

set -e  # Exit on error

echo "=================================="
echo "RedisVL Classifier Router Setup"
echo "=================================="
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed"
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "✅ uv installed successfully"
    echo "Please restart your terminal and run this script again"
    exit 0
fi

echo "✅ uv is installed"

# Check if Redis is running
if ! redis-cli ping &> /dev/null; then
    echo "❌ Redis is not running"
    echo ""
    echo "Please start Redis Stack:"
    echo "  macOS: brew services start redis-stack"
    echo "  Linux: sudo systemctl start redis-stack-server"
    echo "  Docker: docker run -d -p 6379:6379 redis/redis-stack:latest"
    exit 1
fi

echo "✅ Redis is running"

# Create virtual environment and install dependencies
echo ""
echo "Installing dependencies..."
uv sync

echo "✅ Dependencies installed"

# Check if config.py exists
if [ ! -f "config.py" ]; then
    echo ""
    echo "⚠️  config.py not found"
    echo "Creating config.py from template..."
    cp config.example.py config.py
    echo ""
    echo "📝 Please edit config.py and add your OpenAI API key"
    echo "   Get your key from: https://platform.openai.com/api-keys"
    echo ""
    echo "After adding your API key, run:"
    echo "  source .venv/bin/activate"
    echo "  python 4_RedisVLRouterWithOptimizer.py"
    exit 0
fi

echo "✅ config.py exists"

# Run a quick test using uv run
echo ""
echo "Running quick verification..."

uv run python -c "
from config import OPENAI_API_KEY
if OPENAI_API_KEY == 'your-openai-api-key-here':
    print('❌ Please update config.py with your actual OpenAI API key')
    exit(1)
print('✅ Configuration looks good')
"

if [ $? -ne 0 ]; then
    echo ""
    echo "Please edit config.py and add your OpenAI API key"
    exit 1
fi

echo ""
echo "=================================="
echo "✅ Setup Complete!"
echo "=================================="
echo ""
echo "To get started, run the optimized classifier:"
echo "  uv run python 4_RedisVLRouterWithOptimizer.py"
echo ""
echo "Or try other scripts:"
echo "  uv run python 1_baseline_with_openai.py"
echo "  uv run python 2_RedisVLRouter.py"
echo "  uv run python 3_RedisVLRouterwithChatGPT.py"
echo ""
echo "Note: 'uv run' automatically uses the virtual environment,"
echo "      so you don't need to activate it manually!"
echo ""
echo "For more information, see README.md"
echo ""

