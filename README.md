# Cheers Liquor Mart - SKU Finder

A web application for finding and downloading comprehensive product information using UPC/SKU codes via the Go-UPC API.

## 🚀 QUICK START FOR DEVELOPERS

### Current Status
- ✅ **Fully functional** - deployed on Railway
- ✅ **Authentication system** - user registration/login required
- ✅ **Go-UPC API integration** - pulls complete product data
- ✅ **File download system** - generates 3 files per product

### What This App Does
1. User enters UPC/SKU code
2. App queries Go-UPC API for product data
3. User downloads 3 files:
   - **JSON**: Complete API response with all product data
   - **TXT**: Human-readable formatted product information
   - **IMAGE**: Product image downloaded from URL

## 📁 PROJECT STRUCTURE

```
sku-pic-finder/
├── web_app_with_auth.py     # Main Flask application (THIS IS THE ONLY APP FILE)
├── simple_auth.py           # Authentication system
├── auth_config.py          # Auth configuration
├── templates/
│   ├── liquor_store.html   # Main application interface
│   ├── login.html          # Login page
│   ├── register.html       # Registration page
│   └── admin.html          # Admin panel
├── static/                 # CSS/JS assets
├── images/                 # Generated product folders (local only)
├── logs/                   # Application logs
├── requirements.txt        # Python dependencies
├── Procfile               # Railway deployment config
└── .env.example           # Environment variables template
```

## 🔧 SETUP INSTRUCTIONS

### 1. Environment Setup
```bash
# Clone the repository
git clone <repo-url>
cd sku-pic-finder

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Variables
Create `.env` file from template:
```bash
cp .env.example .env
```

**Required environment variables:**
```env
GO_UPC_API_KEY=your_go_upc_api_key_here
SECRET_KEY=your_secret_key_here
FLASK_ENV=development
```

### 3. Get Go-UPC API Key
1. Sign up at [go-upc.com](https://go-upc.com)
2. Get your API key from dashboard
3. Add to `.env` file

### 4. Run Locally
```bash
python web_app_with_auth.py
```
Access at: `http://localhost:5001`

## 🚀 DEPLOYMENT (Railway)

### Current Deployment
- **URL**: [Check Railway dashboard]
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
1. User visits app → redirected to login
2. User registers/logs in → session created
3. User accesses main interface

### Search & Download Flow
1. User enters UPC/SKU
2. Frontend calls `/api/search` endpoint
3. Backend queries Go-UPC API
4. Frontend displays results
5. User clicks "Download All" → 3 files generated client-side

### File Generation (Client-Side)
```javascript
downloadAllFiles(result) {
    // 1. JSON file: Complete API response
    // 2. TXT file: Formatted text from JSON data  
    // 3. IMAGE: Downloaded from image URL in JSON
}
```

## 🔑 API ENDPOINTS

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/login` | GET/POST | User authentication |
| `/register` | GET/POST | User registration |
| `/` | GET | Main application (requires login) |
| `/api/search` | POST | Single SKU search |
| `/api/batch` | POST | Multiple SKU search |
| `/health` | GET | Health check for Railway |

## 🗄️ DATABASE

### SQLite Database: `users.db`
- **users** table: email, password_hash, created_at, is_active, is_superadmin
- **password_resets** table: email, token, expires_at

### Admin Features
- Superadmin account auto-created on startup
- User management panel at `/admin`
- User impersonation capability

## 🐛 DEBUGGING GUIDE

### Common Issues
1. **"Go-UPC API key not configured"**
   - Check environment variables in Railway
   - Verify `.env` file locally

2. **"404 errors"**
   - Check Railway deployment logs
   - Ensure app is running on correct port

3. **"Only getting 1 file download"**
   - Check browser console for JavaScript errors
   - Verify image URL in API response

### Debug Tools
```bash
# Check if server is running
lsof -i :5001

# Test API directly
curl -X POST http://localhost:5001/api/search \
  -H "Content-Type: application/json" \
  -d '{"sku": "012000001390"}'

# Check logs
tail -f logs/app.log
```

## 📝 DEVELOPMENT NOTES

### Key Files to Modify
- **web_app_with_auth.py**: Main application logic
- **templates/liquor_store.html**: Frontend interface
- **simple_auth.py**: Authentication system

### Adding Features
1. **New API endpoints**: Add to `web_app_with_auth.py`
2. **Frontend changes**: Modify `templates/liquor_store.html`
3. **Styling**: Update `static/` files

### Testing
- Use Railway health check: `/health`
- Test authentication flow manually
- Verify file download with real UPC codes

## 🔒 SECURITY NOTES

- All routes require authentication (except login/register)
- Passwords hashed with bcrypt
- Session-based authentication
- Environment variables for sensitive data

## 📦 DEPENDENCIES

Key packages:
- **Flask**: Web framework
- **bcrypt**: Password hashing
- **sqlite3**: Database
- **urllib**: HTTP requests to Go-UPC API

## 🎯 NEXT DEVELOPER TODO

1. **Immediate tasks**: None - app is fully functional
2. **Potential improvements**:
   - Add product search history
   - Implement product categories/filtering
   - Add bulk export features
   - Enhanced error handling for failed image downloads

## 📞 SUPPORT

- **Go-UPC API docs**: [go-upc.com/docs](https://go-upc.com/docs)
- **Railway docs**: [docs.railway.app](https://docs.railway.app)
- **Flask docs**: [flask.palletsprojects.com](https://flask.palletsprojects.com)

---

**This app is production-ready and fully deployed. No immediate development needed.**
