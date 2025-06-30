# Configuration settings for SKU Picture Finder

# API Settings
DEFAULT_MAX_IMAGES = 5
DEFAULT_OUTPUT_DIR = "./images"
REQUEST_TIMEOUT = 30
SCRAPING_DELAY = 1
MAX_RETRIES = 3

# Supported image formats
SUPPORTED_IMAGE_FORMATS = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"]

# User agent for web requests
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# API Endpoints
OPEN_FOOD_FACTS_API = "https://world.openfoodfacts.org/api/v0/product/{}.json"
UPC_DATABASE_API = "https://api.upcitemdb.com/prod/trial/lookup"
EBAY_BROWSE_API = "https://api.ebay.com/buy/browse/v1/item_summary/search"

# Rate limiting (requests per minute)
RATE_LIMITS = {
    "open_food_facts": 60,
    "upc_database": 30,
    "ebay": 100,
    "google_images": 10,
    "duckduckgo": 15,
}

# Confidence thresholds
MIN_CONFIDENCE_THRESHOLD = 0.1
HIGH_CONFIDENCE_THRESHOLD = 0.8

# File naming patterns
IMAGE_FILENAME_PATTERN = "{source}_{timestamp}{extension}"
EXPORT_FILENAME_PATTERN = "sku_results_{timestamp}.csv"
LOG_FILENAME_PATTERN = "sku_finder_{date}.log"

# Image quality settings
MINIMUM_IMAGE_WIDTH = 300   # Lowered from 600 for better results
MINIMUM_IMAGE_HEIGHT = 300  # Lowered from 600 for better results
