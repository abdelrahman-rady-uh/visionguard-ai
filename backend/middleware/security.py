"""Rate limiting and security middleware for Flask."""
from flask import request, jsonify
from functools import wraps
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for API endpoints."""

    def __init__(self, requests_per_minute: int = 30):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests per minute per client
        """
        self.requests_per_minute = requests_per_minute
        self.client_requests = defaultdict(list)

    def get_client_id(self) -> str:
        """
        Get unique client identifier from request.
        
        Returns:
            Client IP address or session ID
        """
        # Try to get real IP from headers (behind proxy)
        if request.headers.get("X-Forwarded-For"):
            return request.headers.get("X-Forwarded-For").split(",")[0]
        
        return request.remote_addr or "unknown"

    def is_allowed(self) -> bool:
        """
        Check if current request should be allowed.
        
        Returns:
            True if request is within rate limit
        """
        client_id = self.get_client_id()
        now = datetime.now(timezone.utc)
        cutoff_time = now - timedelta(minutes=1)

        # Remove old requests
        self.client_requests[client_id] = [
            req_time for req_time in self.client_requests[client_id]
            if req_time > cutoff_time
        ]

        # Check if within limit
        if len(self.client_requests[client_id]) >= self.requests_per_minute:
            return False

        # Add current request
        self.client_requests[client_id].append(now)
        return True

    def get_remaining_requests(self) -> int:
        """
        Get remaining requests for client in current minute.
        
        Returns:
            Number of remaining requests
        """
        client_id = self.get_client_id()
        now = datetime.now(timezone.utc)
        cutoff_time = now - timedelta(minutes=1)

        # Remove old requests
        self.client_requests[client_id] = [
            req_time for req_time in self.client_requests[client_id]
            if req_time > cutoff_time
        ]

        remaining = max(0, self.requests_per_minute - len(self.client_requests[client_id]))
        return remaining


# Global rate limiter
rate_limiter = RateLimiter(requests_per_minute=30)


def rate_limit(requests_per_minute: int = None):
    """
    Decorator for rate limiting endpoints.
    
    Args:
        requests_per_minute: Override global limit for this endpoint
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            limiter = RateLimiter(requests_per_minute or 30)
            
            if not limiter.is_allowed():
                logger.warning(f"Rate limit exceeded for {request.remote_addr}")
                return jsonify({
                    "error": "Rate limit exceeded",
                    "retry_after": 60,
                }), 429

            response = f(*args, **kwargs)
            
            # Add rate limit headers
            if isinstance(response, tuple):
                resp_data, status_code = response
                headers = {
                    "X-RateLimit-Limit": str(requests_per_minute or 30),
                    "X-RateLimit-Remaining": str(limiter.get_remaining_requests()),
                }
                return resp_data, status_code, headers
            
            return response

        return decorated_function
    return decorator


class SecurityHeaders:
    """Add security headers to responses."""

    @staticmethod
    def add_security_headers(response):
        """
        Add security headers to Flask response.
        
        Args:
            response: Flask response object
            
        Returns:
            Modified response with security headers
        """
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "img-src 'self' data: blob: https:; "
            "font-src 'self' https://fonts.gstatic.com; "
            "media-src 'self' blob:; "
            "connect-src 'self'"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response


class InputValidator:
    """Validate and sanitize user inputs."""

    @staticmethod
    def validate_video_upload(file_obj) -> tuple[bool, str]:
        """
        Validate uploaded video file.
        
        Args:
            file_obj: File object from request
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file_obj or file_obj.filename == "":
            return False, "No file provided"

        # Check file extension
        allowed_extensions = {"mp4", "avi", "mov", "mkv", "webm"}
        filename = file_obj.filename.lower()
        
        if not any(filename.endswith("." + ext) for ext in allowed_extensions):
            return False, f"File type not allowed. Allowed: {', '.join(allowed_extensions)}"

        # Check file size (max 1GB)
        max_size = 1024 * 1024 * 1024
        file_obj.seek(0, 2)  # Seek to end
        size = file_obj.tell()
        file_obj.seek(0)  # Seek to beginning

        if size > max_size:
            return False, f"File too large. Maximum size: {max_size / (1024**3):.1f}GB"

        if size < 1024:  # At least 1KB
            return False, "File is too small (minimum 1KB)"

        return True, ""

    @staticmethod
    def validate_json_input(data: dict, required_fields: list) -> tuple[bool, str]:
        """
        Validate JSON input.
        
        Args:
            data: Dictionary to validate
            required_fields: List of required field names
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        missing_fields = [f for f in required_fields if f not in data or data[f] is None]
        
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"

        return True, ""

    @staticmethod
    def sanitize_string(s: str, max_length: int = 1000) -> str:
        """
        Sanitize string input.
        
        Args:
            s: String to sanitize
            max_length: Maximum length
            
        Returns:
            Sanitized string
        """
        if not isinstance(s, str):
            return ""

        # Remove null bytes
        s = s.replace("\x00", "")

        # Limit length
        s = s[:max_length]

        return s.strip()
