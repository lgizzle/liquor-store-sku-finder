"""
Production-ready improvements for the SKU Finder app.
Address security, performance, and deployment concerns.
"""

import logging
import sys
from functools import wraps
from flask import jsonify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def handle_errors(f):
    """Decorator for consistent error handling"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'An internal error occurred. Please try again later.'
            }), 500
    return decorated_function

def validate_sku(sku):
    """Validate SKU format"""
    if not sku or not isinstance(sku, str):
        return False
    
    # Remove whitespace and check length
    sku = sku.strip()
    if len(sku) < 8 or len(sku) > 20:
        return False
    
    # Check if it's numeric (basic UPC format)
    return sku.isdigit()

class RateLimiter:
    """Simple rate limiting for API calls"""
    def __init__(self, max_requests=60, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    def is_allowed(self, key):
        import time
        now = time.time()
        
        # Clean old entries
        self.requests = {k: v for k, v in self.requests.items() 
                        if now - v['first_request'] < self.window_seconds}
        
        if key not in self.requests:
            self.requests[key] = {'count': 1, 'first_request': now}
            return True
        
        if self.requests[key]['count'] < self.max_requests:
            self.requests[key]['count'] += 1
            return True
        
        return False
