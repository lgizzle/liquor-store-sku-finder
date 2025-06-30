# SKU Picture Finder

A Python tool to automatically find product images using SKU numbers or UPC codes, powered by the Go-UPC API.

## Features

- Uses Go-UPC API for reliable product images and data
- Batch processing support
- Image download and organization
- CSV export with results
- Web interface and command-line interface
- Secure API key management via .env file

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Quick Setup

1. Clone or download this repository
2. Navigate to the project directory:
   ```bash
   cd sku-pic-finder
   ```

3. Create a virtual environment (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r web_requirements.txt  # For web interface
   ```

5. Set up your Go-UPC API key in a `.env` file:
   ```bash
   echo "GO_UPC_API_KEY=your_actual_api_key_here" > .env
   ```

## Usage

### Command Line Interface
```bash
# Single SKU search
python sku_finder.py --sku "012345678905"

# Batch processing from CSV file
python sku_finder.py --file "sample_skus.csv" --batch
```

### Web Interface
```bash
python web_app.py
# Open http://localhost:5001 in your browser
```

- Enter a SKU/UPC and search. Images will be downloaded to your system's Downloads folder with filenames like `012345678905-ProductName.jpg`.
- You can select and download images directly from the web interface.

### Python API
```python
from sku_finder import SKUPictureFinder

finder = SKUPictureFinder()
results = finder.find_images("012345678905")
print(f"Found {len(results)} images")

# Batch processing
skus = ["012345678905", "049000028911"]
batch_results = finder.batch_process(skus)
```

## Configuration

Create a `.env` file for your Go-UPC API key:
```
GO_UPC_API_KEY=your_actual_api_key_here
```

## Output

The tool generates:
- Downloaded images saved to your Downloads folder, named with the UPC and product name
- CSV report with image URLs and metadata
- Log file with processing details

## Example Results

When you run the tool, you'll get:
```
Found 1 image for SKU: 012345678905
  1. Product Name (Go-UPC) - Confidence: 100%
Image saved to: ~/Downloads/012345678905-ProductName.jpg
```

## File Structure

```
sku-pic-finder/
├── sku_finder.py          # Main SKU finder class
├── web_app.py             # Flask web interface
├── example_usage.py       # Example usage script
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── web_requirements.txt   # Web interface dependencies
├── sample_skus.csv        # Sample SKU file for testing
├── templates/
│   └── index.html         # Web interface template
│   └── liquor_store.html  # Web interface template
├── .env                   # API key and configuration
```

## API Rate Limits

- Go-UPC: See [Go-UPC documentation](https://go-upc.com/plans/api) for current rate limits and pricing.

## Legal Notice

This tool is for educational and legitimate business purposes. Please:
- Respect the Go-UPC API terms of service
- Ensure you have rights to use the images you download

## Troubleshooting

### Common Issues

1. **No images found**: Ensure the UPC is valid and exists in Go-UPC's database
2. **API key errors**: Check your `.env` file and API key
3. **Download failures**: Check your internet connection and file permissions

## Contributing

Feel free to:
- Improve the web interface
- Fix bugs and add features

## License

This project is for educational purposes. Please respect all API terms of service and applicable laws.
