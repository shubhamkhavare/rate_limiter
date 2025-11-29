from django.test import TestCase, Client
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from limiter.models import RateLimitLog
from limiter.services.ratelimiter import RateLimiter, RateLimitExceeded


class RateLimiterTestCase(TestCase):
    """Test cases for RateLimiter utility."""
    
    def setUp(self):
        """Set up test data."""
        self.identifier = "test_user_123"
        self.endpoint = "/api/test/"
        self.limit = 5
        self.window_seconds = 60
        
        # Clear cache before each test
        RateLimiter._cache.clear()
        RateLimiter._cache_ttl.clear()
    
    def test_rate_limit_allowed(self):
        """Test that requests within limit are allowed."""
        # Make requests up to limit
        for i in range(self.limit):
            is_allowed, remaining, reset_time = RateLimiter.check_limit(
                self.identifier,
                self.endpoint,
                self.limit,
                self.window_seconds
            )
            self.assertTrue(is_allowed)
            self.assertEqual(remaining, self.limit - (i + 1))
        
        # Verify logs were created
        self.assertEqual(
            RateLimitLog.objects.filter(
                identifier=self.identifier,
                endpoint=self.endpoint
            ).count(),
            self.limit
        )
    
    def test_rate_limit_exceeded(self):
        """Test that requests exceeding limit raise RateLimitExceeded."""
        # Make requests up to limit
        for i in range(self.limit):
            RateLimiter.check_limit(
                self.identifier,
                self.endpoint,
                self.limit,
                self.window_seconds
            )
        
        # Next request should exceed limit
        with self.assertRaises(RateLimitExceeded):
            RateLimiter.check_limit(
                self.identifier,
                self.endpoint,
                self.limit,
                self.window_seconds
            )
    
    def test_sliding_window_strategy(self):
        """Test sliding window strategy."""
        # Make requests
        for i in range(3):
            RateLimiter.check_limit(
                self.identifier,
                self.endpoint,
                self.limit,
                self.window_seconds,
                strategy='sliding'
            )
        
        # Count should be 3
        count = RateLimitLog.objects.filter(
            identifier=self.identifier,
            endpoint=self.endpoint
        ).count()
        self.assertEqual(count, 3)
    
    def test_fixed_window_strategy(self):
        """Test fixed window strategy."""
        # Make requests
        for i in range(3):
            RateLimiter.check_limit(
                self.identifier,
                self.endpoint,
                self.limit,
                self.window_seconds,
                strategy='fixed'
            )
        
        # Count should be 3
        count = RateLimitLog.objects.filter(
            identifier=self.identifier,
            endpoint=self.endpoint
        ).count()
        self.assertEqual(count, 3)
    
    def test_caching(self):
        """Test that caching reduces database queries."""
        # First request - should hit DB
        RateLimiter.check_limit(
            self.identifier,
            self.endpoint,
            self.limit,
            self.window_seconds,
            use_cache=True
        )
        
        # Check cache was set
        cache_key = RateLimiter._get_cache_key(self.identifier, self.endpoint)
        self.assertIn(cache_key, RateLimiter._cache)
        
        # Second request - should use cache
        RateLimiter.check_limit(
            self.identifier,
            self.endpoint,
            self.limit,
            self.window_seconds,
            use_cache=True
        )
    
    def test_different_identifiers(self):
        """Test that different identifiers have separate limits."""
        identifier1 = "user1"
        identifier2 = "user2"
        
        # Both should be able to make requests
        RateLimiter.check_limit(identifier1, self.endpoint, self.limit, self.window_seconds)
        RateLimiter.check_limit(identifier2, self.endpoint, self.limit, self.window_seconds)
        
        # Both should have 1 log entry
        self.assertEqual(
            RateLimitLog.objects.filter(identifier=identifier1).count(),
            1
        )
        self.assertEqual(
            RateLimitLog.objects.filter(identifier=identifier2).count(),
            1
        )
    
    def test_different_endpoints(self):
        """Test that different endpoints have separate limits."""
        endpoint1 = "/api/endpoint1/"
        endpoint2 = "/api/endpoint2/"
        
        # Both should be able to make requests
        RateLimiter.check_limit(self.identifier, endpoint1, self.limit, self.window_seconds)
        RateLimiter.check_limit(self.identifier, endpoint2, self.limit, self.window_seconds)
        
        # Both should have 1 log entry
        self.assertEqual(
            RateLimitLog.objects.filter(endpoint=endpoint1).count(),
            1
        )
        self.assertEqual(
            RateLimitLog.objects.filter(endpoint=endpoint2).count(),
            1
        )


class PingViewTestCase(TestCase):
    """Test cases for PingView API endpoint."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
        RateLimiter._cache.clear()
        RateLimiter._cache_ttl.clear()
    
    def test_ping_success(self):
        """Test successful ping request."""
        response = self.client.get('/api/ping/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.json())
        self.assertEqual(response.json()['message'], 'pong')
    
    def test_ping_rate_limit(self):
        """Test ping endpoint rate limiting."""
        # Make 5 requests (the limit)
        for i in range(5):
            response = self.client.get('/api/ping/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 6th request should be rate limited
        response = self.client.get('/api/ping/')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('error', response.json())


class CustomLimitViewTestCase(TestCase):
    """Test cases for CustomLimitView API endpoint."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
        RateLimiter._cache.clear()
        RateLimiter._cache_ttl.clear()
    
    def test_custom_limit_success(self):
        """Test successful custom limit request."""
        data = {
            'identifier': 'test_user',
            'limit': 10,
            'window': 60
        }
        response = self.client.post(
            '/api/custom-limit/',
            data=data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.json())
    
    def test_custom_limit_validation(self):
        """Test custom limit validation."""
        # Missing identifier
        data = {'limit': 10, 'window': 60}
        response = self.client.post(
            '/api/custom-limit/',
            data=data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Invalid limit
        data = {'identifier': 'test', 'limit': -1, 'window': 60}
        response = self.client.post(
            '/api/custom-limit/',
            data=data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_custom_limit_rate_limit(self):
        """Test custom limit endpoint rate limiting."""
        data = {
            'identifier': 'shubham',
            'limit': 3,
            'window': 60
        }
        
        # Make 3 requests (the limit)
        for i in range(3):
            response = self.client.post(
                '/api/custom-limit/',
                data=data,
                content_type='application/json'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 4th request should be rate limited
        response = self.client.post(
            '/api/custom-limit/',
            data=data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class StatsViewTestCase(TestCase):
    """Test cases for StatsView API endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.identifier = 'test_user'
        
        # Create some test logs
        RateLimitLog.objects.create(
            identifier=self.identifier,
            endpoint='/api/ping/'
        )
        RateLimitLog.objects.create(
            identifier=self.identifier,
            endpoint='/api/custom-limit/'
        )
    
    def test_stats_success(self):
        """Test successful stats request."""
        response = self.client.get(f'/api/stats/{self.identifier}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('identifier', response.json())
        self.assertIn('total_requests', response.json())
        self.assertIn('by_endpoint', response.json())


class RateLimitLogModelTestCase(TestCase):
    """Test cases for RateLimitLog model."""
    
    def test_create_log(self):
        """Test creating a rate limit log."""
        log = RateLimitLog.objects.create(
            identifier='test_user',
            endpoint='/api/test/'
        )
        self.assertIsNotNone(log.id)
        self.assertEqual(log.identifier, 'test_user')
        self.assertEqual(log.endpoint, '/api/test/')
        self.assertIsNotNone(log.timestamp)
    
    def test_log_str_representation(self):
        """Test string representation of log."""
        log = RateLimitLog.objects.create(
            identifier='test_user',
            endpoint='/api/test/'
        )
        str_repr = str(log)
        self.assertIn('test_user', str_repr)
        self.assertIn('/api/test/', str_repr)
