import os
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

api_key = os.getenv('GO_UPC_API_KEY')
product_code = '843248155091'  # Example UPC

if not api_key:
    print("GO_UPC_API_KEY not found in environment.")
    exit(1)

url = f'https://go-upc.com/api/v1/code/{product_code}'
req = Request(url)
req.add_header('Authorization', 'Bearer ' + api_key)

try:
    content = urlopen(req).read()
    data = json.loads(content.decode())
    product = data.get("product", {})
    product_name = product.get("name", "N/A")
    product_description = product.get("description", "N/A")
    product_image = product.get("imageUrl", "N/A")

    print("Product Name:", product_name)
    print("Product Description:", product_description)
    print("Product Image URL:", product_image)
except HTTPError as e:
    print("HTTP Error:", e.code, e.reason)
except URLError as e:
    print("URL Error:", e.reason)
except Exception as e:
    print("Error:", e)
