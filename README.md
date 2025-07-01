# 🥃 Cheers Liquor Mart - SKU & UPC Product Information System

A professional web application for looking up product information using UPC/SKU codes via the Go-UPC API. Creates organized file system folders with complete product data, images, and documentation.

## 🚀 Features

### 🔍 **Product Lookup**
- **Single SKU Search** - Look up individual products by UPC/SKU
- **Batch Search** - Process multiple UPCs at once
- **Real-time Go-UPC API integration** - Get accurate product data
- **Automatic image downloading** - High-quality product images

### 📁 **File System Organization**
- **Self-contained product folders** - Each UPC gets its own organized folder
- **Folder naming**: `UPC--ProductName` format for easy identification
- **No ZIP compression** - Direct file system access
- **Multiple file formats**:
  - `product_info.json` - Structured data for systems
  - `product_info.txt` - Human-readable format
  - `image.{ext}` - Downloaded product image

### 📋 **Copy & Paste Features**
- **Quick copy buttons** - One-click copy for titles and descriptions
- **Pretty print modal** - Formatted product info ready for copy/paste
- **Multiple copy options** - Individual fields or complete product info

### 🌐 **File Browser**
- **Browse created products** - View all processed UPCs
- **Direct file access** - Download individual JSON, TXT, or image files
- **Folder structure display** - See exactly what was created

## 🛠️ Technology Stack

- **Backend**: Python Flask
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **API**: Go-UPC Product Database
- **Deployment**: Railway
- **File Storage**: Local file system with organized folders

## 📦 Installation & Setup

### Prerequisites
- Python 3.8+
- Go-UPC API key
- Railway account (for deployment)

### Local Development
1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/liquor-store-sku-finder.git
   cd liquor-store-sku-finder
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables**
   ```bash
   export GO_UPC_API_KEY="your_go_upc_api_key_here"
   export PORT=5001
   ```

4. **Run the application**
   ```bash
   python web_app.py
   ```

5. **Open in browser**
   ```
   http://localhost:5001
   ```

### Railway Deployment
1. **Connect to Railway**
   ```bash
   railway login
   railway link
   ```

2. **Set environment variables**
   ```bash
   railway variables set GO_UPC_API_KEY="your_api_key_here"
   ```

3. **Deploy**
   ```bash
   railway up
   ```

## 🔑 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GO_UPC_API_KEY` | Your Go-UPC API key | Yes |
| `PORT` | Port number (default: 5001) | No |

## 📁 Project Structure

```
liquor-store-sku-finder/
├── web_app.py              # Main Flask application
├── templates/
│   └── liquor_store.html   # Frontend template
├── images/                 # Generated product folders
│   ├── UPC1--ProductName1/
│   │   ├── product_info.json
│   │   ├── product_info.txt
│   │   └── image.jpg
│   └── UPC2--ProductName2/
│       ├── product_info.json
│       ├── product_info.txt
│       └── image.png
├── requirements.txt        # Python dependencies
├── railway.json           # Railway configuration
├── Procfile               # Railway startup command
└── README.md              # This file
```

## 🎯 Usage Examples

### Single Product Search
1. Enter a UPC/SKU in the search box (e.g., `843248155091`)
2. Click "🔍 Search Single SKU"
3. View product information with image
4. Use copy buttons for quick text copying
5. Download individual files or browse the created folder

### Batch Processing
1. Enter multiple UPCs (one per line) in the batch search box
2. Click "📋 Batch Search"
3. All products will be processed and organized into folders
4. Use "📁 Browse Products" to see all created folders

### File Management
- Each UPC creates a folder: `UPC--ProductName/`
- Files are directly accessible via the web interface
- No ZIP extraction needed - everything is ready to use

## 🔧 API Integration

This application integrates with the **Go-UPC API** to fetch:
- Product names and descriptions
- Brand information
- Category and regional data
- Product specifications
- High-quality product images

## 📋 Example Product Output

### Folder Structure
```
854948008655--Hoplark_Really_Really_Hoppy_12oz_Can/
├── product_info.json
├── product_info.txt
└── image.png
```

### Sample product_info.txt
```
PRODUCT INFORMATION
==================

UPC: 854948008655
Name: Hoplark Really Really Hoppy - 12oz Can
Brand: Hoplark
Category: Dry Boxes
Region: USA or Canada

Specifications:
Size: 12 Fl Oz | Countries: United States

Image URL: https://go-upc.s3.amazonaws.com/images/131582384.png
Local Image: image.png
Created: 2025-01-07T12:34:56
```

## 🌟 Key Benefits

- **No manual data entry** - Automatic product information retrieval
- **Organized file system** - Professional folder structure
- **Multiple formats** - JSON for systems, TXT for humans
- **Copy-paste ready** - Quick text copying for various uses
- **Self-contained** - Each product is completely packaged
- **Professional grade** - Perfect for inventory management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support or questions:
- Create an issue on GitHub
- Check the Go-UPC API documentation
- Review the Railway deployment docs

## 🚀 Live Demo

**Production URL**: https://loving-spontaneity-production.up.railway.app

Try it with sample UPCs:
- `843248155091` - Underwraps Python Plush
- `854948008655` - Hoplark Really Really Hoppy
- `049000050103` - Coca-Cola 2 Liter

---

**Built with ❤️ for professional product data management**
# Trigger Railway redeploy - Tue Jul  1 06:38:31 MDT 2025
