#!/usr/bin/env python3
"""
Test script for the MCP-FreeCAD optimization features.
This script tests caching, recovery mechanisms, and performance monitoring.
"""

import asyncio
import aiohttp
import json
import logging
import sys
import time
import random
from datetime import datetime
import argparse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

API_URL = "http://localhost:8000"  # Update this to match your server's host and port
API_KEY = "development"  # Update this to match your server's API key


async def test_health_endpoints():
    """Test the health check endpoints."""
    async with aiohttp.ClientSession() as session:
        # Basic health check
        logger.info("Testing basic health check endpoint...")
        async with session.get(f"{API_URL}/health") as response:
            if response.status == 200:
                result = await response.json()
                logger.info(f"Health check result: {json.dumps(result, indent=2)}")
            else:
                logger.error(f"Failed health check: {response.status}")
                text = await response.text()
                logger.error(text)
        
        # Detailed health check
        logger.info("Testing detailed health check endpoint...")
        async with session.get(f"{API_URL}/health/detailed") as response:
            if response.status == 200:
                result = await response.json()
                logger.info(f"Detailed health check result: {json.dumps(result, indent=2)}")
            else:
                logger.error(f"Failed detailed health check: {response.status}")
                text = await response.text()
                logger.error(text)


async def test_cache():
    """Test the caching functionality."""
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": API_KEY}
        
        # Get cache stats
        logger.info("Testing cache stats endpoint...")
        async with session.get(f"{API_URL}/cache/stats", headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                logger.info(f"Cache stats: {json.dumps(result, indent=2)}")
            else:
                logger.error(f"Failed to get cache stats: {response.status}")
                text = await response.text()
                logger.error(text)
        
        # Clear cache
        logger.info("Testing cache clear endpoint...")
        async with session.post(f"{API_URL}/cache/clear", headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                logger.info(f"Cache clear result: {json.dumps(result, indent=2)}")
            else:
                logger.error(f"Failed to clear cache: {response.status}")
                text = await response.text()
                logger.error(text)
                
        # Get cache stats again to verify clear
        logger.info("Verifying cache was cleared...")
        async with session.get(f"{API_URL}/cache/stats", headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                logger.info(f"Cache stats after clear: {json.dumps(result, indent=2)}")
            else:
                logger.error(f"Failed to get cache stats: {response.status}")
                text = await response.text()
                logger.error(text)


async def test_diagnostics():
    """Test the diagnostics endpoints."""
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": API_KEY}
        
        # Get diagnostics
        logger.info("Testing diagnostics endpoint...")
        async with session.get(f"{API_URL}/diagnostics", headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                logger.info(f"Diagnostics summary:")
                logger.info(f"  Server uptime: {result['server']['uptime_formatted']}")
                logger.info(f"  Request count: {result['server']['request_count']}")
                logger.info(f"  Error count: {result['server']['error_count']}")
                logger.info(f"  Metric count: {result['server']['metric_count']}")
                
                # Log system stats
                if 'system' in result:
                    logger.info(f"  CPU usage: {result['system'].get('cpu_percent', 'N/A')}%")
                    if 'memory_usage' in result['system']:
                        logger.info(f"  Memory usage: {round(result['system']['memory_usage'].get('rss', 0), 2)} MB")
                    if 'thread_count' in result['system']:
                        logger.info(f"  Thread count: {result['system']['thread_count']}")
                
                # Log top 3 slowest endpoints
                if 'metrics' in result and result['metrics']:
                    sorted_metrics = sorted(result['metrics'], key=lambda m: m.get('avg_duration', 0), reverse=True)
                    logger.info("  Top slowest endpoints:")
                    for i, metric in enumerate(sorted_metrics[:3], 1):
                        logger.info(f"    {i}. {metric['name']}: {round(metric['avg_duration'] * 1000, 2)} ms (calls: {metric['total_calls']})")
            else:
                logger.error(f"Failed to get diagnostics: {response.status}")
                text = await response.text()
                logger.error(text)
        
        # Reset diagnostics
        logger.info("Testing diagnostics reset endpoint...")
        async with session.post(f"{API_URL}/diagnostics/reset", headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                logger.info(f"Diagnostics reset result: {json.dumps(result, indent=2)}")
            else:
                logger.error(f"Failed to reset diagnostics: {response.status}")
                text = await response.text()
                logger.error(text)


async def stress_test_recovery(num_requests=20, concurrency=5):
    """Test the recovery mechanism with concurrent requests."""
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": API_KEY}
        
        # Function to make a measurement request
        async def make_measurement_request(i):
            try:
                data = {
                    "parameters": {
                        "object1": f"TestObject{i}",
                        "object2": f"TestObject{i+1}",
                        "random": random.random()
                    }
                }
                
                start_time = time.time()
                async with session.post(
                    f"{API_URL}/tools/measurement.distance",
                    headers=headers,
                    json=data
                ) as response:
                    duration = time.time() - start_time
                    status = response.status
                    if status == 200:
                        return True, duration
                    else:
                        text = await response.text()
                        logger.warning(f"Request {i} failed with status {status}: {text}")
                        return False, duration
            except Exception as e:
                logger.error(f"Request {i} exception: {e}")
                return False, 0
        
        # Create tasks for concurrent requests
        logger.info(f"Starting stress test with {num_requests} requests ({concurrency} concurrent)...")
        tasks = []
        results = []
        
        for i in range(num_requests):
            if len(tasks) >= concurrency:
                # Wait for one task to complete before adding more
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                tasks = list(pending)
                for task in done:
                    results.append(await task)
            
            # Add a new task
            tasks.append(asyncio.create_task(make_measurement_request(i)))
            
        # Wait for remaining tasks
        if tasks:
            done, _ = await asyncio.wait(tasks)
            for task in done:
                results.append(await task)
        
        # Analyze results
        success_count = sum(1 for success, _ in results if success)
        failure_count = len(results) - success_count
        if results:
            avg_duration = sum(duration for _, duration in results) / len(results)
            
            logger.info(f"Stress test results:")
            logger.info(f"  Total requests: {len(results)}")
            logger.info(f"  Successful requests: {success_count} ({(success_count/len(results))*100:.1f}%)")
            logger.info(f"  Failed requests: {failure_count}")
            logger.info(f"  Average duration: {avg_duration*1000:.2f} ms")
        else:
            logger.error("No results from stress test")


async def main():
    """Run all optimization tests."""
    parser = argparse.ArgumentParser(description='Test MCP-FreeCAD optimization features')
    parser.add_argument('--url', default='http://localhost:8000', help='Server URL')
    parser.add_argument('--key', default='development', help='API key')
    parser.add_argument('--stress', action='store_true', help='Run stress test')
    parser.add_argument('--requests', type=int, default=20, help='Number of requests for stress test')
    parser.add_argument('--concurrency', type=int, default=5, help='Concurrent requests for stress test')
    
    args = parser.parse_args()
    
    global API_URL, API_KEY
    API_URL = args.url
    API_KEY = args.key
    
    logger.info(f"Testing optimization features on {API_URL}")
    
    try:
        # Test health check endpoints
        await test_health_endpoints()
        
        # Test cache functionality
        await test_cache()
        
        # Test diagnostics
        await test_diagnostics()
        
        # Run stress test if requested
        if args.stress:
            await stress_test_recovery(args.requests, args.concurrency)
        
        logger.info("All tests completed!")
        
    except Exception as e:
        logger.error(f"Error during testing: {e}")
        return 1
        
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user.")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1) 