"""
Retry mechanisms and graceful degradation utilities for the web scraper application.
Provides exponential backoff retry logic and fallback mechanisms.
"""
import asyncio
import time
import random
from typing import Callable, Any, Optional, Dict, List, Union, Type
from functools import wraps
from dataclasses import dataclass
from enum import Enum

from .exceptions import (
    BaseScraperException, RetryableException, NetworkException,
    AIException, EmailException, ErrorSeverity
)
from .logger import get_logger


class RetryStrategy(Enum):
    """Different retry strategies available."""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    IMMEDIATE = "immediate"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    jitter: bool = True
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    retryable_exceptions: tuple = (NetworkException, AIException, EmailException)
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for the given attempt number."""
        if self.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.base_delay * (self.backoff_multiplier ** attempt)
        elif self.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.base_delay * (attempt + 1)
        elif self.strategy == RetryStrategy.FIXED_DELAY:
            delay = self.base_delay
        else:  # IMMEDIATE
            delay = 0
            
        # Apply maximum delay limit
        delay = min(delay, self.max_delay)
        
        # Add jitter to prevent thundering herd
        if self.jitter and delay > 0:
            jitter_amount = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_amount, jitter_amount)
            
        return max(0, delay)


class RetryManager:
    """
    Manages retry logic with exponential backoff and graceful degradation.
    Provides both synchronous and asynchronous retry capabilities.
    """
    
    def __init__(self, default_config: Optional[RetryConfig] = None):
        """
        Initialize retry manager.
        
        Args:
            default_config: Default retry configuration
        """
        self.default_config = default_config or RetryConfig()
        self.logger = get_logger("RetryManager")
        self.retry_stats: Dict[str, Dict[str, Any]] = {}
        
    def retry(self, config: Optional[RetryConfig] = None):
        """
        Decorator for adding retry logic to functions.
        
        Args:
            config: Retry configuration (uses default if None)
        """
        retry_config = config or self.default_config
        
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                return self._execute_with_retry(func, retry_config, *args, **kwargs)
            return wrapper
        return decorator
    
    def async_retry(self, config: Optional[RetryConfig] = None):
        """
        Decorator for adding retry logic to async functions.
        
        Args:
            config: Retry configuration (uses default if None)
        """
        retry_config = config or self.default_config
        
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await self._execute_async_with_retry(func, retry_config, *args, **kwargs)
            return wrapper
        return decorator
    
    def _execute_with_retry(self, func: Callable, config: RetryConfig, *args, **kwargs) -> Any:
        """Execute function with retry logic."""
        func_name = f"{func.__module__}.{func.__name__}"
        last_exception = None
        
        for attempt in range(config.max_attempts):
            try:
                self.logger.debug(f"Executing {func_name}, attempt {attempt + 1}/{config.max_attempts}")
                result = func(*args, **kwargs)
                
                # Log successful retry if not first attempt
                if attempt > 0:
                    self.logger.info(f"{func_name} succeeded on attempt {attempt + 1}")
                    self._update_retry_stats(func_name, attempt + 1, True)
                    
                return result
                
            except Exception as e:
                last_exception = e
                
                # Check if exception is retryable
                if not self._is_retryable_exception(e, config):
                    self.logger.debug(f"{func_name} failed with non-retryable exception: {e}")
                    self._update_retry_stats(func_name, attempt + 1, False)
                    raise
                
                # Check if we have more attempts
                if attempt >= config.max_attempts - 1:
                    self.logger.warning(f"{func_name} failed after {config.max_attempts} attempts")
                    self._update_retry_stats(func_name, attempt + 1, False)
                    break
                
                # Calculate delay and wait
                delay = config.calculate_delay(attempt)
                self.logger.info(f"{func_name} failed (attempt {attempt + 1}), retrying in {delay:.2f}s: {e}")
                
                if delay > 0:
                    time.sleep(delay)
        
        # All attempts failed
        if isinstance(last_exception, BaseScraperException):
            # Update retry count in exception
            if hasattr(last_exception, 'retry_count'):
                last_exception.retry_count = config.max_attempts - 1
            raise last_exception
        else:
            # Wrap in RetryableException
            raise RetryableException(
                f"Operation failed after {config.max_attempts} attempts: {last_exception}",
                retry_count=config.max_attempts - 1,
                max_retries=config.max_attempts - 1
            ) from last_exception
    
    async def _execute_async_with_retry(self, func: Callable, config: RetryConfig, *args, **kwargs) -> Any:
        """Execute async function with retry logic."""
        func_name = f"{func.__module__}.{func.__name__}"
        last_exception = None
        
        for attempt in range(config.max_attempts):
            try:
                self.logger.debug(f"Executing async {func_name}, attempt {attempt + 1}/{config.max_attempts}")
                result = await func(*args, **kwargs)
                
                # Log successful retry if not first attempt
                if attempt > 0:
                    self.logger.info(f"Async {func_name} succeeded on attempt {attempt + 1}")
                    self._update_retry_stats(func_name, attempt + 1, True)
                    
                return result
                
            except Exception as e:
                last_exception = e
                
                # Check if exception is retryable
                if not self._is_retryable_exception(e, config):
                    self.logger.debug(f"Async {func_name} failed with non-retryable exception: {e}")
                    self._update_retry_stats(func_name, attempt + 1, False)
                    raise
                
                # Check if we have more attempts
                if attempt >= config.max_attempts - 1:
                    self.logger.warning(f"Async {func_name} failed after {config.max_attempts} attempts")
                    self._update_retry_stats(func_name, attempt + 1, False)
                    break
                
                # Calculate delay and wait
                delay = config.calculate_delay(attempt)
                self.logger.info(f"Async {func_name} failed (attempt {attempt + 1}), retrying in {delay:.2f}s: {e}")
                
                if delay > 0:
                    await asyncio.sleep(delay)
        
        # All attempts failed
        if isinstance(last_exception, BaseScraperException):
            # Update retry count in exception
            if hasattr(last_exception, 'retry_count'):
                last_exception.retry_count = config.max_attempts - 1
            raise last_exception
        else:
            # Wrap in RetryableException
            raise RetryableException(
                f"Async operation failed after {config.max_attempts} attempts: {last_exception}",
                retry_count=config.max_attempts - 1,
                max_retries=config.max_attempts - 1
            ) from last_exception
    
    def _is_retryable_exception(self, exception: Exception, config: RetryConfig) -> bool:
        """Check if an exception is retryable based on configuration."""
        # Check if it's in the retryable exceptions list
        if isinstance(exception, config.retryable_exceptions):
            return True
            
        # Check if it's explicitly marked as retryable
        if isinstance(exception, RetryableException):
            return True
            
        # Check for specific error conditions that are typically retryable
        error_message = str(exception).lower()
        retryable_patterns = [
            "timeout", "connection", "network", "temporary", "rate limit",
            "service unavailable", "internal server error", "bad gateway"
        ]
        
        return any(pattern in error_message for pattern in retryable_patterns)
    
    def _update_retry_stats(self, func_name: str, attempts: int, success: bool):
        """Update retry statistics for monitoring."""
        if func_name not in self.retry_stats:
            self.retry_stats[func_name] = {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_attempts": 0,
                "max_attempts_used": 0
            }
        
        stats = self.retry_stats[func_name]
        stats["total_calls"] += 1
        stats["total_attempts"] += attempts
        stats["max_attempts_used"] = max(stats["max_attempts_used"], attempts)
        
        if success:
            stats["successful_calls"] += 1
        else:
            stats["failed_calls"] += 1
    
    def get_retry_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get retry statistics for monitoring."""
        return self.retry_stats.copy()
    
    def reset_stats(self):
        """Reset retry statistics."""
        self.retry_stats.clear()


class FallbackManager:
    """
    Manages fallback mechanisms when primary operations fail.
    Provides graceful degradation for various application components.
    """
    
    def __init__(self):
        """Initialize fallback manager."""
        self.logger = get_logger("FallbackManager")
        self.fallback_handlers: Dict[str, List[Callable]] = {}
        self.fallback_stats: Dict[str, Dict[str, Any]] = {}
        
    def register_fallback(self, operation_name: str, fallback_func: Callable, priority: int = 0):
        """
        Register a fallback function for an operation.
        
        Args:
            operation_name: Name of the operation
            fallback_func: Fallback function to call
            priority: Priority (lower numbers = higher priority)
        """
        if operation_name not in self.fallback_handlers:
            self.fallback_handlers[operation_name] = []
            
        self.fallback_handlers[operation_name].append((priority, fallback_func))
        # Sort by priority
        self.fallback_handlers[operation_name].sort(key=lambda x: x[0])
        
        self.logger.info(f"Registered fallback for {operation_name} with priority {priority}")
    
    def execute_with_fallback(self, operation_name: str, primary_func: Callable, 
                            *args, **kwargs) -> Any:
        """
        Execute function with fallback mechanisms.
        
        Args:
            operation_name: Name of the operation for fallback lookup
            primary_func: Primary function to execute
            *args, **kwargs: Arguments for the function
            
        Returns:
            Result from primary function or fallback
        """
        try:
            self.logger.debug(f"Executing primary function for {operation_name}")
            result = primary_func(*args, **kwargs)
            self._update_fallback_stats(operation_name, "primary", True)
            return result
            
        except Exception as e:
            self.logger.warning(f"Primary function failed for {operation_name}: {e}")
            self._update_fallback_stats(operation_name, "primary", False)
            
            # Try fallback functions
            if operation_name in self.fallback_handlers:
                for priority, fallback_func in self.fallback_handlers[operation_name]:
                    try:
                        self.logger.info(f"Trying fallback (priority {priority}) for {operation_name}")
                        result = fallback_func(*args, **kwargs)
                        self._update_fallback_stats(operation_name, f"fallback_{priority}", True)
                        return result
                        
                    except Exception as fallback_error:
                        self.logger.warning(f"Fallback {priority} failed for {operation_name}: {fallback_error}")
                        self._update_fallback_stats(operation_name, f"fallback_{priority}", False)
                        continue
            
            # All fallbacks failed, re-raise original exception
            self.logger.error(f"All fallbacks failed for {operation_name}")
            raise
    
    async def execute_async_with_fallback(self, operation_name: str, primary_func: Callable,
                                        *args, **kwargs) -> Any:
        """
        Execute async function with fallback mechanisms.
        
        Args:
            operation_name: Name of the operation for fallback lookup
            primary_func: Primary async function to execute
            *args, **kwargs: Arguments for the function
            
        Returns:
            Result from primary function or fallback
        """
        try:
            self.logger.debug(f"Executing primary async function for {operation_name}")
            result = await primary_func(*args, **kwargs)
            self._update_fallback_stats(operation_name, "primary", True)
            return result
            
        except Exception as e:
            self.logger.warning(f"Primary async function failed for {operation_name}: {e}")
            self._update_fallback_stats(operation_name, "primary", False)
            
            # Try fallback functions
            if operation_name in self.fallback_handlers:
                for priority, fallback_func in self.fallback_handlers[operation_name]:
                    try:
                        self.logger.info(f"Trying async fallback (priority {priority}) for {operation_name}")
                        
                        if asyncio.iscoroutinefunction(fallback_func):
                            result = await fallback_func(*args, **kwargs)
                        else:
                            result = fallback_func(*args, **kwargs)
                            
                        self._update_fallback_stats(operation_name, f"fallback_{priority}", True)
                        return result
                        
                    except Exception as fallback_error:
                        self.logger.warning(f"Async fallback {priority} failed for {operation_name}: {fallback_error}")
                        self._update_fallback_stats(operation_name, f"fallback_{priority}", False)
                        continue
            
            # All fallbacks failed, re-raise original exception
            self.logger.error(f"All async fallbacks failed for {operation_name}")
            raise
    
    def _update_fallback_stats(self, operation_name: str, handler_type: str, success: bool):
        """Update fallback statistics."""
        if operation_name not in self.fallback_stats:
            self.fallback_stats[operation_name] = {}
            
        if handler_type not in self.fallback_stats[operation_name]:
            self.fallback_stats[operation_name][handler_type] = {
                "attempts": 0,
                "successes": 0,
                "failures": 0
            }
        
        stats = self.fallback_stats[operation_name][handler_type]
        stats["attempts"] += 1
        
        if success:
            stats["successes"] += 1
        else:
            stats["failures"] += 1
    
    def get_fallback_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get fallback statistics."""
        return self.fallback_stats.copy()


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for preventing cascading failures.
    Temporarily disables failing operations to allow recovery.
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0,
                 expected_exception: Type[Exception] = Exception):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before attempting recovery
            expected_exception: Exception type that triggers circuit breaker
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
        
        self.logger = get_logger("CircuitBreaker")
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator for circuit breaker functionality."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self._execute_with_circuit_breaker(func, *args, **kwargs)
        return wrapper
    
    def _execute_with_circuit_breaker(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker logic."""
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half_open"
                self.logger.info("Circuit breaker moving to half-open state")
            else:
                raise Exception("Circuit breaker is open - operation not allowed")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
            
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful operation."""
        if self.state == "half_open":
            self.state = "closed"
            self.failure_count = 0
            self.logger.info("Circuit breaker reset to closed state")
    
    def _on_failure(self):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            self.logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


# Global instances
_global_retry_manager: Optional[RetryManager] = None
_global_fallback_manager: Optional[FallbackManager] = None


def get_retry_manager() -> RetryManager:
    """Get global retry manager instance."""
    global _global_retry_manager
    if _global_retry_manager is None:
        _global_retry_manager = RetryManager()
    return _global_retry_manager


def get_fallback_manager() -> FallbackManager:
    """Get global fallback manager instance."""
    global _global_fallback_manager
    if _global_fallback_manager is None:
        _global_fallback_manager = FallbackManager()
    return _global_fallback_manager


# Convenience decorators using global instances
def retry_on_failure(config: Optional[RetryConfig] = None):
    """Convenience decorator for retry functionality."""
    return get_retry_manager().retry(config)


def async_retry_on_failure(config: Optional[RetryConfig] = None):
    """Convenience decorator for async retry functionality."""
    return get_retry_manager().async_retry(config)


def with_fallback(operation_name: str):
    """Convenience decorator for fallback functionality."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return get_fallback_manager().execute_with_fallback(operation_name, func, *args, **kwargs)
        return wrapper
    return decorator


def with_async_fallback(operation_name: str):
    """Convenience decorator for async fallback functionality."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await get_fallback_manager().execute_async_with_fallback(operation_name, func, *args, **kwargs)
        return wrapper
    return decorator