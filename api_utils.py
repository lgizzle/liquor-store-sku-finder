import time
import random
from urllib.error import HTTPError

class APIRateLimiter:
    """Exponential backoff for API rate limiting"""
    
    def __init__(self, base_delay=1, max_delay=60, max_retries=3):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
    
    def execute_with_backoff(self, func, *args, **kwargs):
        """Execute function with exponential backoff on rate limit errors"""
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except HTTPError as e:
                if e.code == 429:  # Too Many Requests
                    if attempt < self.max_retries:
                        delay = min(
                            self.base_delay * (2 ** attempt) + random.uniform(0, 1),
                            self.max_delay
                        )
                        print(f"Rate limited. Waiting {delay:.1f}s before retry {attempt + 1}/{self.max_retries}")
                        time.sleep(delay)
                        continue
                    else:
                        raise Exception("API rate limit exceeded. Please try again later.")
                else:
                    raise e
            except Exception as e:
                # For other errors, don't retry
                raise e
        
        raise Exception("Max retries exceeded")

def search_go_upc_with_backoff(sku):
    """Search with rate limiting protection"""
    rate_limiter = APIRateLimiter()
    
    def _search():
        import os
        from urllib.request import Request, urlopen
        import json
        
        api_key = os.environ.get('GO_UPC_API_KEY', '')
        if not api_key:
            raise Exception("Go-UPC API key not configured")
        
        req = Request(f'https://go-upc.com/api/v1/code/{sku}')
        req.add_header('Authorization', f'Bearer {api_key}')
        
        with urlopen(req, timeout=10) as response:
            content = response.read()
            return json.loads(content.decode())
    
    return rate_limiter.execute_with_backoff(_search)
