import time
import logging
from typing import Dict, Any, Optional, Callable, TypeVar, Generic, List
from threading import Lock

logger = logging.getLogger(__name__)

T = TypeVar('T')

class CacheEntry(Generic[T]):
    """A cache entry with expiration time."""
    
    def __init__(self, value: T, ttl: float = 30.0):
        """
        Initialize a cache entry.
        
        Args:
            value: The cached value
            ttl: Time to live in seconds (default: 30 seconds)
        """
        self.value = value
        self.expiry = time.time() + ttl
        
    def is_expired(self) -> bool:
        """Check if the cache entry is expired."""
        return time.time() > self.expiry

class ResourceCache:
    """
    Cache for resource providers to improve performance.
    
    This class provides a simple time-based cache for resource providers.
    Resources are cached for a configurable amount of time to reduce
    the number of expensive operations (like querying FreeCAD).
    """
    
    def __init__(self, default_ttl: float = 30.0, max_size: int = 100):
        """
        Initialize the resource cache.
        
        Args:
            default_ttl: Default time to live in seconds (default: 30 seconds)
            max_size: Maximum number of entries in the cache (default: 100)
        """
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.cache: Dict[str, CacheEntry] = {}
        self.lock = Lock()
        self.hits = 0
        self.misses = 0
        logger.info(f"Initialized resource cache with TTL={default_ttl}s, max_size={max_size}")
        
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            The cached value, or None if not in cache or expired
        """
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                if entry.is_expired():
                    logger.debug(f"Cache entry for '{key}' is expired")
                    del self.cache[key]
                    self.misses += 1
                    return None
                logger.debug(f"Cache hit for '{key}'")
                self.hits += 1
                return entry.value
            logger.debug(f"Cache miss for '{key}'")
            self.misses += 1
            return None
            
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: The cache key
            value: The value to cache
            ttl: Optional custom TTL, otherwise uses default
        """
        with self.lock:
            # If cache is full, remove oldest entries
            if len(self.cache) >= self.max_size:
                self._evict_entries()
                
            # Set the new entry
            self.cache[key] = CacheEntry(value, ttl or self.default_ttl)
            logger.debug(f"Cached value for '{key}' (TTL={ttl or self.default_ttl}s)")
            
    def invalidate(self, key: str) -> None:
        """
        Invalidate a specific cache entry.
        
        Args:
            key: The cache key to invalidate
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                logger.debug(f"Invalidated cache entry for '{key}'")
                
    def invalidate_pattern(self, pattern: str) -> None:
        """
        Invalidate all cache entries matching a pattern.
        
        Args:
            pattern: The pattern to match against cache keys
        """
        with self.lock:
            keys_to_remove = [k for k in self.cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self.cache[key]
            logger.debug(f"Invalidated {len(keys_to_remove)} cache entries matching pattern '{pattern}'")
                
    def clear(self) -> None:
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
            logger.debug("Cleared entire cache")
            
    def _evict_entries(self) -> None:
        """Evict old entries when cache is full."""
        # First, remove expired entries
        expired_keys = [k for k, v in self.cache.items() if v.is_expired()]
        for key in expired_keys:
            del self.cache[key]
            
        # If still too many entries, remove oldest based on expiry time
        if len(self.cache) >= self.max_size:
            sorted_keys = sorted(self.cache.keys(), key=lambda k: self.cache[k].expiry)
            # Remove 20% of the oldest entries
            keys_to_remove = sorted_keys[:max(1, int(self.max_size * 0.2))]
            for key in keys_to_remove:
                del self.cache[key]
                
        logger.debug(f"Evicted old cache entries, new size: {len(self.cache)}")
        
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total = self.hits + self.misses
            hit_rate = self.hits / total if total > 0 else 0.0
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "default_ttl": self.default_ttl
            }
            
    def __len__(self) -> int:
        """Get the number of entries in the cache."""
        with self.lock:
            return len(self.cache)

def cached_resource(cache: ResourceCache, key_prefix: str = "", ttl: Optional[float] = None):
    """
    Decorator for caching resource provider methods.
    
    Args:
        cache: The cache instance to use
        key_prefix: Optional prefix for cache keys
        ttl: Optional custom TTL for this method
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            # Generate a cache key from the function name and arguments
            arg_str = ",".join([str(arg) for arg in args[1:]])  # Skip self
            kwarg_str = ",".join([f"{k}={v}" for k, v in kwargs.items()])
            cache_key = f"{key_prefix}:{func.__name__}:{arg_str}:{kwarg_str}"
            
            # Try to get from cache first
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
                
            # Not in cache, call the original function
            result = await func(*args, **kwargs)
            
            # Cache the result
            cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator 