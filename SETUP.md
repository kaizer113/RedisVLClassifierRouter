# Setup Guide

This guide will walk you through setting up the RedisVL Classifier Router project from scratch.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Install uv](#install-uv)
3. [Install Redis Stack](#install-redis-stack)
4. [Clone and Setup Project](#clone-and-setup-project)
5. [Configure API Keys](#configure-api-keys)
6. [Verify Installation](#verify-installation)
7. [Run Your First Classification](#run-your-first-classification)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

Before you begin, ensure you have:

- **Operating System**: macOS, Linux, or Windows with WSL2
- **Python**: Version 3.11 or higher
- **Internet Connection**: For downloading dependencies
- **OpenAI Account**: For API access (get one at [platform.openai.com](https://platform.openai.com))

## Install uv

`uv` is a fast Python package manager that we use for dependency management.

### macOS / Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows (PowerShell)

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Alternative: Install with pip

```bash
pip install uv
```

### Verify Installation

```bash
uv --version
# Should output: uv 0.x.x
```

## Install Redis Stack

Redis Stack includes RedisSearch with vector similarity support, which is required for this project.

### macOS

```bash
# Install via Homebrew
brew tap redis-stack/redis-stack
brew install redis-stack

# Start Redis Stack
redis-stack-server
```

To run Redis Stack in the background:
```bash
brew services start redis-stack
```

### Linux (Ubuntu/Debian)

```bash
# Add Redis repository
curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg

echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list

# Install Redis Stack
sudo apt-get update
sudo apt-get install redis-stack-server

# Start Redis Stack
redis-stack-server
```

To run as a service:
```bash
sudo systemctl start redis-stack-server
sudo systemctl enable redis-stack-server
```

### Docker (All Platforms)

```bash
# Run Redis Stack in Docker
docker run -d \
  --name redis-stack \
  -p 6379:6379 \
  -p 8001:8001 \
  redis/redis-stack:latest
```

The container includes:
- Redis on port 6379
- RedisInsight (web UI) on port 8001

### Verify Redis Installation

```bash
# Test connection
redis-cli ping
# Should return: PONG

# Check Redis Stack modules
redis-cli MODULE LIST
# Should show: search, json, timeseries, bloom, graph
```

## Clone and Setup Project

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/RedisVLClassifierRouter.git
cd RedisVLClassifierRouter
```

### 2. Create Virtual Environment and Install Dependencies

```bash
# This creates a .venv directory and installs all dependencies
uv sync
```

This command:
- Creates a virtual environment in `.venv/`
- Installs all dependencies from `pyproject.toml`
- Locks versions in `uv.lock`

### 3. Activate Virtual Environment

**macOS / Linux:**
```bash
source .venv/bin/activate
```

**Windows:**
```bash
.venv\Scripts\activate
```

You should see `(.venv)` in your terminal prompt.

### 4. Verify Python Environment

```bash
python --version
# Should show: Python 3.11.x or higher

which python
# Should point to: /path/to/project/.venv/bin/python
```

## Configure API Keys

### 1. Get OpenAI API Key

1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)

### 2. Create config.py

```bash
# Copy the example config
cp config.example.py config.py
```

### 3. Edit config.py

Open `config.py` in your editor and replace the placeholder:

```python
# config.py
OPENAI_API_KEY = "sk-your-actual-api-key-here"
```

**⚠️ IMPORTANT:** Never commit `config.py` to Git! It's already in `.gitignore`.

## Verify Installation

### 1. Check All Dependencies

```bash
uv pip list
```

You should see:
- `openai`
- `redisvl`
- `sentence-transformers`
- `redis-retrieval-optimizer`
- `numpy`
- And their dependencies

### 2. Test Redis Connection

```bash
python -c "import redis; r = redis.Redis(host='localhost', port=6379); print(r.ping())"
# Should print: True
```

### 3. Test OpenAI Connection

```bash
python -c "from openai import OpenAI; from config import OPENAI_API_KEY; client = OpenAI(api_key=OPENAI_API_KEY); print('OpenAI client initialized successfully')"
```

### 4. Test RedisVL

```bash
python -c "from redisvl.extensions.router import SemanticRouter; print('RedisVL imported successfully')"
```

## Run Your First Classification

Now you're ready to run the scripts!

### Quick Test (Recommended)

Start with the optimized router script:

```bash
python 4_RedisVLRouterWithOptimizer.py
```

This will:
1. Load reference articles (300 per category)
2. Create semantic routes
3. Optimize thresholds automatically
4. Classify test articles
5. Show accuracy and performance metrics

Expected runtime: 3-5 minutes

### Try Other Scripts

```bash
# Baseline with pure GPT-4
python 1_baseline_with_openai.py

# RedisVL router only
python 2_RedisVLRouter.py

# Hybrid approach
python 3_RedisVLRouterwithChatGPT.py
```

## Troubleshooting

### Redis Connection Error

**Error:** `redis.exceptions.ConnectionError: Error 61 connecting to localhost:6379`

**Solution:**
```bash
# Check if Redis is running
redis-cli ping

# If not running, start it
redis-stack-server
# or
brew services start redis-stack
```

### OpenAI API Error

**Error:** `openai.AuthenticationError: Incorrect API key provided`

**Solution:**
1. Check your API key in `config.py`
2. Verify it starts with `sk-`
3. Make sure there are no extra spaces
4. Generate a new key if needed

### Module Not Found Error

**Error:** `ModuleNotFoundError: No module named 'redisvl'`

**Solution:**
```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
uv sync

# Verify installation
uv pip list | grep redisvl
```

### Python Version Error

**Error:** `This project requires Python >=3.11`

**Solution:**
```bash
# Check Python version
python --version

# Install Python 3.11+ if needed
# macOS:
brew install python@3.11

# Linux:
sudo apt-get install python3.11

# Then recreate virtual environment
rm -rf .venv
uv sync
```

### Out of Memory Error

**Error:** `RuntimeError: CUDA out of memory` or similar

**Solution:**
- Reduce `num_per_category` in the scripts (e.g., from 300 to 100)
- Reduce `num_articles` for testing (e.g., from 200 to 50)
- Close other applications to free up RAM

### Slow Performance

**Issue:** Scripts taking too long to run

**Solutions:**
1. **Reduce dataset size:**
   ```python
   # In the script, change:
   num_per_category=100  # Instead of 300
   num_articles=50       # Instead of 200
   ```

2. **Use CPU instead of GPU:**
   ```bash
   export CUDA_VISIBLE_DEVICES=""
   ```

3. **Check Redis performance:**
   ```bash
   redis-cli INFO stats
   ```

## Next Steps

Once everything is working:

1. **Read the documentation:**
   - [README.md](README.md) - Main documentation
   - [README_OPTIMIZER.md](README_OPTIMIZER.md) - Threshold optimization guide

2. **Experiment with parameters:**
   - Try different `distance_threshold` values
   - Test different `eval_metric` options (f1, precision, recall)
   - Adjust `max_iterations` for optimization

3. **Use your own data:**
   - Replace the BBC News CSV files with your own dataset
   - Update the `CATEGORIES` list in the scripts
   - Adjust the data loading functions

4. **Contribute:**
   - See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines
   - Report issues on GitHub
   - Submit pull requests with improvements

## Getting Help

- **Issues:** [GitHub Issues](https://github.com/yourusername/RedisVLClassifierRouter/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/RedisVLClassifierRouter/discussions)
- **Redis Documentation:** [redis.io/docs](https://redis.io/docs)
- **RedisVL Documentation:** [redisvl.com](https://redisvl.com)

---

**Happy Coding! 🚀**

