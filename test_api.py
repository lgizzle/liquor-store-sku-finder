import urllib.request
import json
import os
from urllib.request import Request, urlopen

# Test the Go-UPC API
product_code = '843248155091'
api_key = '011032ef800fbfd7de89ef7b56dc4dca354db908286d38b85100c619236912eb'

print(f"Testing Go-UPC API with product code: {product_code}")
print(f"API Key: {api_key[:20]}...")

try:
    req = Request('https://go-upc.com/api/v1/code/' + product_code)
    req.add_header('Authorization', 'Bearer ' + api_key)
    
    content = urlopen(req).read()
    data = json.loads(content.decode())
    
    print("\nAPI Response:")
    print(json.dumps(data, indent=2))
    
    if 'product' in data and data['product']:
        product_name = data["product"]["name"]
        product_description = data["product"]["description"]
        product_image = data["product"]["imageUrl"]
        
        print(f"\nProduct Name: {product_name}")
        print(f"Product Description: {product_description}")
        print(f"Product Image URL: {product_image}")
    else:
        print("No product data found")
        
except Exception as e:
    print(f"Error: {e}")
