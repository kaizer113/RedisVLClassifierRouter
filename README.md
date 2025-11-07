# RedisVL Classifier Router

A comprehensive comparison of different approaches to text classification using BBC News articles, featuring RedisVL SemanticRouter with automatic threshold optimization.

## 🎯 Project Overview

This project demonstrates and compares multiple approaches to text classification:

1. **Baseline with OpenAI** - Pure GPT-4 classification
2. **RedisVL SemanticRouter** - Fast, local vector-based routing
3. **Hybrid Approach** - RedisVL with ChatGPT fallback
4. **Optimized Router** - Automatic threshold optimization using `redis-retrieval-optimizer`

### Key Features

- 📊 **BBC News Dataset**: 5 categories (business, tech, sport, politics, entertainment)
- 🚀 **Fast Classification**: Vector-based semantic routing with Redis
- 🤖 **AI Fallback**: ChatGPT integration for unknown cases
- 🎛️ **Auto-Optimization**: Automatic threshold tuning per category
- 📈 **Performance Metrics**: Accuracy, latency (P95/P99), and cost analysis

## 📋 Prerequisites

- **Python 3.11+**
- **Redis Stack** (with RedisSearch and vector similarity)
- **OpenAI API Key**
- **uv** (Python package manager)

## 🚀 Quick Start

### 1. Install uv

If you don't have `uv` installed:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

### 2. Install Redis Stack

**macOS:**
```bash
brew tap redis-stack/redis-stack
brew install redis-stack
redis-stack-server
```

**Linux:**
```bash
curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list
sudo apt-get update
sudo apt-get install redis-stack-server
redis-stack-server
```

**Docker:**
```bash
docker run -d --name redis-stack -p 6379:6379 redis/redis-stack:latest
```

### 3. Clone and Setup Project

```bash
# Clone the repository
git clone https://github.com/yourusername/RedisVLClassifierRouter.git
cd RedisVLClassifierRouter

# Create virtual environment and install dependencies with uv
uv sync
```

**Note:** With `uv run`, you don't need to manually activate the virtual environment! The `uv run` command automatically uses the project's `.venv`.

### 4. Configure API Keys

Create a `config.py` file with your OpenAI API key:

```python
# config.py
OPENAI_API_KEY = "your-openai-api-key-here"
```

**⚠️ Important:** Never commit your API keys to Git! The `config.py` file is already in `.gitignore`.

### 5. Verify Setup

```bash
# Check Redis is running
redis-cli ping
# Should return: PONG

# Check Python environment
uv run python --version
# Should show: Python 3.11.x or higher
```

## 📚 Dataset

The project uses the BBC News dataset with three CSV files:

- `BBC News Train2.csv` - Reference articles for building the router (1500+ articles)
- `BBC News Train.csv` - Test articles for evaluation (1000+ articles)
- `BBC News Test.csv` - Additional test set

Each article has:
- `ArticleId` - Unique identifier
- `Text` - Article content
- `Category` - One of: business, tech, sport, politics, entertainment

## 🎮 Running the Scripts

### Script 1: Baseline with OpenAI

Pure GPT-4 classification without any caching or optimization.

```bash
uv run python 1_baseline_with_openai.py
```

**What it does:**
- Classifies articles using GPT-4-turbo
- Measures accuracy, latency, and cost
- Provides baseline metrics for comparison

**Expected output:**
- Accuracy: ~95%
- Average latency: ~1-2s per article
- Cost: ~$0.001-0.002 per article

### Script 2: RedisVL Router

Fast vector-based classification using RedisVL SemanticRouter.

```bash
uv run python 2_RedisVLRouter.py
```

**What it does:**
- Creates semantic routes for each category
- Uses 300 reference articles per category
- Classifies using vector similarity (COSINE distance)
- Returns "unknown" if no match within threshold

**Expected output:**
- Accuracy: ~85-90% (on matched articles)
- Average latency: ~0.05-0.1s per article
- Cost: $0 (local processing)
- Router match rate: ~70-80%

### Script 3: Hybrid Approach

Combines RedisVL router with ChatGPT fallback for unknown cases.

```bash
uv run python 3_RedisVLRouterwithChatGPT.py
```

**What it does:**
- First attempts classification with RedisVL router
- Falls back to ChatGPT for "unknown" results
- Adds ChatGPT-classified articles back to router as new references
- Learns and improves over time

**Expected output:**
- Accuracy: ~95% (same as baseline)
- Average latency: ~0.2-0.5s per article (mixed)
- Cost: ~$0.0005 per article (50% reduction)
- Router match rate: ~70-80% initially, improves over time

### Script 4: Optimized Router (Recommended)

Uses automatic threshold optimization for best performance.

```bash
uv run python 4_RedisVLRouterWithOptimizer.py
```

**What it does:**
- Creates routes with initial threshold (0.5)
- Runs `RouterThresholdOptimizer` on 100 validation articles
- Finds optimal threshold for each category independently
- Evaluates on full test set with optimized thresholds

**Expected output:**
```
Step 6: Running threshold optimization...
  Initial thresholds: {'business': 0.5, 'tech': 0.5, 'sport': 0.5, ...}

Eval metric PRECISION: start 0.850, end 0.923
Ending thresholds: {'business': 0.45, 'tech': 0.52, 'sport': 0.38, ...}

  Optimized thresholds: {'business': 0.45, 'tech': 0.52, 'sport': 0.38, ...}

SUMMARY STATISTICS
==================
Optimized Thresholds by Route:
  business: 0.4500
  tech: 0.5200
  sport: 0.3800
  politics: 0.4800
  entertainment: 0.4200

Accuracy: 185/200 (92.5%)
Router Matches: 165/200 (82.5%)
ChatGPT Fallbacks: 35/200 (17.5%)
```

**Benefits:**
- Higher accuracy than manual threshold tuning
- Per-category optimization (some categories need stricter/looser matching)
- Automated - no trial and error needed
- Data-driven based on validation set performance

## 🔧 Configuration Options

### Threshold Optimization Parameters

In `4_RedisVLRouterWithOptimizer.py`, you can adjust:

```python
optimizer = RouterThresholdOptimizer(
    router=router,
    test_dict=optimizer_test_data,
    eval_metric="precision"  # Options: "f1", "precision", "recall"
)

optimizer.optimize(
    max_iterations=20,  # More iterations = better optimization (slower)
    search_step=0.20    # Search range: ±0.20 around current threshold
)
```

**Evaluation Metrics:**
- `"f1"` - Balance between precision and recall (default)
- `"precision"` - Minimize false positives (incorrect matches)
- `"recall"` - Minimize false negatives (missed matches)

### Router Configuration

```python
# Number of reference articles per category
num_per_category = 300  # More = better accuracy, slower indexing

# Number of test articles
num_articles = 200  # Adjust based on your needs

# Distance aggregation method
RoutingConfig(aggregation_method=DistanceAggregationMethod.min)
# Options: min (recommended), avg, sum
```

### Distance Threshold Constraints

- **Range**: 0 < threshold ≤ 2.0 (for COSINE distance)
- **Lower values** (0.3-0.5): Stricter matching, fewer false positives
- **Higher values** (0.6-0.8): More lenient, fewer false negatives
- **Optimal**: Usually 0.4-0.6, varies by category

## 📊 Performance Comparison

| Approach | Accuracy | Avg Latency | Cost/Article | Router Rate |
|----------|----------|-------------|--------------|-------------|
| Baseline (GPT-4) | ~95% | 1-2s | $0.001-0.002 | N/A |
| RedisVL Router | ~85-90%* | 0.05-0.1s | $0 | 70-80% |
| Hybrid | ~95% | 0.2-0.5s | ~$0.0005 | 70-80% |
| Optimized | ~92-95% | 0.1-0.3s | ~$0.0003 | 80-90% |

*On matched articles only (excludes "unknown" results)

## 🏗️ Project Structure

```
RedisVLClassifierRouter/
├── 1_baseline_with_openai.py          # Pure GPT-4 classification
├── 2_RedisVLRouter.py                 # RedisVL semantic router
├── 3_RedisVLRouterwithChatGPT.py      # Hybrid approach
├── 4_RedisVLRouterWithOptimizer.py    # Optimized router (recommended)
├── config.py                          # API keys (create this)
├── pyproject.toml                     # Project dependencies
├── uv.lock                            # Locked dependencies
├── README.md                          # This file
├── README_OPTIMIZER.md                # Detailed optimizer documentation
├── BBC News Train2.csv                # Reference articles
├── BBC News Train.csv                 # Test articles
└── BBC News Test.csv                  # Additional test set
```

## 🧪 Testing Distance Thresholds

To experiment with different thresholds:

```bash
uv run python test_distance_threshold.py
```

This script tests multiple threshold values and shows which queries match at each level.

## 📖 Additional Documentation

- **[README_OPTIMIZER.md](README_OPTIMIZER.md)** - Detailed guide on threshold optimization
- **[RedisVL Documentation](https://redisvl.com)** - Official RedisVL docs
- **[redis-retrieval-optimizer](https://pypi.org/project/redis-retrieval-optimizer/)** - Optimizer package docs

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **RedisVL** - Vector library for Redis
- **OpenAI** - GPT models for classification
- **BBC News Dataset** - Training and test data
- **redis-retrieval-optimizer** - Automatic threshold optimization

## 📧 Contact

For questions or issues, please open an issue on GitHub.

---

**Happy Classifying! 🚀**
