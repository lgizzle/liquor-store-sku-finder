#!/usr/bin/env python3
"""
Cheers Liquor Mart SKU Finder - Clean Implementation
A simple Flask app for looking up product information by SKU/UPC
"""

import os
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for,
    flash,
    make_response,
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

# Simple user credentials (in production, use a proper database)
USERS = {
    "les.gutches@gmail.com": {"password": "CheersBusiness2024", "role": "admin"},
    "test@cheersliquormart.com": {"password": "CheersBusiness2024", "role": "user"},
}


def get_go_upc_api_key():
    """Get the Go-UPC API key from environment variables"""
    return os.environ.get("GO_UPC_API_KEY", "")


def search_go_upc(sku):
    """Search for product information using Go-UPC API"""
    api_key = get_go_upc_api_key()
    if not api_key:
        raise ValueError("Go-UPC API key not configured")

    try:
        req = Request(f"https://go-upc.com/api/v1/code/{sku}")
        req.add_header("Authorization", f"Bearer {api_key}")

        response = urlopen(req)
        content = response.read()
        data = json.loads(content.decode())

        return data

    except HTTPError as e:
        if e.code == 401:
            raise RuntimeError("API key is invalid or expired")
        elif e.code == 404:
            raise RuntimeError(f"Product with SKU '{sku}' not found")
        else:
            raise RuntimeError(f"API error (HTTP {e.code}): {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error calling Go-UPC API: {str(e)}")


@app.route("/")
def index():
    """Main page - requires login"""
    if "user_email" not in session:
        return redirect(url_for("login"))

    return render_template("index.html", user_email=session["user_email"])


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page"""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if email in USERS and USERS[email]["password"] == password:
            session["user_email"] = email
            session["user_role"] = USERS[email]["role"]
            flash("Login successful!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid email or password", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Logout and clear session"""
    session.clear()
    flash("You have been logged out", "info")
    return redirect(url_for("login"))


@app.route("/api/search", methods=["POST"])
def api_search():
    """API endpoint for SKU search"""
    if "user_email" not in session:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json()
    sku = data.get("sku", "").strip()

    if not sku:
        return jsonify({"error": "SKU is required"}), 400

    try:
        # Search using Go-UPC API
        upc_data = search_go_upc(sku)

        if not upc_data.get("product"):
            return jsonify({"error": "Product not found"}), 404

        product = upc_data["product"]

        # Format the response
        result = {
            "success": True,
            "sku": sku,
            "product": {
                "name": product.get("name", "Unknown Product"),
                "description": product.get("description", ""),
                "brand": product.get("brand", ""),
                "category": product.get("category", ""),
                "imageUrl": product.get("imageUrl", ""),
                "specs": product.get("specs", []),
            },
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/download-image")
def download_image():
    """Download product image with proper headers"""
    if "user_email" not in session:
        return redirect("/login")

    image_url = request.args.get("url")
    sku = request.args.get("sku", "product")

    if not image_url:
        return "Image URL required", 400

    try:
        # Fetch the image from the external URL
        req = Request(image_url)
        response = urlopen(req)
        image_data = response.read()

        # Get file extension from URL
        file_ext = image_url.split(".")[-1] if "." in image_url else "png"
        filename = f"{sku}_image.{file_ext}"

        # Create response with proper download headers
        response = make_response(image_data)
        response.headers["Content-Type"] = "application/octet-stream"
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response

    except Exception as e:
        app.logger.error(f"Image download error: {str(e)}")
        return "Failed to download image", 500


@app.route("/favicon.ico")
def favicon():
    """Handle favicon requests"""
    return "", 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
