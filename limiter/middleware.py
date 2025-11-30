class IPExtractionMiddleware:
    """
    Middleware to extract and attach IP address to request object.
    Handles various proxy scenarios (X-Forwarded-For, X-Real-IP, etc.)
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Extract IP address
        ip_address = self.get_client_ip(request)
        request.client_ip = ip_address
        
        response = self.get_response(request)
        return response
    
    @staticmethod
    def get_client_ip(request):
        """
        Extract client IP address from request.
        Handles proxies, load balancers, etc.
        """
        # Check X-Forwarded-For header (most common in production)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # X-Forwarded-For can contain multiple IPs, take the first one
            ip = x_forwarded_for.split(',')[0].strip()
            return ip
        
        # Check X-Real-IP header
        x_real_ip = request.META.get('HTTP_X_REAL_IP')
        if x_real_ip:
            return x_real_ip.strip()
        
        # Fall back to REMOTE_ADDR
        return request.META.get('REMOTE_ADDR', '127.0.0.1')


