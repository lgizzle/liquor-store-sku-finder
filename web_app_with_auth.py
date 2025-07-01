from flask import Flask, request, jsonify, render_template, send_from_directory, send_file, session, redirect, url_for, flash
import os
import shutil
import urllib.request
import json
import hashlib
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from datetime import datetime
from functools import wraps
from simple_auth import SimpleAuth
from auth_config import AuthConfig

app = Flask(__name__)
app.secret_key = AuthConfig().SECRET_KEY

# Initialize authentication
auth = SimpleAuth()

# Create superadmin on startup
auth.create_superadmin_if_not_exists()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Superadmin required decorator
def superadmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            return redirect(url_for('login'))
        
        user = auth.get_user_by_email(session['user_email'])
        if not user or not user.get('is_superadmin'):
            return jsonify({'error': 'Access denied'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

# Enable CORS manually if flask-cors is not available
@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE")
    return response

# Authentication Routes
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        result = auth.verify_user(email, password)
        if result['success']:
            session['user_email'] = email
            return redirect(url_for('index'))
        else:
            return render_template('login.html', message=result['error'], message_type='error')
    
    return render_template('login.html')

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        
        if password != confirm_password:
            return render_template('register.html', message="Passwords don't match", message_type='error')
        
        if len(password) < 6:
            return render_template('register.html', message="Password must be at least 6 characters", message_type='error')
        
        result = auth.create_user(email, password)
        if result['success']:
            return render_template('login.html', message="Account created! Please login.", message_type='success')
        else:
            return render_template('register.html', message=result['error'], message_type='error')
    
    return render_template('register.html')

@app.route("/logout")
def logout():
    session.pop('user_email', None)
    return redirect(url_for('login'))

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        result = auth.generate_reset_token(email)
        
        if result['success']:
            return render_template('login.html', message="Password reset email sent!", message_type='success')
        else:
            return render_template('login.html', message=result['error'], message_type='error')
    
    return render_template('login.html')

# Create images directory if it doesn't exist
IMAGES_DIR = "images"
if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

def get_go_upc_api_key():
    """Get the Go-UPC API key from environment variables"""
    return os.environ.get('GO_UPC_API_KEY', '')

def search_go_upc(sku):
    """Search for product information using Go-UPC API"""
    api_key = get_go_upc_api_key()
    if not api_key:
        raise Exception("Go-UPC API key not configured")
    
    try:
        req = Request(f'https://go-upc.com/api/v1/code/{sku}')
        req.add_header('Authorization', f'Bearer {api_key}')
        
        content = urlopen(req).read()
        data = json.loads(content.decode())
        
        return data
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

def create_product_package(product_data, sku, full_api_response=None):
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
        image_filename = None
        if product_data.get('imageUrl'):
            image_path = download_product_image(
                product_data['imageUrl'], 
                product_folder, 
                f"{sku}--{sanitized_name}--Image"
            )
            if image_path:
                image_filename = os.path.basename(image_path)
        
        # Save COMPLETE API response as JSON (matching frontend expectations)
        json_filename = f"{sku}--{sanitized_name}--Data.json"
        json_path = os.path.join(product_folder, json_filename)
        
        # Save the complete API response or create comprehensive data
        json_data = full_api_response if full_api_response else {
            "upc": sku,
            "name": product_data.get('name', ''),
            "description": product_data.get('description', ''),
            "brand": product_data.get('brand', ''),
            "category": product_data.get('category', ''),
            "region": product_data.get('region', ''),
            "specifications": product_data.get('specs', []),
            "image_url": product_data.get('imageUrl', ''),
            "barcode_url": product_data.get('barcodeUrl', ''),
            "created_date": datetime.now().isoformat(),
            "source": "Go-UPC API",
            "local_image_filename": image_filename
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        # Save human-readable text file (matching frontend expectations)
        txt_filename = f"{sku}--{sanitized_name}--Info.txt"
        txt_path = os.path.join(product_folder, txt_filename)
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("PRODUCT INFORMATION\n")
            f.write("==================\n\n")
            f.write(f"UPC: {sku}\n")
            f.write(f"Name: {product_data.get('name', '')}\n")
            f.write(f"Brand: {product_data.get('brand', '')}\n")
            f.write(f"Category: {product_data.get('category', '')}\n")
            f.write(f"Region: {product_data.get('region', '')}\n\n")
            
            description = product_data.get('description', '')
            if description:
                f.write(f"Description:\n{description}\n\n")
            
            specs = product_data.get('specs', [])
            if specs:
                f.write("Specifications:\n")
                for spec in specs:
                    if isinstance(spec, list) and len(spec) >= 2:
                        f.write(f"  {spec[0]}: {spec[1]}\n")
                    elif isinstance(spec, dict):
                        for key, value in spec.items():
                            f.write(f"  {key}: {value}\n")
                f.write("\n")
            
            f.write(f"Image URL: {product_data.get('imageUrl', '')}\n")
            f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        return {
            "folder_path": product_folder,
            "folder_name": folder_name,
            "image_filename": image_filename,
            "txt_filename": txt_filename,
            "json_filename": json_filename
        }
    except Exception as e:
        print(f"Error creating product package: {e}")
        return None

def download_product_image(image_url, product_folder, base_filename):
    """Download image to the specific product folder with proper naming"""
    if not image_url:
        return None
        
    try:
        # Get file extension from URL
        parsed_url = urlparse(image_url)
        path = parsed_url.path
        ext = os.path.splitext(path)[1] if os.path.splitext(path)[1] else '.jpg'
        
        # Create filename: SKU--ProductName--Image.ext
        image_filename = f"{base_filename}{ext}"
        local_path = os.path.join(product_folder, image_filename)
        
        # Download the image with proper headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        req = Request(image_url, headers=headers)
        with urlopen(req, timeout=10) as response:
            with open(local_path, 'wb') as f:
                f.write(response.read())
        
        print(f"Successfully downloaded image: {image_filename}")
        return local_path
        
    except Exception as e:
        print(f"Error downloading image from {image_url}: {e}")
        return None

# PROTECTED ROUTES (require login)
@app.route("/")
@login_required
def index():
    # Get current user info to pass to template
    current_user = auth.get_user_by_email(session['user_email'])
    return render_template("liquor_store.html", current_user=current_user)

@app.route("/api/search", methods=["POST"])
@login_required
def search_sku():
    data = request.get_json()
    sku = data.get("sku", "").strip()

    if not sku:
        return jsonify({"error": "SKU is required"}), 400

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
            package_info = create_product_package(product, sku, upc_data)
            
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
@login_required  
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
                    package_info = create_product_package(product, sku, upc_data)
                    
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

# Add all other API routes with @login_required...

# Serve files from product folders
# Add all other API routes with @login_required...

# Serve files from product folders
# Add all other API routes with @login_required...

# Serve files from product folders
# Add all other API routes with @login_required...

# Serve files from product folders
# Add all other API routes with @login_required...

# Serve files from product folders
# Add all other API routes with @login_required...

# Serve files from product folders
# Add all other API routes with @login_required...

# Serve files from product folders
# Add all other API routes with @login_required...

# Serve files from product folders
# Add all other API routes with @login_required...

# Serve files from product folders
# Add all other API routes with @login_required...

# Serve files from product folders
# Add all other API routes with @login_required...

# Serve files from product folders
# Add all other API routes with @login_required...

# Serve files from product folders
# Add all other API routes with @login_required...

# Serve files from product folders
# Add all other API routes with @login_required...

# Serve files from product folders
# Add all other API routes with @login_required...

# Serve files from product folders
# Add all other API routes with @login_required...

# Serve files from product folders
# Add all other API routes with @login_required...

# Serve files from product folders
@app.route("/files/<folder_name>/<filename>")
@login_required
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

# Admin Routes
@app.route("/admin")
@superadmin_required
def admin_panel():
    """Admin panel for user management"""
    users = auth.get_all_users()
    return render_template('admin.html', users=users)

# Health check endpoint for Railway
@app.route("/health")
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy", "service": "sku-finder"}), 200

@app.route("/admin/toggle-user", methods=["POST"])
@superadmin_required
def toggle_user():
    """Enable/disable user account"""
    data = request.get_json()
    user_id = data.get('user_id')
    is_active = data.get('is_active')
    
    result = auth.toggle_user_status(user_id, is_active)
    return jsonify(result)

@app.route("/admin/reset-password", methods=["POST"])
@superadmin_required
def admin_reset_password():
    """Reset user password"""
    user_id = request.form.get('user_id')
    new_password = request.form.get('new_password')
    
    if not user_id or not new_password:
        return render_template('admin.html', 
                             users=auth.get_all_users(),
                             message="User ID and password are required", 
                             message_type="error")
    
    result = auth.reset_user_password(user_id, new_password)
    
    if result['success']:
        message = "Password reset successfully"
        message_type = "success"
    else:
        message = f"Error: {result['error']}"
        message_type = "error"
    
    return render_template('admin.html', 
                         users=auth.get_all_users(),
                         message=message, 
                         message_type=message_type)

@app.route("/admin/impersonate/<int:user_id>")
@superadmin_required
def impersonate_user(user_id):
    """Impersonate a user (superadmin only)"""
    # Store original admin session
    session['original_admin_email'] = session['user_email']
    
    # Find the user to impersonate
    users = auth.get_all_users()
    target_user = next((u for u in users if u['id'] == user_id), None)
    
    if not target_user:
        return render_template('admin.html', 
                             users=auth.get_all_users(),
                             message="User not found", 
                             message_type="error")
    
    # Switch session to target user
    session['user_email'] = target_user['email']
    session['impersonating'] = True
    
    return redirect(url_for('index'))

@app.route("/admin/stop-impersonating")
def stop_impersonating():
    """Stop impersonating and return to admin account"""
    if 'original_admin_email' in session and session.get('impersonating'):
        session['user_email'] = session['original_admin_email']
        session.pop('original_admin_email', None)
        session.pop('impersonating', None)
    
    return redirect(url_for('admin_panel'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(debug=debug, host="0.0.0.0", port=port)
