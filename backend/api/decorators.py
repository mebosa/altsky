from functools import wraps
from django.core.cache import cache
from rest_framework.response import Response
from django.conf import settings

def rate_limit(key_prefix, requests=5, window=60):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            client_ip = request.META.get('HTTP_X_FORWARDED_FOR', '') or request.META.get('REMOTE_ADDR')
            cache_key = f"ratelimit:{key_prefix}:{client_ip}"
            
            # Get the current request count for this IP
            request_count = cache.get(cache_key, 0)
            
            # If request count exceeds limit, return 429 Too Many Requests
            if request_count >= requests:
                return Response(
                    {"error": "too_many_requests", "message": "Too many requests. Please try again later."},
                    status=429
                )
            
            # Increment the request count
            if request_count == 0:
                # First request - set with expiry
                cache.set(cache_key, 1, window)
            else:
                # Increment existing counter
                cache.incr(cache_key)
            
            try:
                # Call the view function
                return view_func(request, *args, **kwargs)
            except ConnectionError:
                # Handle broken pipe and other connection errors gracefully
                return Response(
                    {"error": "connection_error", "message": "The connection was interrupted. Please try again."},
                    status=500
                )
                
        return _wrapped_view
    return decorator