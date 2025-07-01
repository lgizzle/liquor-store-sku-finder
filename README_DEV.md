# Cheers Liquor Mart SKU Finder - Development Guide

A clean, modern web application for finding product information using SKU codes. Features Bootstrap 5 interface with Cheers branding, single SKU search, copy-to-clipboard functionality, and image downloads.

## 🚀 Quick Start

### Development Setup (Recommended)

1. **Run the setup script** (creates virtual environment and installs dependencies):
   ```bash
   ./setup_dev.sh
   ```

2. **Start the development server**:
   ```bash
   ./start_dev.sh
   ```

3. **Access the application**:
   - Local URL: http://127.0.0.1:5001
   - Login credentials:
     - Admin: `les.gutches@gmail.com` / `CheersBusiness2024`
     - Test User: `test@cheersliquormart.com` / `CheersBusiness2024`

### Manual Setup

If you prefer manual setup:

1. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment variables** (already configured in `.env`):
   ```
   GO_UPC_API_KEY=011032ef800fbfd7de89ef7b56dc4dca354db908286d38b85100c619236912eb
   SECRET_KEY=dev-secret-key-change-in-production
   FLASK_ENV=development
   ```

4. **Run the application**:
   ```bash
   source venv/bin/activate
   python3 app.py
   ```

## 🎯 Features

- **Clean Interface**: Modern Bootstrap 5 design with Cheers branding
- **Single SKU Search**: Simplified interface (no batch processing)
- **Copy to Clipboard**: Separate buttons for product name and description
- **Image Preview & Download**: View and download product images with proper filenames
- **Responsive Design**: Works on desktop and mobile devices
- **Session Authentication**: Simple login system with test accounts

## 🔐 Authentication

**Available Accounts**:
- **Admin**: `les.gutches@gmail.com` / `CheersBusiness2024`
- **Test User**: `test@cheersliquormart.com` / `CheersBusiness2024`

## 📖 Usage

1. **Login**: Use either account above to access the application
2. **Search**: Enter a single SKU/UPC code (try sample SKUs provided)
3. **View Results**: See product name, description, and image preview
4. **Copy Information**: Use copy buttons for name and description
5. **Download Image**: Click download button to save with SKU-based filename

## 🧪 Sample SKUs for Testing

- **Tequila Ocho Single Estate Plata**: `898627001308`
- **Eagle Rare Single Barrel**: `088004021344`

## 🚀 Deployment

### Local Development
- Use `./start_dev.sh` for local development
- Access at http://127.0.0.1:5001

### Railway Production
- Production URL: https://liquorforge.com
- Auto-deploys from `main` branch
- Environment variables configured in Railway dashboard

## 📁 File Structure

```
sku-pic-finder/
├── app.py                    # Main Flask application (CLEAN IMPLEMENTATION)
├── templates/
│   ├── index.html           # Bootstrap 5 interface with Cheers branding
│   └── login.html           # Simple login page
├── static/
│   └── images/
│       └── cheers-logo.png  # Cheers branding logo
├── venv/                    # Virtual environment
├── setup_dev.sh             # Development setup script
├── start_dev.sh             # Development start script
├── requirements.txt         # Python dependencies (minimal)
├── .env                     # Environment variables
├── Procfile                 # Railway deployment config
├── railway.json             # Railway configuration
├── .railwayignore          # Railway ignore file
├── README.md               # Main documentation
└── README_DEV.md           # This development guide (ignored in production)
```

## 🔧 Troubleshooting

### Virtual Environment Issues
- Run `./setup_dev.sh` to create and configure virtual environment
- Always activate: `source venv/bin/activate`

### Authentication Issues
- Use provided credentials exactly as shown
- Clear browser cache/cookies if login issues persist

### API Issues
- API key is pre-configured in `.env` file
- Test with sample SKUs: `898627001308` or `088004021344`

### Image Download Issues
- Images are proxied through Flask backend to handle CORS
- Check browser console for JavaScript errors

## 🔄 Development Workflow

1. **Setup**: Run `./setup_dev.sh` once to create environment
2. **Start**: Use `./start_dev.sh` to start the development server
3. **Test**: Access http://127.0.0.1:5001 and test with sample SKUs
4. **Deploy**: Push to `main` branch for automatic Railway deployment

## 📝 Implementation Status

✅ **Complete & Clean**:
- Modern Bootstrap 5 interface with Cheers branding
- Single SKU search with copy-to-clipboard functionality
- Image preview and download with proper filenames
- Session-based authentication with test accounts
- Clean codebase (187 lines, no dead code)
- Minimal dependencies (Flask, python-dotenv, gunicorn)
- Production-ready deployment configuration
