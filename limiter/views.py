from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db.models import Count, Max
from django.utils import timezone
from datetime import timedelta
from limiter.services.ratelimiter import RateLimiter, RateLimitExceeded
from limiter.models import RateLimitLog


class PingView(APIView):
    """
    Demo endpoint to test rate limiting.
    Rate limit: 5 requests per minute per IP.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Get IP from middleware or fallback
        identifier = getattr(request, 'client_ip', request.META.get('REMOTE_ADDR', '127.0.0.1'))
        endpoint = '/api/ping/'
        limit = 5
        window_seconds = 60  # 1 minute
        
        try:
            is_allowed, remaining, reset_time = RateLimiter.check_limit(
                identifier=identifier,
                endpoint=endpoint,
                limit=limit,
                window_seconds=window_seconds,
                strategy='sliding',
                use_cache=True
            )
            
            return Response({
                "message": "pong",
                "remaining_requests": remaining,
                "reset_time": reset_time.isoformat()
            }, status=status.HTTP_200_OK)
        
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


class CustomLimitView(APIView):
    """
    Endpoint that accepts dynamic rate limit parameters.
    POST /api/custom-limit/
    Body: {
        "identifier": "shubham",
        "limit": 10,
        "window": 60
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        identifier = request.data.get('identifier')
        limit = request.data.get('limit')
        window = request.data.get('window')
        strategy = request.data.get('strategy', 'sliding')
        
        # Validation
        if not identifier:
            return Response(
                {"error": "identifier is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not limit or not isinstance(limit, int) or limit <= 0:
            return Response(
                {"error": "limit must be a positive integer"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not window or not isinstance(window, int) or window <= 0:
            return Response(
                {"error": "window must be a positive integer (seconds)"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if strategy not in ['sliding', 'fixed']:
            return Response(
                {"error": "strategy must be 'sliding' or 'fixed'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        endpoint = '/api/custom-limit/'
        
        try:
            is_allowed, remaining, reset_time = RateLimiter.check_limit(
                identifier=identifier,
                endpoint=endpoint,
                limit=limit,
                window_seconds=window,
                strategy=strategy,
                use_cache=True
            )
            
            return Response({
                "message": "Request allowed",
                "identifier": identifier,
                "remaining_requests": remaining,
                "limit": limit,
                "window_seconds": window,
                "reset_time": reset_time.isoformat()
            }, status=status.HTTP_200_OK)
        
        except RateLimitExceeded as e:
            return Response(
                {
                    "error": "Rate limit exceeded",
                    "message": str(e),
                    "identifier": identifier,
                    "limit": limit,
                    "window_seconds": window,
                    "retry_after": window
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )


class StatsView(APIView):
    """
    Endpoint to view request statistics for an identifier.
    GET /api/stats/<identifier>/
    Returns count of requests grouped by endpoint.
    """
    permission_classes = [AllowAny]
    
    def get(self, request, identifier):
        # Optional query params
        hours = int(request.query_params.get('hours', 24))
        
        # Calculate time range
        now = timezone.now()
        start_time = now - timedelta(hours=hours)
        
        # Get stats grouped by endpoint
        stats = RateLimitLog.objects.filter(
            identifier=identifier,
            timestamp__gte=start_time
        ).values('endpoint').annotate(
            count=Count('id'),
            last_request=Max('timestamp')
        ).order_by('-count')
        
        # Get total count
        total_requests = RateLimitLog.objects.filter(
            identifier=identifier,
            timestamp__gte=start_time
        ).count()
        
        # Get recent requests
        recent_requests = RateLimitLog.objects.filter(
            identifier=identifier,
            timestamp__gte=start_time
        ).order_by('-timestamp')[:10]
        
        return Response({
            "identifier": identifier,
            "time_range_hours": hours,
            "start_time": start_time.isoformat(),
            "end_time": now.isoformat(),
            "total_requests": total_requests,
            "by_endpoint": list(stats),
            "recent_requests": [
                {
                    "endpoint": req.endpoint,
                    "timestamp": req.timestamp.isoformat()
                }
                for req in recent_requests
            ]
        }, status=status.HTTP_200_OK)
