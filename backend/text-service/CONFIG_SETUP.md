# SkillScreen Configuration Setup

This document explains how to set up the configuration for the SkillScreen application.

## 🔐 Security Notice

**IMPORTANT**: Never commit API keys or sensitive configuration data to version control. The `.config` file is already excluded from Git.

## 📋 Setup Instructions

### 1. Copy the Example Configuration

```bash
cd backend/text-service
cp .config.example .config
```

### 2. Fill in Your API Keys

Edit the `.config` file and replace the placeholder values with your actual API keys:

```bash
# API Keys
GEMINI_API_KEY=your_actual_gemini_api_key_here
WOLFRAM_APP_ID=your_actual_wolfram_app_id_here
SERPAPI_KEY=your_actual_serpapi_key_here
```

### 3. Required API Keys

#### Google Gemini API
- **Purpose**: AI-powered question generation
- **How to get**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Cost**: Free tier available

#### Wolfram Alpha API
- **Purpose**: Enhanced question generation with computational knowledge
- **How to get**: Visit [Wolfram Alpha API](https://developer.wolframalpha.com/)
- **Cost**: Free tier available

#### SerpApi API
- **Purpose**: Real-time data and industry trends for question generation
- **How to get**: Visit [SerpApi](https://serpapi.com/)
- **Cost**: Free tier available

### 4. Optional Configuration

You can also configure other settings in the `.config` file:

```bash
# Database Configuration
DATABASE_URL=sqlite:///./skillscreen.db
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=skillscreen
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password_here

# Application Configuration
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=your_secret_key_here

# File Upload Configuration
MAX_FILE_SIZE=10485760  # 10MB in bytes
UPLOAD_DIRECTORY=uploads/
ALLOWED_EXTENSIONS=pdf,docx,txt
```

## 🔧 Environment Variables Alternative

Instead of using the `.config` file, you can also set environment variables:

```bash
export GEMINI_API_KEY="your_gemini_api_key"
export WOLFRAM_APP_ID="your_wolfram_app_id"
export SERPAPI_KEY="your_serpapi_key"
```

Environment variables take precedence over the `.config` file.

## 🚀 Running the Application

After setting up your configuration:

```bash
# Start the FastAPI backend
cd backend/text-service
python -m uvicorn fastapi_app:app --host 0.0.0.0 --port 8000

# Start the Streamlit frontend (in another terminal)
cd frontend/streamlit-app
streamlit run streamlit_frontend.py
```

## 🔍 Configuration Loading

The application uses a `ConfigLoader` class that:

1. **First checks environment variables** (highest priority)
2. **Then checks the `.config` file**
3. **Finally uses default values**

This allows for flexible configuration management across different environments.

## 🛡️ Security Best Practices

1. **Never commit `.config` files** to version control
2. **Use environment variables** in production
3. **Rotate API keys regularly**
4. **Use different keys** for development and production
5. **Monitor API usage** to detect unauthorized access

## 📞 Support

If you encounter issues with configuration setup, please check:

1. **API key validity** - Ensure keys are active and have proper permissions
2. **File permissions** - Ensure the `.config` file is readable
3. **Environment variables** - Check if conflicting environment variables are set
4. **Logs** - Check application logs for configuration-related errors

## 🔄 Updates

When updating the application, you may need to:

1. **Update your `.config` file** with new configuration options
2. **Check the `.config.example`** for new required fields
3. **Update environment variables** if using them instead

---

**Remember**: Keep your API keys secure and never share them publicly!
