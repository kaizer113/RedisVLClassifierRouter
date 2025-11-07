#!/usr/bin/env python3
"""
Hybrid classification script combining RedisVL SemanticRouter with ChatGPT fallback.
- First attempts classification using RedisVL SemanticRouter (fast, local, free)
- If no match found (unknown), falls back to ChatGPT gpt-4-turbo
- Adds ChatGPT-classified articles as new references to the router for future learning
"""

import csv
import time
import os
import numpy as np
from redisvl.extensions.router import Route, SemanticRouter, RoutingConfig 
from redisvl.extensions.router.schema import DistanceAggregationMethod
from redisvl.utils.vectorize import HFTextVectorizer
from openai import OpenAI
from config import OPENAI_API_KEY

# Disable tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Redis connection
REDIS_URL = "redis://localhost:6379"

# Categories
CATEGORIES = ["business", "tech", "sport", "politics", "entertainment"]

# OpenAI pricing for gpt-4-turbo (per 1M tokens)
PRICING = {
    "input": 10.00,   # $10.00 per 1M input tokens
    "output": 30.00   # $30.00 per 1M output tokens
}


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


def create_routes(references_by_category, distance_threshold=0.5):
    """Create Route objects for each category."""
    routes = []
    
    for category, references in references_by_category.items():
        if references:
            route = Route(
                name=category,
                references=references,
                metadata={"category": category},
                distance_threshold=distance_threshold
            )
            routes.append(route)
            print(f"  Created route '{category}' with {len(references)} references")
    
    return routes


def initialize_router(routes, router_name="news-classifier-hybrid"):
    """Initialize the SemanticRouter with the given routes."""
    print(f"\nInitializing SemanticRouter '{router_name}'...")
    
    router = SemanticRouter(
        name=router_name,
        vectorizer=HFTextVectorizer(),
        routes=routes,
        redis_url=REDIS_URL,
        overwrite=True
    )
    
    print(f"  Router initialized with {len(routes)} routes")
    return router


def classify_with_router(router, text):
    """Classify an article using the semantic router."""
    start_time = time.time()
    
    route_match = router(text)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    predicted_category = route_match.name if route_match.name else "unknown"
    distance = route_match.distance if route_match.distance else None
    print(f"distance {distance}")
    return predicted_category, distance, elapsed_time


def classify_with_chatgpt(client, text):
    """Classify news article using ChatGPT gpt-4-turbo with rate limit handling."""
    prompt = f"""Classify the following news article into exactly ONE of these categories:
- business
- tech
- sport
- politics
- entertainment

Article: {text}

Respond with ONLY the category name in lowercase, nothing else."""

    start_time = time.time()
    
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "You are a news article classifier. Respond only with the category name."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=10,
                timeout=3.0
            )
            break
        except Exception as e:
            error_str = str(e).lower()
            if "rate_limit" in error_str or "429" in error_str or "timeout" in error_str:
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = 7 * retry_count
                    print(f"    Rate limit/timeout, waiting {wait_time}s (retry {retry_count}/{max_retries})...")
                    time.sleep(wait_time)
                else:
                    raise
            else:
                raise
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    predicted_category = response.choices[0].message.content.strip().lower()
    
    # Extract token usage
    input_tokens = response.usage.prompt_tokens
    output_tokens = response.usage.completion_tokens
    
    # Calculate cost
    input_cost = (input_tokens / 1_000_000) * PRICING["input"]
    output_cost = (output_tokens / 1_000_000) * PRICING["output"]
    cost = input_cost + output_cost
    
    return predicted_category, elapsed_time, cost, input_tokens, output_tokens


def add_reference_to_router(router, category, text):
    """Add a new reference to the router for the specified category."""
    try:
        router.add_route_references(route_name=category, references=[text])
        return True
    except Exception as e:
        print(f"    Warning: Failed to add reference to router: {e}")
        return False


def calculate_statistics(times):
    """Calculate average, p95, and p99 from list of times."""
    if not times:
        return 0, 0, 0
    
    avg_time = np.mean(times)
    p95_time = np.percentile(times, 95)
    p99_time = np.percentile(times, 99)
    
    return avg_time, p95_time, p99_time


def main():
    """Main function to run hybrid classification."""
    print("=" * 80)
    print("BBC News Classification - Hybrid: RedisVL + ChatGPT Fallback")
    print("=" * 80)
    print()
    
    # Initialize OpenAI client
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Step 1: Read reference articles
    print("Step 1: Reading reference articles from 'BBC News Train2.csv'...")
    references_by_category = read_reference_articles('BBC News Train2.csv', num_per_category=300)
    
    total_refs = sum(len(refs) for refs in references_by_category.values())
    print(f"  Loaded {total_refs} reference articles across {len(CATEGORIES)} categories")
    for category, refs in references_by_category.items():
        print(f"    - {category}: {len(refs)} references")
    
    # Step 2: Create routes
    print("\nStep 2: Creating routes...")
    routes = create_routes(references_by_category, distance_threshold=0.5)
    
    # Step 3: Initialize router
    router = initialize_router(routes)
    router.update_routing_config(
        RoutingConfig(aggregation_method=DistanceAggregationMethod.min)
    )
    
    # Step 4: Read test articles
    print("\nStep 3: Reading test articles from 'BBC News Train.csv'...")
    test_articles = read_test_articles('BBC News Train.csv', num_articles=200)
    print(f"  Loaded {len(test_articles)} test articles")
    
    # Step 5: Classify with hybrid approach
    print("\nStep 4: Classifying articles with hybrid approach...")
    print("-" * 80)
    
    results = []
    router_times = []
    chatgpt_times = []
    correct_predictions = 0
    router_matches = 0
    chatgpt_fallbacks = 0
    total_cost = 0.0
    total_input_tokens = 0
    total_output_tokens = 0
    references_added = 0
    
    for idx, article in enumerate(test_articles, 1):
        if idx % 10 == 0:
            print(f"  Processing article {idx}/{len(test_articles)}...")
        
        # Try router first
        predicted_category, distance, router_time = classify_with_router(router, article['text'])
        router_times.append(router_time)
        
        used_chatgpt = False
        chatgpt_time = 0
        cost = 0
        
        if predicted_category == "unknown":
            # Fallback to ChatGPT
            used_chatgpt = True
            chatgpt_fallbacks += 1
            
            predicted_category, chatgpt_time, cost, input_tokens, output_tokens = classify_with_chatgpt(
                client, article['text']
            )
            chatgpt_times.append(chatgpt_time)
            total_cost += cost
            total_input_tokens += input_tokens
            total_output_tokens += output_tokens
            
            # Add this article as a new reference to the router
            if predicted_category in CATEGORIES:
                if add_reference_to_router(router, predicted_category, article['text']):
                    references_added += 1
        else:
            router_matches += 1
        
        # Validate
        is_correct = predicted_category == article['actual_category']
        if is_correct:
            correct_predictions += 1
        
        total_time = router_time + chatgpt_time
        
        results.append({
            'article_id': article['article_id'],
            'actual': article['actual_category'],
            'predicted': predicted_category,
            'distance': distance,
            'correct': is_correct,
            'used_chatgpt': used_chatgpt,
            'router_time': router_time,
            'chatgpt_time': chatgpt_time,
            'total_time': total_time,
            'cost': cost
        })
    
    # Step 6: Calculate and display statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    
    accuracy = (correct_predictions / len(test_articles)) * 100
    router_rate = (router_matches / len(test_articles)) * 100
    fallback_rate = (chatgpt_fallbacks / len(test_articles)) * 100
    
    print(f"\nAccuracy: {correct_predictions}/{len(test_articles)} ({accuracy:.1f}%)")
    print(f"\nRouting Statistics:")
    print(f"  Router Matches: {router_matches}/{len(test_articles)} ({router_rate:.1f}%)")
    print(f"  ChatGPT Fallbacks: {chatgpt_fallbacks}/{len(test_articles)} ({fallback_rate:.1f}%)")
    print(f"  References Added to Router: {references_added}")
    
    # Calculate latency statistics
    all_times = [r['total_time'] for r in results]
    avg_time, p95_time, p99_time = calculate_statistics(all_times)
    
    print(f"\nLatency Statistics (Total):")
    print(f"  Average Response Time: {avg_time:.3f}s")
    print(f"  P95 Response Time: {p95_time:.3f}s")
    print(f"  P99 Response Time: {p99_time:.3f}s")
    print(f"  Min Response Time: {min(all_times):.3f}s")
    print(f"  Max Response Time: {max(all_times):.3f}s")
    
    if router_times:
        avg_router, p95_router, p99_router = calculate_statistics(router_times)
        print(f"\nRouter Latency:")
        print(f"  Average: {avg_router:.3f}s")
    
    if chatgpt_times:
        avg_chatgpt, p95_chatgpt, p99_chatgpt = calculate_statistics(chatgpt_times)
        print(f"\nChatGPT Latency (when used):")
        print(f"  Average: {avg_chatgpt:.3f}s")
        print(f"  P95: {p95_chatgpt:.3f}s")
        print(f"  P99: {p99_chatgpt:.3f}s")
    
    # Cost statistics
    cost_per_article = total_cost / len(test_articles)
    daily_cost_100k = cost_per_article * 100_000
    
    print(f"\nCost Statistics:")
    print(f"  Total Cost: ${total_cost:.6f}")
    print(f"  Cost per Article: ${cost_per_article:.6f}")
    print(f"  Daily Cost (100K articles): ${daily_cost_100k:.2f}")
    print(f"  Total Tokens: {total_input_tokens + total_output_tokens:,} ({total_input_tokens:,} input, {total_output_tokens:,} output)")
    
    print("\n" + "=" * 80)
    
    # Cleanup
    print("\nCleaning up...")
    #router.delete()
    print("  Router deleted from Redis")
    
    print("\nDone!")


if __name__ == "__main__":
    main()

