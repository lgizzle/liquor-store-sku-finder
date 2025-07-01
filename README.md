# Cheers Liquor Mart - SKU Finder

A clean, simple web application for finding product information using SKU/UPC codes via the Go-UPC API. Features a modern Bootstrap interface with product search, copy-to-clipboard functionality, and image downloads.

## 🚀 QUICK START

### Current Status
- ✅ **Clean & Simple** - streamlined single SKU search interface
- ✅ **Authentication** - simple login system with test accounts
- ✅ **Go-UPC API integration** - pulls complete product data
- ✅ **Modern UI** - Bootstrap 5 with Cheers branding
- ✅ **Copy functionality** - easy copy-to-clipboard for product details
- ✅ **Image downloads** - direct download with proper filenames

### What This App Does
1. User logs in with provided credentials
2. User enters a single SKU/UPC code
3. App queries Go-UPC API for product data
4. User can:
   - Copy product name and description to clipboard
   - Preview product image
   - Download product image with SKU-based filename

## 📁 PROJECT STRUCTURE

```
sku-pic-finder/
├── app.py                  # Main Flask application (CLEAN IMPLEMENTATION)
├── templates/
│   ├── index.html         # Main SKU finder interface
│   └── login.html         # Simple login page
├── static/
│   └── images/
│       └── cheers-logo.png # Cheers branding logo
├── logs/                  # Application logs
├── venv/                  # Virtual environment
├── requirements.txt       # Python dependencies
├── Procfile              # Railway deployment config
├── setup_dev.sh          # Development setup script
├── start_dev.sh          # Development start script
└── .env                  # Environment variables
```

## 🔧 SETUP INSTRUCTIONS

### Quick Setup (Recommended)
```bash
# Clone the repository
git clone https://github.com/lgizzle/liquor-store-sku-finder.git
cd sku-pic-finder

# Run setup script (creates venv and installs dependencies)
chmod +x setup_dev.sh start_dev.sh
./setup_dev.sh

# Start the application
./start_dev.sh
```

### Manual Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python3 app.py
```

### Environment Variables
The `.env` file contains:
```env
GO_UPC_API_KEY=011032ef800fbfd7de89ef7b56dc4dca354db908286d38b85100c619236912eb
SECRET_KEY=dev-secret-key-change-in-production
FLASK_ENV=development
```

### Access the Application
- **Local URL**: http://127.0.0.1:5001
- **Login Credentials**:
  - Admin: `les.gutches@gmail.com` / `CheersBusiness2024`
  - Test User: `test@cheersliquormart.com` / `CheersBusiness2024`

## 🚀 DEPLOYMENT (Railway)

### Current Deployment
- **URL**: https://liquorforge.com
- **Auto-deploy**: Enabled on `main` branch
- **Environment variables**: Set in Railway dashboard

### Deploy Changes
```bash
git add .
git commit -m "Your changes"
git push origin main
# Railway auto-deploys from main branch
```

### Railway Configuration
Environment variables set in Railway:
- `GO_UPC_API_KEY`: Your Go-UPC API key
- `SECRET_KEY`: Flask secret key
- `FLASK_ENV`: production

## 💻 HOW THE APP WORKS

### Authentication Flow
1. User visits app → redirected to login if not authenticated
2. User logs in with provided credentials → session created
3. User accesses main SKU finder interface

### Search & Copy Flow
1. User enters single UPC/SKU code
2. Frontend calls `/api/search` endpoint via AJAX
3. Backend queries Go-UPC API with Bearer token authentication
4. Frontend displays product information with copy buttons
5. User can copy product name/description to clipboard
6. User can preview and download product image

### Image Download System
```python
@app.route("/download-image")
def download_image():
    # Proxies image downloads to bypass CORS restrictions
    # Sets proper Content-Disposition headers for file download
    # Creates meaningful filenames using SKU + extension
```

## 🔑 API ENDPOINTS

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Main SKU finder interface (requires login) |
| `/login` | GET/POST | Simple authentication |
| `/logout` | GET | Clear session and logout |
| `/api/search` | POST | Single SKU search via Go-UPC API |
| `/download-image` | GET | Proxy image downloads with proper headers |
| `/favicon.ico` | GET | Handle favicon requests |

## 🗄️ AUTHENTICATION

### Simple User System
- **In-memory user storage** (no database required)
- **Session-based authentication** using Flask sessions
- **Two test accounts** provided for immediate use

### User Accounts
```python
USERS = {
    "les.gutches@gmail.com": {"password": "CheersBusiness2024", "role": "admin"},
    "test@cheersliquormart.com": {"password": "CheersBusiness2024", "role": "user"},
}
```

## 🐛 DEBUGGING GUIDE

### Common Issues
1. **"Go-UPC API key not configured"**
   - Check `.env` file contains correct API key
   - Verify environment variables in Railway dashboard

2. **"Authentication required" errors**
   - Ensure you're logged in with provided credentials
   - Check session is active (try refreshing page)

3. **"Product not found" errors**
   - Verify SKU/UPC code is correct
   - Try sample SKUs: `898627001308` or `088004021344`

4. **Image download issues**
   - Check browser console for JavaScript errors
   - Verify image URL exists in API response

### Debug Tools
```bash
# Check if server is running
lsof -i :5001

# Test API directly (requires login session)
curl -X POST http://localhost:5001/api/search \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your_session_cookie" \
  -d '{"sku": "898627001308"}'

# Check Flask logs in terminal
```

## 📝 DEVELOPMENT NOTES

### Key Files
- **app.py**: Main Flask application (187 lines, clean implementation)
- **templates/index.html**: Bootstrap 5 interface with Cheers branding
- **templates/login.html**: Simple login form

### Code Quality
- ✅ **Clean codebase**: No dead code, all functions used
- ✅ **Modern frameworks**: Bootstrap 5, Flask best practices
- ✅ **Proper error handling**: API errors, authentication, validation
- ✅ **Environment detection**: Development vs production modes

### Adding Features
1. **New routes**: Add to `app.py` with proper authentication checks
2. **Frontend changes**: Modify `templates/index.html` (Bootstrap 5)
3. **Styling**: Use CSS custom properties for Cheers brand colors

### Testing
- **Local**: Use provided login credentials and sample SKUs
- **Production**: Test at https://liquorforge.com
- **Sample SKUs**: `898627001308` (Tequila Ocho), `088004021344` (Eagle Rare)

## 🔒 SECURITY NOTES

- **Session-based authentication**: All routes protected except login
- **Environment variables**: Sensitive data in `.env` file
- **No database**: Simple in-memory user storage
- **HTTPS in production**: Railway provides SSL certificates

## 📦 DEPENDENCIES

```txt
Flask==3.0.0
python-dotenv==1.0.0
```

**Minimal dependencies** - only what's needed for core functionality.

## 🎯 CURRENT STATUS

✅ **Production Ready**: Clean, simple, fully functional
- Modern Bootstrap 5 interface with Cheers branding
- Single SKU search with copy-to-clipboard functionality
- Image preview and download with proper filenames
- Clean codebase with no technical debt

## 📞 SUPPORT

- **Go-UPC API docs**: [go-upc.com/docs](https://go-upc.com/docs)
- **Railway docs**: [docs.railway.app](https://docs.railway.app)
- **Bootstrap docs**: [getbootstrap.com](https://getbootstrap.com)

---

**🎉 This app is clean, modern, and production-ready!**
