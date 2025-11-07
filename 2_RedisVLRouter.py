#!/usr/bin/env python3
"""
Script to classify BBC news articles using RedisVL SemanticRouter.
Uses reference routes from BBC News Train2.csv to initialize the router,
then tests on first 5 articles from BBC News Train.csv.
Tracks accuracy and latency statistics.
"""

import csv
import time
import os
import numpy as np
from redisvl.extensions.router import Route, SemanticRouter
from redisvl.utils.vectorize import HFTextVectorizer

# Disable tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Redis connection
REDIS_URL = "redis://localhost:6379"

# Categories
CATEGORIES = ["business", "tech", "sport", "politics", "entertainment"]


def read_reference_articles(filename, num_per_category=10):
    """Read reference articles from CSV file for each category."""
    references_by_category = {cat: [] for cat in CATEGORIES}
    
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            category = row['Category'].lower()
            if category in references_by_category:
                if len(references_by_category[category]) < num_per_category:
                    references_by_category[category].append(row['Text'])
    
    return references_by_category


def read_test_articles(filename, num_articles=5):
    """Read test articles from CSV file."""
    articles = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= num_articles:
                break
            articles.append({
                'article_id': row['ArticleId'],
                'text': row['Text'],
                'actual_category': row['Category'].lower()
            })
    return articles


def create_routes(references_by_category, distance_threshold=0.99):
    """Create Route objects for each category."""
    routes = []
    
    for category, references in references_by_category.items():
        if references:  # Only create route if we have references
            route = Route(
                name=category,
                references=references,
                metadata={"category": category},
                distance_threshold=distance_threshold
            )
            routes.append(route)
            print(f"  Created route '{category}' with {len(references)} references")
    
    return routes


def initialize_router(routes, router_name="news-classifier-router"):
    """Initialize the SemanticRouter with the given routes."""
    print(f"\nInitializing SemanticRouter '{router_name}'...")
    
    router = SemanticRouter(
        name=router_name,
        vectorizer=HFTextVectorizer(),
        routes=routes,
        redis_url=REDIS_URL,
        overwrite=True  # Overwrite any existing router with this name
    )
    
    print(f"  Router initialized with {len(routes)} routes")
    return router


def classify_article(router, text):
    """Classify an article using the semantic router."""
    start_time = time.time()
    
    # Get the best matching route
    route_match = router(text)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    # Extract the predicted category (route name)
    predicted_category = route_match.name if route_match.name else "unknown"
    distance = route_match.distance if route_match.distance else None
    
    return predicted_category, distance, elapsed_time


def calculate_statistics(times):
    """Calculate average, p95, and p99 from list of times."""
    if not times:
        return 0, 0, 0
    
    avg_time = np.mean(times)
    p95_time = np.percentile(times, 95)
    p99_time = np.percentile(times, 99)
    
    return avg_time, p95_time, p99_time


def main():
    """Main function to run the classification and validation."""
    print("=" * 80)
    print("BBC News Article Classification - RedisVL SemanticRouter")
    print("=" * 80)
    print()
    
    # Step 1: Read reference articles from Train2.csv
    print("Step 1: Reading reference articles from 'BBC News Train2.csv'...")
    references_by_category = read_reference_articles('BBC News Train2.csv', num_per_category=150)
    
    total_refs = sum(len(refs) for refs in references_by_category.values())
    print(f"  Loaded {total_refs} reference articles across {len(CATEGORIES)} categories")
    for category, refs in references_by_category.items():
        print(f"    - {category}: {len(refs)} references")
    
    # Step 2: Create routes
    print("\nStep 2: Creating routes...")
    routes = create_routes(references_by_category, distance_threshold=0.50)
    
    # Step 3: Initialize the SemanticRouter
    router = initialize_router(routes)
    
    # Step 4: Read test articles from Train.csv
    print("\nStep 3: Reading test articles from 'BBC News Train.csv'...")
    test_articles = read_test_articles('BBC News Train.csv', num_articles=100)
    print(f"  Loaded {len(test_articles)} test articles")
    
    # Step 5: Classify and validate
    print("\nStep 4: Classifying articles with SemanticRouter...")
    print("-" * 80)
    
    results = []
    response_times = []
    correct_predictions = 0
    unknown_predictions = 0

    for idx, article in enumerate(test_articles, 1):
        #print(f"\nArticle {idx}/{len(test_articles)} (ID: {article['article_id']})")
        #print(f"  Actual category: {article['actual_category']}")
        
        # Classify
        predicted_category, distance, elapsed_time = classify_article(router, article['text'])
        response_times.append(elapsed_time)
        
        # Validate
        is_correct = predicted_category == article['actual_category']
        if is_correct:
            correct_predictions += 1
        else:
            print(f"Incorrect Distance: {distance:.4f}" if distance else "  Distance: N/A")
        # Track unknown predictions
        if predicted_category == "unknown":
            unknown_predictions += 1


        #print(f" {idx} : {predicted_category} : {'✓ CORRECT' if is_correct else '✗ INCORRECT'}")
        #print(f"  Distance: {distance:.4f}" if distance else "  Distance: N/A")
        #print(f"  Response time: {elapsed_time:.3f}s")
        #print(f"  Result: {'✓ CORRECT' if is_correct else '✗ INCORRECT'}")
        
        results.append({
            'article_id': article['article_id'],
            'actual': article['actual_category'],
            'predicted': predicted_category,
            'distance': distance,
            'correct': is_correct,
            'time': elapsed_time
        })
    
    # Step 6: Calculate and display statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)

    accuracy = (correct_predictions / len(test_articles)) * 100
    unknown_rate = (unknown_predictions / len(test_articles)) * 100
    avg_time, p95_time, p99_time = calculate_statistics(response_times)

    print(f"\nAccuracy: {correct_predictions}/{len(test_articles)} ({accuracy:.1f}%)")
    print(f"Unknown Predictions: {unknown_predictions}/{len(test_articles)} ({unknown_rate:.1f}%)")
    print(f"\nLatency Statistics:")
    print(f"  Average Response Time: {avg_time:.3f}s")
    print(f"  P95 Response Time: {p95_time:.3f}s")
    print(f"  P99 Response Time: {p99_time:.3f}s")
    print(f"  Min Response Time: {min(response_times):.3f}s")
    print(f"  Max Response Time: {max(response_times):.3f}s")
    
    print("\n" + "=" * 80)
    
    # Cleanup
    print("\nCleaning up...")
    #router.delete()
    print("  Router deleted from Redis")
    
    print("\nDone!")


if __name__ == "__main__":
    main()

