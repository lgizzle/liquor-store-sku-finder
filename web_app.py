from flask import Flask, request, jsonify, render_template, send_from_directory, send_file
from flask import Flask, request, jsonify, render_template, send_from_directory, send_file
from sku_finder import SKUPictureFinder
import os
import shutil

app = Flask(__name__)


# Enable CORS manually if flask-cors is not available
@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE")
    return response


# Initialize the SKU finder
finder = SKUPictureFinder()


@app.route("/")
def index():
    return render_template("liquor_store.html")


@app.route("/api/search", methods=["POST"])
def search_sku():
    data = request.get_json()
    sku = data.get("sku", "").strip()

    if not sku:
        return jsonify({"error": "SKU is required"}), 400

    try:
        results = finder.find_images(sku)

        # Convert results to JSON-serializable format
        json_results = []
        for result in results:
            json_results.append(
                {
                    "sku": result.sku,
                    "source": result.source,
                    "image_url": result.image_url,
                    "title": result.title,
                    "price": result.price,
                    "description": result.description,
                    "local_path": result.local_path,
                    "confidence": result.confidence,
                }
            )

        return jsonify(
            {
                "success": True,
                "sku": sku,
                "results": json_results,
                "count": len(json_results),
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/batch", methods=["POST"])
def batch_search():
    data = request.get_json()
    skus = data.get("skus", [])

    if not skus:
        return jsonify({"error": "SKUs list is required"}), 400

    try:
        batch_results = finder.batch_process(skus)

        # Convert to JSON-serializable format
        json_results = {}
        for sku, results in batch_results.items():
            json_results[sku] = []
            for result in results:
                json_results[sku].append(
                    {
                        "sku": result.sku,
                        "source": result.source,
                        "image_url": result.image_url,
                        "title": result.title,
                        "price": result.price,
                        "description": result.description,
                        "local_path": result.local_path,
                        "confidence": result.confidence,
                    }
                )

        return jsonify(
            {"success": True, "results": json_results, "processed": len(skus)}
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/stats")
def get_stats():
    try:
        stats = finder.get_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/export")
def export_results():
    try:
        filename = finder.export_results()
        return jsonify(
            {
                "success": True,
                "filename": filename,
                "message": "Results exported successfully",
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/images/<path:filename>")
def serve_image(filename):
    return send_from_directory(finder.output_dir, filename)


@app.route("/api/save-selected", methods=["POST"])
def save_selected_images():
    """Save only the selected images and remove unselected ones"""
    data = request.get_json()
    sku = data.get("sku", "").strip()
    selected_local_paths = data.get("selected_local_paths", [])

    if not sku or len(selected_local_paths) == 0:
        return jsonify({"error": "SKU and selected image paths are required"}), 400

    try:
        # Get all image files for this SKU in the images directory (flat structure)
        all_sku_files = []
        images_dir = finder.output_dir

        for file in os.listdir(images_dir):
            if file.lower().endswith(
                (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp")
            ):
                if file.startswith(sku + "-") or file.startswith(sku + "_"):
                    all_sku_files.append(file)

        # Convert selected local paths to just filenames
        selected_filenames = set()
        for path in selected_local_paths:
            if path:
                filename = os.path.basename(path)
                selected_filenames.add(filename)

        # Remove files that are not selected
        removed_count = 0
        for file in all_sku_files:
            if file not in selected_filenames:
                file_path = os.path.join(images_dir, file)
                try:
                    os.remove(file_path)
                    removed_count += 1
                except Exception as e:
                    print(f"Error removing {file_path}: {e}")

        remaining_count = len(selected_filenames)

        return jsonify(
            {
                "success": True,
                "message": f"Saved {remaining_count} selected images",
                "removed_count": removed_count,
                "remaining_count": remaining_count,
            }
        )

    except Exception as e:
        return jsonify({"error": f"Error saving selected images: {str(e)}"}), 500


@app.route("/api/download", methods=["GET"])
def download_image():
    """Serve an image for download with a custom filename (UPC and product name)"""
    local_path = request.args.get("local_path")
    sku = request.args.get("sku")
    title = request.args.get("title")
    if not local_path or not sku or not title:
        return jsonify({"error": "Missing parameters"}), 400
    try:
        # Sanitize filename
        safe_title = ''.join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip().replace(' ', '_')
        filename = f"{sku}-{safe_title}.jpg"
        # Serve from the images directory
        return send_file(local_path, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, host="0.0.0.0", port=port)
