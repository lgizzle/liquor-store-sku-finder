from flask import Flask, request, jsonify, render_template, send_from_directory, send_file
import os
import shutil
import urllib.request
import json
import hashlib
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from datetime import datetime

app = Flask(__name__)

# Enable CORS manually if flask-cors is not available
@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE")
    return response

# Create images directory if it doesn't exist
IMAGES_DIR = "images"
if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

def get_go_upc_api_key():
    """Get the Go-UPC API key from environment variables"""
    return os.environ.get('GO_UPC_API_KEY', '')

def search_go_upc(sku):
    """Search for product information using Go-UPC API with rate limiting"""
    from api_utils import search_go_upc_with_backoff
    try:
        return search_go_upc_with_backoff(sku)
    except Exception as e:
        raise Exception(f"Error calling Go-UPC API: {str(e)}")

def sanitize_filename(filename):
    """Sanitize filename to remove disallowed characters"""
    import re
    # Replace disallowed characters with underscores
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple underscores and trim
    sanitized = re.sub(r'_+', '_', sanitized).strip('_')
    # Limit length to prevent filesystem issues
    return sanitized[:100]

def create_product_package(product_data, sku):
    """Create a self-contained product folder with all data and assets"""
    if not product_data:
        return None
        
    try:
        # Create sanitized folder name: UPC--ProductName
        product_name = product_data.get('name', 'Unknown_Product')
        sanitized_name = sanitize_filename(product_name)
        folder_name = f"{sku}--{sanitized_name}"
        
        # Create the product folder
        product_folder = os.path.join(IMAGES_DIR, folder_name)
        if not os.path.exists(product_folder):
            os.makedirs(product_folder)
        
        # Download the product image
        image_path = None
        if product_data.get('imageUrl'):
            image_path = download_product_image(
                product_data['imageUrl'], 
                product_folder, 
                product_data.get('name', 'product')
            )
        
        # Create comprehensive product info JSON
        product_info = {
            "upc": sku,
            "name": product_data.get('name', ''),
            "description": product_data.get('description', ''),
            "brand": product_data.get('brand', ''),
            "category": product_data.get('category', ''),
            "region": product_data.get('region', ''),
            "specifications": product_data.get('specs', []),
            "image_url": product_data.get('imageUrl', ''),
            "local_image_path": os.path.basename(image_path) if image_path else None,
            "barcode_url": product_data.get('barcodeUrl', ''),
            "created_date": datetime.now().isoformat(),
            "source": "Go-UPC API"
        }
        
        # Save JSON file
        json_path = os.path.join(product_folder, 'product_info.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(product_info, f, indent=2, ensure_ascii=False)
        
        # Save human-readable text file
        txt_path = os.path.join(product_folder, 'product_info.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("PRODUCT INFORMATION\\n")
            f.write("==================\\n\\n")
            f.write(f"UPC: {sku}\\n")
            f.write(f"Name: {product_info['name']}\\n")
            f.write(f"Brand: {product_info['brand']}\\n")
            f.write(f"Category: {product_info['category']}\\n")
            f.write(f"Region: {product_info['region']}\\n\\n")
            f.write(f"Description:\\n{product_info['description']}\\n\\n")
            
            if product_info['specifications']:
                f.write("Specifications:\\n")
                for spec in product_info['specifications']:
                    if isinstance(spec, list) and len(spec) >= 2:
                        f.write(f"  {spec[0]}: {spec[1]}\\n")
            
            f.write(f"\\nImage URL: {product_info['image_url']}\\n")
        
        return {
            "folder_path": product_folder,
            "image_filename": os.path.basename(image_path) if image_path else None
        }
    except Exception as e:
        print(f"Error creating product package: {e}")
        return None

def download_product_image(image_url, product_folder, product_name):
    """Download image to the specific product folder - optimized single download"""
    if not image_url:
        return None
        
    try:
        import io
        from PIL import Image
        
        # Single request with proper headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        req = Request(image_url, headers=headers)
        with urlopen(req, timeout=10) as response:
            # Read image data once
            image_data = response.read()
        
        # Validate image and get dimensions
        try:
            with io.BytesIO(image_data) as img_buffer:
                img = Image.open(img_buffer)
                img.verify()  # Verify it's a valid image
                width, height = img.size
                
                # Skip tiny images (likely placeholders)
                if width < 50 or height < 50:
                    print(f"Skipping tiny image: {width}x{height}")
                    return None
                    
        except Exception as e:
            print(f"Invalid image format: {e}")
            return None
        
        # Get file extension from URL or content type
        parsed_url = urlparse(image_url)
        ext = os.path.splitext(parsed_url.path)[1]
        if not ext:
            ext = '.jpg'  # Default fallback
        
        # Create image filename
        image_filename = f"image{ext}"
        local_path = os.path.join(product_folder, image_filename)
        
        # Write image data to file
        with open(local_path, 'wb') as f:
            f.write(image_data)
        
        print(f"Downloaded image: {width}x{height} -> {local_path}")
        return local_path
        
    except Exception as e:
        print(f"Error downloading image from {image_url}: {e}")
        return None

@app.route("/")
def index():
    return render_template("liquor_store.html")

@app.route("/api/search", methods=["POST"])
def search_sku():
    from utils import validate_sku, handle_errors
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400
        
    sku = data.get("sku", "").strip()

    if not sku:
        return jsonify({"error": "SKU is required"}), 400
    
    if not validate_sku(sku):
        return jsonify({"error": "Invalid SKU format. Must be 8-20 digits."}), 400

    try:
        # Search using Go-UPC API
        upc_data = search_go_upc(sku)
        
        results = []
        
        if upc_data.get('product'):
            product = upc_data['product']
            product_name = product.get('name', 'Unknown Product')
            product_description = product.get('description', '')
            product_image = product.get('imageUrl', '')
            brand = product.get('brand', '')
            category = product.get('category', '')
            specs = product.get('specs', [])
            region = product.get('region', '')
            
            # Create product package (folder with all data and assets)
            package_info = create_product_package(product, sku)
            
            # Format specifications
            specs_text = ""
            if specs:
                specs_text = " | ".join([f"{spec[0]}: {spec[1]}" for spec in specs[:3]])  # First 3 specs
            
            # Create result in expected format with enhanced data
            result = {
                "sku": sku,
                "source": "Go-UPC",
                "image_url": product_image,
                "title": product_name,
                "price": None,  # Go-UPC doesn't provide price
                "description": product_description,
                "brand": brand,
                "category": category,
                "specs": specs_text,
                "region": region,
                "local_path": package_info["folder_path"] if package_info else None,
                "folder_name": os.path.basename(package_info["folder_path"]) if package_info else None,
                "image_filename": package_info["image_filename"] if package_info else None,
            }
            results.append(result)

        return jsonify({
            "success": True,
            "sku": sku,
            "results": results,
            "count": len(results),
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/batch", methods=["POST"])
def batch_search():
    data = request.get_json()
    skus = data.get("skus", [])

    if not skus:
        return jsonify({"error": "SKUs list is required"}), 400

    try:
        batch_results = {}
        
        for sku in skus:
            sku = sku.strip()
            if not sku:
                continue
                
            try:
                # Search using Go-UPC API
                upc_data = search_go_upc(sku)
                
                sku_results = []
                
                if upc_data.get('product'):
                    product = upc_data['product']
                    product_name = product.get('name', 'Unknown Product')
                    product_description = product.get('description', '')
                    product_image = product.get('imageUrl', '')
                    brand = product.get('brand', '')
                    category = product.get('category', '')
                    specs = product.get('specs', [])
                    region = product.get('region', '')
                    
                    # Create product package (folder with all data and assets)
                    package_info = create_product_package(product, sku)
                    
                    # Format specifications
                    specs_text = ""
                    if specs:
                        specs_text = " | ".join([f"{spec[0]}: {spec[1]}" for spec in specs[:3]])  # First 3 specs
                    
                    # Create result in expected format with enhanced data
                    result = {
                        "sku": sku,
                        "source": "Go-UPC",
                        "image_url": product_image,
                        "title": product_name,
                        "price": None,
                        "description": product_description,
                        "brand": brand,
                        "category": category,
                        "specs": specs_text,
                        "region": region,
                         "image_filename": package_info["image_filename"] if package_info else None,
                         "package_created": package_info is not None,
                         "local_path": package_info["folder_path"] if package_info else None,
                         "folder_name": os.path.basename(package_info["folder_path"]) if package_info else None,
                    }
                    
                    sku_results.append(result)
                
                batch_results[sku] = sku_results
                
            except Exception as e:
                print(f"Error processing SKU {sku}: {e}")
                batch_results[sku] = []

        return jsonify({
            "success": True,
            "results": batch_results,
            "processed": len(skus)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/browse-products")
def browse_products():
    """List all created product packages"""
    try:
        product_folders = []
        
        if os.path.exists(IMAGES_DIR):
            for item in os.listdir(IMAGES_DIR):
                item_path = os.path.join(IMAGES_DIR, item)
                if os.path.isdir(item_path) and '--' in item:
                    # Parse folder name (UPC--ProductName)
                    parts = item.split('--', 1)
                    if len(parts) == 2:
                        upc, product_name = parts
                        
                        # Check for product files
                        files = []
                        if os.path.exists(os.path.join(item_path, 'product_info.json')):
                            files.append('product_info.json')
                        if os.path.exists(os.path.join(item_path, 'product_info.txt')):
                            files.append('product_info.txt')
                        
                        # Find image file
                        for file in os.listdir(item_path):
                            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
                                files.append(file)
                                break
                        
                        product_folders.append({
                            "folder_name": item,
                            "upc": upc,
                            "product_name": product_name.replace('_', ' '),
                            "files": files,
                            "created_date": os.path.getctime(item_path)
                        })
        
        # Sort by creation date (newest first)
        product_folders.sort(key=lambda x: x['created_date'], reverse=True)
        
        return jsonify({
            "success": True,
            "products": product_folders,
            "count": len(product_folders)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/stats")
def get_stats():
    try:
        # Count product folders and files
        total_products = 0
        total_files = 0
        
        if os.path.exists(IMAGES_DIR):
            for item in os.listdir(IMAGES_DIR):
                item_path = os.path.join(IMAGES_DIR, item)
                if os.path.isdir(item_path) and '--' in item:
                    total_products += 1
                    # Count files in this product folder
                    for file in os.listdir(item_path):
                        file_path = os.path.join(item_path, file)
                        if os.path.isfile(file_path):
                            total_files += 1
        
        stats = {
            "total_products": total_products,
            "total_files": total_files,
            "avg_confidence": 1.0,
            "sources": {"Go-UPC": total_products}
        }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/export")
def export_results():
    try:
        return jsonify({
            "success": True,
            "filename": "Product folders available in file system",
            "message": "Products are organized in individual folders - no export needed",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Serve files from product folders
@app.route("/files/<folder_name>/<filename>")
def serve_product_file(folder_name, filename):
    """Serve individual files from product folders"""
    try:
        folder_path = os.path.join(IMAGES_DIR, folder_name)
        if not os.path.exists(folder_path):
            return jsonify({"error": "Product folder not found"}), 404
        
        file_path = os.path.join(folder_path, filename)
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
        
        return send_file(file_path)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/images/<path:filename>")
def serve_image(filename):
    return send_from_directory(IMAGES_DIR, filename)

@app.route("/api/save-selected", methods=["POST"])
def save_selected_images():
    """This endpoint is now mainly for compatibility - files are already organized"""
    data = request.get_json()
    sku = data.get("sku", "").strip()
    
    return jsonify({
        "success": True,
        "message": f"Product {sku} is already organized in its own folder",
        "remaining_count": 1,
    })

@app.route("/api/download", methods=["GET"])
def download_image_endpoint():
    """Serve an image for download with a custom filename"""
    local_path = request.args.get("local_path")
    sku = request.args.get("sku")
    title = request.args.get("title")
    
    if not local_path or not sku or not title:
        return jsonify({"error": "Missing parameters"}), 400
        
    try:
        # Sanitize filename
        safe_title = ''.join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip().replace(' ', '_')
        filename = f"{sku}-{safe_title}.jpg"
        
        # Serve the file
        return send_file(local_path, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, host="0.0.0.0", port=port)
