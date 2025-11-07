#!/usr/bin/env python3
"""
Test script to demonstrate how distance_threshold works in RedisVL SemanticRouter.
"""

import os
from redisvl.extensions.router import Route, SemanticRouter
from redisvl.utils.vectorize import HFTextVectorizer

os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Test with different distance thresholds
thresholds = [0.5, 0.6, 0.7, 0.8, 0.9, 0.99]

# Create a simple route
tech_route = Route(
    name="technology",
    references=[
        "artificial intelligence and machine learning",
        "latest smartphone releases",
        "cloud computing trends"
    ],
    distance_threshold=0.7  # We'll update this in the loop
)

# Test queries - some close, some far from tech
test_queries = [
    ("AI is transforming industries", "Very close to tech"),
    ("New iPhone announced today", "Close to tech"),
    ("Football match results", "Far from tech"),
    ("Cooking recipes for dinner", "Very far from tech")
]

print("=" * 80)
print("Distance Threshold Test")
print("=" * 80)
print("\nNote: In cosine distance, LOWER values = MORE similar")
print("      Distance 0.0 = identical, Distance 1.0 = completely different")
print()

for threshold in thresholds:
    print(f"\n{'=' * 80}")
    print(f"Testing with distance_threshold = {threshold}")
    print(f"{'=' * 80}")
    
    # Update the route's threshold
    tech_route.distance_threshold = threshold
    
    # Create router
    router = SemanticRouter(
        name=f"test-router-{threshold}",
        vectorizer=HFTextVectorizer(),
        routes=[tech_route],
        redis_url="redis://localhost:6379",
        overwrite=True
    )
    
    # Test each query
    for query, description in test_queries:
        result = router(query)
        
        if result.name:
            print(f"  ✓ MATCHED: '{query[:40]}...' ({description})")
            print(f"    Distance: {result.distance:.4f} (below threshold {threshold})")
        else:
            print(f"  ✗ NO MATCH: '{query[:40]}...' ({description})")
            print(f"    (distance was above threshold {threshold})")
    
    # Cleanup
    router.delete()

print("\n" + "=" * 80)
print("Summary:")
print("=" * 80)
print("- LOWER threshold = MORE STRICT (fewer matches, only very similar)")
print("- HIGHER threshold = MORE PERMISSIVE (more matches, accepts less similar)")
print("- Threshold 0.99 accepts almost everything!")
print("- Threshold 0.5-0.7 is typically good for strict matching")
print("=" * 80)

