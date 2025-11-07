#!/usr/bin/env python3
"""
Script to classify BBC news articles using ChatGPT and validate results.
Measures performance metrics including average time, p95, p99, and cost.
"""

import csv
import time
import numpy as np
import json
from openai import OpenAI
from config import OPENAI_API_KEY

# Pricing per 1M tokens (as of 2025)
PRICING = {
    "gpt-4-turbo": {
        "input": 10.00,   # $10.00 per 1M input tokens
        "output": 30.00   # $30.00 per 1M output tokens
    },
    "gpt-4": {
        "input": 30.00,   # $30.00 per 1M input tokens
        "output": 60.00   # $60.00 per 1M output tokens
    },
    "gpt-3.5-turbo": {
        "input": 0.50,    # $0.50 per 1M input tokens
        "output": 1.50    # $1.50 per 1M output tokens
    }
}

# Batch API pricing (50% discount)
BATCH_PRICING = {
    "gpt-4-turbo": {
        "input": 5.00,    # $5.00 per 1M input tokens (50% off)
        "output": 15.00   # $15.00 per 1M output tokens (50% off)
    },
    "gpt-4": {
        "input": 15.00,   # $15.00 per 1M input tokens (50% off)
        "output": 30.00   # $30.00 per 1M output tokens (50% off)
    },
    "gpt-3.5-turbo": {
        "input": 0.25,    # $0.25 per 1M input tokens (50% off)
        "output": 0.75    # $0.75 per 1M output tokens (50% off)
    }
}

MODELS_TO_TEST = ["gpt-3.5-turbo", "gpt-4-turbo", "gpt-4"]  # Models to compare


def read_news_articles(filename, num_articles=5):
    """Read specified number of articles from CSV file."""
    articles = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= num_articles:
                break
            articles.append({
                'article_id': row['ArticleId'],
                'text': row['Text'],
                'actual_category': row['Category']
            })
    return articles


def calculate_cost(input_tokens, output_tokens, model):
    """Calculate the cost based on token usage and model pricing."""
    if model not in PRICING:
        return 0.0

    input_cost = (input_tokens / 1_000_000) * PRICING[model]["input"]
    output_cost = (output_tokens / 1_000_000) * PRICING[model]["output"]
    total_cost = input_cost + output_cost

    return total_cost


def classify_with_chatgpt(client, text, model):
    """Classify news article text using ChatGPT with rate limit handling."""
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
                model=model,
                messages=[
                    {"role": "system", "content": "You are a news article classifier. Respond only with the category name."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=10,
                timeout=3.0  # 3 second timeout
            )
            break  # Success, exit retry loop

        except Exception as e:
            error_str = str(e).lower()
            if "rate_limit" in error_str or "429" in error_str or "timeout" in error_str:
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = 7 * retry_count  # Exponential backoff: 5s, 10s, 15s, 20s
                    error_type = "Rate limit" if "rate_limit" in error_str or "429" in error_str else "Timeout"
                    print(f"  {error_type} hit, waiting {wait_time}s before retry {retry_count}/{max_retries}...")
                    time.sleep(wait_time)
                else:
                    raise  # Max retries reached, re-raise the exception
            else:
                raise  # Not a rate limit or timeout error, re-raise

    end_time = time.time()
    elapsed_time = end_time - start_time

    predicted_category = response.choices[0].message.content.strip().lower()

    # Extract token usage
    input_tokens = response.usage.prompt_tokens
    output_tokens = response.usage.completion_tokens

    # Calculate cost
    cost = calculate_cost(input_tokens, output_tokens, model)

    return predicted_category, elapsed_time, input_tokens, output_tokens, cost


def calculate_percentiles(times):
    """Calculate average, p95, and p99 from list of times."""
    if not times:
        return 0, 0, 0
    
    avg_time = np.mean(times)
    p95_time = np.percentile(times, 95)
    p99_time = np.percentile(times, 99)
    
    return avg_time, p95_time, p99_time


def test_model_batch(client, articles, model):
    """Test a single model using Batch API and return metrics."""
    print(f"\nTesting {model} with Batch API...")

    # Step 1: Create batch input file
    print(f"  Creating batch requests for {len(articles)} articles...")
    batch_requests = []

    for idx, article in enumerate(articles):
        prompt = f"""Classify the following news article into exactly ONE of these categories:
- business
- tech
- sport
- politics
- entertainment

Article: {article['text']}

Respond with ONLY the category name in lowercase, nothing else."""

        request = {
            "custom_id": f"request-{idx}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a news article classifier. Respond only with the category name."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0,
                "max_tokens": 10
            }
        }
        batch_requests.append(request)

    # Write batch requests to file
    batch_input_file = f"batch_input_{model.replace('-', '_')}.jsonl"
    with open(batch_input_file, 'w') as f:
        for request in batch_requests:
            f.write(json.dumps(request) + '\n')

    print(f"  Batch input file created: {batch_input_file}")

    # Step 2: Upload the batch input file
    print(f"  Uploading batch input file...")
    start_time = time.time()

    with open(batch_input_file, 'rb') as f:
        batch_input_file_obj = client.files.create(
            file=f,
            purpose="batch"
        )

    print(f"  File uploaded: {batch_input_file_obj.id}")

    # Step 3: Create the batch
    print(f"  Creating batch job...")
    batch_job = client.batches.create(
        input_file_id=batch_input_file_obj.id,
        endpoint="/v1/chat/completions",
        completion_window="24h"
    )

    print(f"  Batch job created: {batch_job.id}")
    print(f"  Status: {batch_job.status}")

    # Step 4: Poll for completion
    print(f"  Waiting for batch to complete...")
    while batch_job.status not in ["completed", "failed", "expired", "cancelled"]:
        time.sleep(10)  # Poll every 10 seconds
        batch_job = client.batches.retrieve(batch_job.id)
        print(f"  Status: {batch_job.status} (Request counts: {batch_job.request_counts})")

    end_time = time.time()
    total_time = end_time - start_time

    if batch_job.status != "completed":
        print(f"  Batch job failed with status: {batch_job.status}")
        return None

    print(f"  Batch completed in {total_time:.2f} seconds!")

    # Step 5: Download and process results
    print(f"  Downloading results...")
    result_file_id = batch_job.output_file_id
    result_content = client.files.content(result_file_id)

    # Parse results
    results = []
    correct_predictions = 0
    total_input_tokens = 0
    total_output_tokens = 0

    result_lines = result_content.text.strip().split('\n')
    for line in result_lines:
        result = json.loads(line)
        custom_id = result['custom_id']
        idx = int(custom_id.split('-')[1])

        response_body = result['response']['body']
        predicted_category = response_body['choices'][0]['message']['content'].strip().lower()

        input_tokens = response_body['usage']['prompt_tokens']
        output_tokens = response_body['usage']['completion_tokens']
        total_input_tokens += input_tokens
        total_output_tokens += output_tokens

        article = articles[idx]
        is_correct = predicted_category == article['actual_category']
        if is_correct:
            correct_predictions += 1

        results.append({
            'article_id': article['article_id'],
            'actual': article['actual_category'],
            'predicted': predicted_category,
            'correct': is_correct,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens
        })

    # Calculate cost using batch pricing (50% discount)
    input_cost = (total_input_tokens / 1_000_000) * BATCH_PRICING[model]["input"]
    output_cost = (total_output_tokens / 1_000_000) * BATCH_PRICING[model]["output"]
    total_cost = input_cost + output_cost
    avg_cost = total_cost / len(articles)

    # Calculate metrics
    accuracy = (correct_predictions / len(articles)) * 100
    avg_time_per_article = total_time / len(articles)

    print(f"  Completed: {len(articles)} articles processed.")

    return {
        'model': model,
        'accuracy': accuracy,
        'correct': correct_predictions,
        'total': len(articles),
        'total_time': total_time,
        'avg_time': avg_time_per_article,
        'total_cost': total_cost,
        'avg_cost': avg_cost,
        'daily_cost': avg_cost * 100000,  # Cost for 100,000 articles per day
        'total_input_tokens': total_input_tokens,
        'total_output_tokens': total_output_tokens,
        'results': results,
        'batch_job_id': batch_job.id
    }


def test_model(client, articles, model):
    """Test a single model and return metrics."""
    print(f"\nTesting {model}...")

    results = []
    response_times = []
    costs = []
    total_input_tokens = 0
    total_output_tokens = 0
    correct_predictions = 0

    for idx, article in enumerate(articles, 1):
        # Show progress every 10 articles
        if idx % 10 == 0:
            print(f"  Progress: {idx}/{len(articles)} articles processed...")

        # Classify with ChatGPT
        predicted_category, elapsed_time, input_tokens, output_tokens, cost = classify_with_chatgpt(
            client, article['text'], model
        )
        response_times.append(elapsed_time)
        costs.append(cost)
        total_input_tokens += input_tokens
        total_output_tokens += output_tokens

        # Validate
        is_correct = predicted_category == article['actual_category']
        if is_correct:
            correct_predictions += 1

        results.append({
            'article_id': article['article_id'],
            'actual': article['actual_category'],
            'predicted': predicted_category,
            'correct': is_correct,
            'time': elapsed_time,
            'cost': cost,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens
        })

    print(f"  Completed: {len(articles)}/{len(articles)} articles processed.")

    # Calculate metrics
    accuracy = (correct_predictions / len(articles)) * 100
    avg_time, p95_time, p99_time = calculate_percentiles(response_times)
    total_cost = sum(costs)
    avg_cost = np.mean(costs)

    return {
        'model': model,
        'accuracy': accuracy,
        'correct': correct_predictions,
        'total': len(articles),
        'avg_time': avg_time,
        'p95_time': p95_time,
        'p99_time': p99_time,
        'min_time': min(response_times),
        'max_time': max(response_times),
        'total_cost': total_cost,
        'avg_cost': avg_cost,
        'daily_cost': avg_cost * 100000,  # Cost for 100,000 articles per day
        'total_input_tokens': total_input_tokens,
        'total_output_tokens': total_output_tokens,
        'results': results
    }


def main():
    """Main function to run the classification and validation."""
    print("=" * 80)
    print("BBC News Article Classification - Model Comparison")
    print("=" * 80)
    print()

    # Initialize OpenAI client
    client = OpenAI(api_key=OPENAI_API_KEY)

    # Read articles
    print("Reading 100 articles from 'BBC News Train.csv'...")
    articles = read_news_articles('BBC News Train.csv', num_articles=100)
    print(f"Successfully read {len(articles)} articles.")

    # Test all models
    all_results = []
    for model in MODELS_TO_TEST:
        model_results = test_model(client, articles, model)
        all_results.append(model_results)

    # Display comparison table
    print(f"\n\n{'=' * 100}")
    print("MODEL COMPARISON - SUMMARY STATISTICS")
    print(f"{'=' * 100}\n")

    # Header
    print(f"{'Model':<20} {'Accuracy':<12} {'Avg Time':<12} {'P95 Time':<12} {'P99 Time':<12} {'Cost/Article':<15} {'Daily Cost':<12}")
    print("-" * 100)

    # Data rows
    for result in all_results:
        print(f"{result['model']:<20} "
              f"{result['correct']}/{result['total']} ({result['accuracy']:.1f}%){'':<2} "
              f"{result['avg_time']:.3f}s{'':<6} "
              f"{result['p95_time']:.3f}s{'':<6} "
              f"{result['p99_time']:.3f}s{'':<6} "
              f"${result['avg_cost']:.6f}{'':<6} "
              f"${result['daily_cost']:.2f}")

    print(f"\n{'=' * 100}\n")

    # Detailed breakdown for each model
    print("\nDETAILED BREAKDOWN BY MODEL:")
    print("=" * 100)

    for result in all_results:
        print(f"\n{result['model']}:")
        print(f"  Accuracy: {result['correct']}/{result['total']} ({result['accuracy']:.1f}%)")
        print(f"  Response Times: Avg={result['avg_time']:.3f}s, Min={result['min_time']:.3f}s, Max={result['max_time']:.3f}s")
        print(f"  Tokens: {result['total_input_tokens']:,} input, {result['total_output_tokens']:,} output")
        print(f"  Total Cost: ${result['total_cost']:.6f}")

    print(f"\n{'=' * 100}\n")


def main_batch():
    """Main function to run batch classification and validation."""
    print("=" * 80)
    print("BBC News Article Classification - Batch API Model Comparison")
    print("=" * 80)
    print()

    # Initialize OpenAI client
    client = OpenAI(api_key=OPENAI_API_KEY)

    # Read articles
    print("Reading 100 articles from 'BBC News Train.csv'...")
    articles = read_news_articles('BBC News Train.csv', num_articles=100)
    print(f"Successfully read {len(articles)} articles.")

    # Test all models with Batch API
    all_results = []
    for model in MODELS_TO_TEST:
        model_results = test_model_batch(client, articles, model)
        if model_results:
            all_results.append(model_results)

    # Display comparison table
    print(f"\n\n{'=' * 100}")
    print("BATCH API MODEL COMPARISON - SUMMARY STATISTICS")
    print(f"{'=' * 100}\n")

    # Header
    print(f"{'Model':<20} {'Accuracy':<12} {'Total Time':<12} {'Avg Time':<12} {'Cost/Article':<15} {'Daily Cost':<12}")
    print("-" * 100)

    # Data rows
    for result in all_results:
        print(f"{result['model']:<20} "
              f"{result['correct']}/{result['total']} ({result['accuracy']:.1f}%){'':<2} "
              f"{result['total_time']:.1f}s{'':<7} "
              f"{result['avg_time']:.3f}s{'':<6} "
              f"${result['avg_cost']:.6f}{'':<6} "
              f"${result['daily_cost']:.2f}")

    print(f"\n{'=' * 100}\n")

    # Detailed breakdown for each model
    print("\nDETAILED BREAKDOWN BY MODEL:")
    print("=" * 100)

    for result in all_results:
        print(f"\n{result['model']}:")
        print(f"  Accuracy: {result['correct']}/{result['total']} ({result['accuracy']:.1f}%)")
        print(f"  Total Time: {result['total_time']:.2f}s")
        print(f"  Avg Time per Article: {result['avg_time']:.3f}s")
        print(f"  Tokens: {result['total_input_tokens']:,} input, {result['total_output_tokens']:,} output")
        print(f"  Total Cost: ${result['total_cost']:.6f} (with 50% batch discount)")
        print(f"  Batch Job ID: {result['batch_job_id']}")

    print(f"\n{'=' * 100}\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--batch":
        main_batch()
    else:
        main()

