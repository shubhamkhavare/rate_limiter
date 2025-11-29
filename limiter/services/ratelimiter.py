from datetime import timedelta
from django.utils import timezone
from django.core.cache import cache
from rest_framework import status
from rest_framework.response import Response
from limiter.models import RateLimitLog


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    pass


class RateLimiter:
    """
    Advanced rate limiter with sliding window, caching, and multiple strategies.
    """
    
    # Simple in-memory cache (can be replaced with Redis in production)
    _cache = {}
    _cache_ttl = {}
    
    @staticmethod
    def _get_cache_key(identifier, endpoint):
        """Generate cache key for identifier and endpoint combination."""
        return f"ratelimit:{identifier}:{endpoint}"
    
    @staticmethod
    def _clean_old_cache_entries():
        """Clean expired cache entries periodically."""
        current_time = timezone.now()
        expired_keys = [
            key for key, expiry in RateLimiter._cache_ttl.items()
            if expiry < current_time
        ]
        for key in expired_keys:
            RateLimiter._cache.pop(key, None)
            RateLimiter._cache_ttl.pop(key, None)
    
    @staticmethod
    def _get_from_cache(identifier, endpoint, window_seconds):
        """Get cached count if available and valid."""
        cache_key = RateLimiter._get_cache_key(identifier, endpoint)
        cache_data = RateLimiter._cache.get(cache_key)
        
        if cache_data:
            cache_time, cache_count = cache_data
            cache_age = (timezone.now() - cache_time).total_seconds()
            
            # If cache is still within window, return cached count
            if cache_age < window_seconds:
                return cache_count
        
        return None
    
    @staticmethod
    def _set_cache(identifier, endpoint, count, window_seconds):
        """Set cache with TTL."""
        cache_key = RateLimiter._get_cache_key(identifier, endpoint)
        RateLimiter._cache[cache_key] = (timezone.now(), count)
        RateLimiter._cache_ttl[cache_key] = timezone.now() + timedelta(seconds=window_seconds)
    
    @staticmethod
    def _count_requests_sliding_window(identifier, endpoint, window_seconds):
        """
        Count requests in sliding window using database query.
        Optimized with filtered query ranges and indexes.
        """
        now = timezone.now()
        window_start = now - timedelta(seconds=window_seconds)
        
        # Use optimized query with index on (identifier, endpoint, timestamp)
        count = RateLimitLog.objects.filter(
            identifier=identifier,
            endpoint=endpoint,
            timestamp__gte=window_start,
            timestamp__lte=now
        ).count()
        
        return count
    
    @staticmethod
    def _count_requests_fixed_window(identifier, endpoint, window_seconds):
        """
        Count requests in fixed window (bucket-based).
        Less accurate but more performant.
        """
        from datetime import datetime
        now = timezone.now()
        
        # Round down to window boundary
        # Calculate seconds since epoch
        epoch_seconds = int(now.timestamp())
        # Round down to nearest window boundary
        window_start_seconds = (epoch_seconds // window_seconds) * window_seconds
        window_start = timezone.make_aware(datetime.fromtimestamp(window_start_seconds))
        
        count = RateLimitLog.objects.filter(
            identifier=identifier,
            endpoint=endpoint,
            timestamp__gte=window_start,
            timestamp__lte=now
        ).count()
        
        return count
    
    @staticmethod
    def check_limit(identifier, endpoint, limit, window_seconds, strategy='sliding', use_cache=True):
        """
        Check if request is within rate limit.
        
        Args:
            identifier: IP address, user_id, or API key
            endpoint: The API endpoint being accessed
            limit: Maximum number of requests allowed
            window_seconds: Time window in seconds
            strategy: 'sliding' or 'fixed' window strategy
            use_cache: Whether to use caching (default: True)
        
        Returns:
            tuple: (is_allowed: bool, remaining_requests: int, reset_time: datetime)
        
        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        # Clean old cache entries periodically
        if len(RateLimiter._cache) > 1000:
            RateLimiter._clean_old_cache_entries()
        
        # Try to get from cache first
        cached_count = None
        if use_cache:
            cached_count = RateLimiter._get_from_cache(identifier, endpoint, window_seconds)
        
        if cached_count is not None:
            current_count = cached_count
        else:
            # Query database based on strategy
            if strategy == 'sliding':
                current_count = RateLimiter._count_requests_sliding_window(
                    identifier, endpoint, window_seconds
                )
            else:  # fixed
                current_count = RateLimiter._count_requests_fixed_window(
                    identifier, endpoint, window_seconds
                )
            
            # Cache the result
            if use_cache:
                RateLimiter._set_cache(identifier, endpoint, current_count, window_seconds)
        
        # Check if limit exceeded
        if current_count >= limit:
            reset_time = timezone.now() + timedelta(seconds=window_seconds)
            raise RateLimitExceeded(
                f"Rate limit exceeded: {current_count}/{limit} requests in {window_seconds}s"
            )
        
        # Log the request
        RateLimitLog.objects.create(
            identifier=identifier,
            endpoint=endpoint
        )
        
        # Update cache
        if use_cache:
            new_count = current_count + 1
            RateLimiter._set_cache(identifier, endpoint, new_count, window_seconds)
        
        remaining = limit - (current_count + 1)
        reset_time = timezone.now() + timedelta(seconds=window_seconds)
        
        return True, remaining, reset_time
    
    @staticmethod
    def get_rate_limit_response(identifier, endpoint, limit, window_seconds):
        """
        Get a DRF Response for rate limit exceeded.
        """
        try:
            is_allowed, remaining, reset_time = RateLimiter.check_limit(
                identifier, endpoint, limit, window_seconds
            )
            return None  # Request is allowed
        except RateLimitExceeded as e:
            return Response(
                {
                    "error": "Rate limit exceeded",
                    "message": str(e),
                    "limit": limit,
                    "window_seconds": window_seconds,
                    "retry_after": window_seconds
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

