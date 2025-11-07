# RedisVL Router with Threshold Optimization

This script demonstrates how to use the `RouterThresholdOptimizer` from the `redis-retrieval-optimizer` package to automatically find optimal distance thresholds for a RedisVL SemanticRouter.

## What is Threshold Optimization?

When using a SemanticRouter for classification, each route has a `distance_threshold` parameter that determines how similar a query must be to match that route. Finding the right threshold is crucial:

- **Too low (strict)**: You'll get many "unknown" results (false negatives)
- **Too high (lenient)**: You'll get incorrect matches (false positives)

The `RouterThresholdOptimizer` automatically finds the best threshold for each route by:
1. Testing different threshold values
2. Evaluating performance using metrics like F1 score, precision, or recall
3. Selecting the thresholds that maximize the chosen metric

## How It Works

### 1. Setup Phase
```python
# Create routes with initial thresholds
routes = create_routes(references_by_category, distance_threshold=0.5)

# Initialize router
router = SemanticRouter(
    name="news-classifier",
    vectorizer=HFTextVectorizer(),
    routes=routes,
    redis_url="redis://localhost:6379"
)
```

### 2. Prepare Test Data
The optimizer requires test data in a specific format:
```python
test_data = [
    {"query": "article text...", "query_match": "business"},
    {"query": "article text...", "query_match": "tech"},
    ...
]
```

Each entry has:
- `query`: The text to classify
- `query_match`: The expected route name (ground truth)

### 3. Run Optimization
```python
optimizer = RouterThresholdOptimizer(
    router=router,
    test_dict=test_data,
    eval_metric="f1"  # Can also use "precision" or "recall"
)

optimizer.optimize(
    max_iterations=20,  # Number of random search iterations
    search_step=0.10    # Search range around current threshold (±0.10)
)
```

### 4. Results
After optimization, each route will have its own optimized threshold:
```python
print(router.route_thresholds)
# Output: {'business': 0.45, 'tech': 0.52, 'sport': 0.38, ...}
```

## Key Features

### Random Search Algorithm
The optimizer uses random search to explore the threshold space:
- For each iteration, it randomly samples thresholds within `±search_step` of the current value
- It evaluates performance on the test set
- It keeps the best-performing thresholds

### Per-Route Optimization
Unlike a single global threshold, the optimizer finds the best threshold for **each route independently**. This is important because:
- Some categories may need stricter matching (lower threshold)
- Others may benefit from more lenient matching (higher threshold)

### Evaluation Metrics
You can optimize for different goals:
- **F1 score** (default): Balance between precision and recall
- **Precision**: Minimize false positives (incorrect matches)
- **Recall**: Minimize false negatives (missed matches)

## Script Flow

1. **Load reference articles** (300 per category) to build the router
2. **Create routes** with initial threshold (0.5)
3. **Initialize router** with min aggregation method
4. **Load optimization dataset** (100 articles)
5. **Run optimization** to find best thresholds
6. **Evaluate on full test set** (200 articles)
7. **Report statistics** including accuracy and optimized thresholds

## Expected Output

```
Step 6: Running threshold optimization...
  Initial thresholds: {'business': 0.5, 'tech': 0.5, 'sport': 0.5, ...}
  
Eval metric F1: start 0.850, end 0.923
Ending thresholds: {'business': 0.45, 'tech': 0.52, 'sport': 0.38, ...}

  Optimized thresholds: {'business': 0.45, 'tech': 0.52, 'sport': 0.38, ...}
```

## Benefits

1. **Automated tuning**: No manual trial-and-error
2. **Better accuracy**: Optimized thresholds improve classification performance
3. **Per-category customization**: Each route gets its optimal threshold
4. **Data-driven**: Based on actual performance on your test set

## Parameters to Tune

### `max_iterations`
- Default: 20
- Higher values = more thorough search but slower
- Recommended: 20-50 for production

### `search_step`
- Default: 0.10
- Defines the search range: `[current_threshold - 0.10, current_threshold + 0.10]`
- Smaller values = finer-grained search
- Larger values = broader exploration

### `eval_metric`
- Options: "f1", "precision", "recall"
- Choose based on your use case:
  - **F1**: Balanced performance
  - **Precision**: When false positives are costly
  - **Recall**: When false negatives are costly

## Installation

Make sure you have the required package:
```bash
pip install redis-retrieval-optimizer
```

## Running the Script

```bash
python 4_RedisVLRouterWithOptimizer.py
```

## Comparison with Manual Tuning

**Manual approach:**
- Try threshold 0.3 → accuracy 75%
- Try threshold 0.5 → accuracy 82%
- Try threshold 0.7 → accuracy 78%
- Use 0.5 for all routes

**Optimized approach:**
- Automatically tests many combinations
- Finds best threshold per route
- Achieves 92%+ accuracy
- business: 0.45, tech: 0.52, sport: 0.38, etc.

## Notes

- The optimizer uses a subset of data (100 articles) for speed
- Final evaluation uses the full test set (200 articles)
- Optimization takes a few minutes depending on dataset size
- Results are deterministic given the same random seed

