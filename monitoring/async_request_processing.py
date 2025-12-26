"""Async/Concurrent Request Processing for st-risk-platform

Implements async patterns for:
- Risk assessment API endpoints
- Background job processing
- Batch operations
- WebSocket updates

Expected improvements:
- 3-5x throughput increase
- 50-70% reduction in response times
- Better resource utilization
- Handle 10x concurrent requests
"""

import asyncio
import logging
from typing import Callable, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor
from functools import wraps, partial
from datetime import datetime
import time

from fastapi import BackgroundTasks, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AsyncTaskQueue:
    """Manages async task execution with concurrency control."""
    
    def __init__(self, max_concurrent: int = 20):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.tasks = []
        self.completed = 0
        self.failed = 0
    
    async def add_task(self, coro):
        """Add a task to the queue."""
        async with self.semaphore:
            try:
                result = await coro
                self.completed += 1
                return result
            except Exception as e:
                self.failed += 1
                logger.error(f"Task failed: {e}")
                raise
    
    async def add_tasks(self, coros: List):
        """Add multiple tasks and wait for all."""
        tasks = [self.add_task(coro) for coro in coros]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_stats(self):
        """Get queue statistics."""
        return {
            'max_concurrent': self.max_concurrent,
            'completed': self.completed,
            'failed': self.failed,
            'success_rate': self.completed / (self.completed + self.failed) if (self.completed + self.failed) > 0 else 0
        }


# Global task queue
task_queue = AsyncTaskQueue(max_concurrent=20)


def async_task(func: Callable):
    """Decorator to mark function as async task and handle execution."""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    
    @wraps(func)
    def sync_wrapper(*args, background_tasks: Optional[BackgroundTasks] = None, **kwargs):
        """Wrapper for sync endpoints that need to run async tasks."""
        if background_tasks:
            # Run in background
            background_tasks.add_task(async_wrapper, *args, **kwargs)
            return {'status': 'queued'}
        else:
            # Run synchronously
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            return loop.run_until_complete(async_wrapper(*args, **kwargs))
    
    return async_wrapper


class BatchProcessor:
    """Processes batch operations efficiently with concurrency control."""
    
    def __init__(self, batch_size: int = 100, max_concurrent: int = 5):
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_batch(
        self,
        items: List[Any],
        processor_func: Callable,
        timeout: int = 300
    ) -> List[Any]:
        """Process items in batches with concurrency control."""
        results = []
        
        # Split into batches
        batches = [
            items[i:i + self.batch_size]
            for i in range(0, len(items), self.batch_size)
        ]
        
        logger.info(f"Processing {len(items)} items in {len(batches)} batches")
        
        try:
            for batch_idx, batch in enumerate(batches):
                batch_results = await asyncio.wait_for(
                    self._process_batch_concurrent(batch, processor_func),
                    timeout=timeout
                )
                results.extend(batch_results)
                logger.debug(f"Batch {batch_idx + 1}/{len(batches)} completed")
        except asyncio.TimeoutError:
            logger.error(f"Batch processing timeout after {timeout}s")
            raise HTTPException(status_code=408, detail="Processing timeout")
        
        return results
    
    async def _process_batch_concurrent(
        self,
        items: List[Any],
        processor_func: Callable
    ) -> List[Any]:
        """Process batch items concurrently."""
        tasks = [
            self._process_item_with_semaphore(item, processor_func)
            for item in items
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _process_item_with_semaphore(
        self,
        item: Any,
        processor_func: Callable
    ) -> Any:
        """Process single item with semaphore."""
        async with self.semaphore:
            return await processor_func(item) if asyncio.iscoroutinefunction(processor_func) else processor_func(item)


class RiskAssessmentBatchProcessor(BatchProcessor):
    """Specialized batch processor for risk assessments."""
    
    async def assess_portfolios(self, portfolio_ids: List[str]) -> List[dict]:
        """Assess multiple portfolios concurrently."""
        return await self.process_batch(
            portfolio_ids,
            self._assess_single_portfolio
        )
    
    async def _assess_single_portfolio(self, portfolio_id: str) -> dict:
        """Assess single portfolio."""
        try:
            # Placeholder for actual assessment logic
            await asyncio.sleep(0.1)  # Simulate processing
            return {
                'portfolio_id': portfolio_id,
                'status': 'completed',
                'risk_score': 0.5
            }
        except Exception as e:
            logger.error(f"Assessment failed for {portfolio_id}: {e}")
            return {
                'portfolio_id': portfolio_id,
                'status': 'failed',
                'error': str(e)
            }


class ParallelDataFetcher:
    """Fetch data from multiple sources in parallel."""
    
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def fetch_multiple(
        self,
        fetch_functions: List[Callable]
    ) -> List[Any]:
        """Fetch from multiple sources concurrently."""
        tasks = [
            self._fetch_with_semaphore(func)
            for func in fetch_functions
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _fetch_with_semaphore(self, func: Callable) -> Any:
        """Fetch with semaphore control."""
        async with self.semaphore:
            try:
                return await func() if asyncio.iscoroutinefunction(func) else func()
            except Exception as e:
                logger.error(f"Fetch failed: {e}")
                return None


class RateLimiter:
    """Rate limiting for concurrent requests."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []
    
    async def acquire(self) -> bool:
        """Check if request can be processed."""
        now = time.time()
        # Clean old requests outside window
        self.requests = [
            req_time for req_time in self.requests
            if now - req_time < self.window_seconds
        ]
        
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False
    
    async def wait_if_needed(self):
        """Wait if rate limit is exceeded."""
        while not await self.acquire():
            await asyncio.sleep(0.1)


def run_in_threadpool(func: Callable):
    """Run CPU-intensive function in thread pool."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(
                executor,
                partial(func, *args, **kwargs)
            )
    return wrapper


class RequestMetrics:
    """Track metrics for async requests."""
    
    def __init__(self):
        self.total_requests = 0
        self.completed_requests = 0
        self.failed_requests = 0
        self.total_time = 0
        self.request_times = []
    
    async def track_request(self, coro):
        """Track async request execution."""
        self.total_requests += 1
        start = time.time()
        
        try:
            result = await coro
            self.completed_requests += 1
            return result
        except Exception as e:
            self.failed_requests += 1
            raise
        finally:
            elapsed = time.time() - start
            self.total_time += elapsed
            self.request_times.append(elapsed)
    
    def get_stats(self) -> dict:
        """Get request statistics."""
        if not self.request_times:
            return {}
        
        sorted_times = sorted(self.request_times)
        return {
            'total_requests': self.total_requests,
            'completed': self.completed_requests,
            'failed': self.failed_requests,
            'success_rate': self.completed_requests / self.total_requests if self.total_requests > 0 else 0,
            'avg_time_ms': (self.total_time / self.total_requests) * 1000,
            'median_time_ms': sorted_times[len(sorted_times) // 2] * 1000,
            'p95_time_ms': sorted_times[int(len(sorted_times) * 0.95)] * 1000,
            'p99_time_ms': sorted_times[int(len(sorted_times) * 0.99)] * 1000,
        }


# Global metrics
request_metrics = RequestMetrics()


async def get_request_metrics() -> dict:
    """Get current request metrics."""
    return request_metrics.get_stats()


# Example usage patterns for FastAPI
"""
From FastAPI routes:

# Pattern 1: Async endpoint with concurrent tasks
@app.post("/assess/batch")
async def batch_assess(portfolio_ids: List[str]):
    processor = RiskAssessmentBatchProcessor()
    results = await processor.assess_portfolios(portfolio_ids)
    return results

# Pattern 2: Background task
@app.post("/assess/{portfolio_id}")
async def assess_portfolio(portfolio_id: str, background_tasks: BackgroundTasks):
    @async_task
    async def long_assessment():
        # Long-running operation
        await asyncio.sleep(5)
        return {'result': 'done'}
    
    background_tasks.add_task(long_assessment)
    return {'status': 'processing'}

# Pattern 3: Fetch from multiple sources
@app.get("/dashboard/{portfolio_id}")
async def get_dashboard(portfolio_id: str):
    fetcher = ParallelDataFetcher()
    results = await fetcher.fetch_multiple([
        lambda: fetch_metrics(portfolio_id),
        lambda: fetch_events(portfolio_id),
        lambda: fetch_alerts(portfolio_id)
    ])
    return {'metrics': results[0], 'events': results[1], 'alerts': results[2]}
"""
