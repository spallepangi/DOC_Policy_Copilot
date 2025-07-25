# Deployment Guide

## 🚀 Deploy to GitHub and Streamlit Cloud

### Step 1: Prepare for GitHub Upload

1. **Initialize Git Repository:**
```bash
cd /Users/santhosh/Documents/Projects/DOC_Policy_Copilot
git init
```

2. **Add Files (excluding sensitive data):**
```bash
git add .
git commit -m "Initial commit: Missouri DOC Policy Copilot"
```

3. **Connect to GitHub:**
```bash
git remote add origin https://github.com/YOUR-USERNAME/DOC_Policy_Copilot.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy to Streamlit Cloud

1. **Go to [Streamlit Cloud](https://share.streamlit.io/)**

2. **Click "New app" and connect your GitHub repository:**
   - Repository: `YOUR-USERNAME/DOC_Policy_Copilot`
   - Branch: `main`
   - Main file path: `app_no_upload.py`

3. **Add Environment Variables:**
   - Click "Advanced settings"
   - Add secrets in TOML format:
   ```toml
   GEMINI_API_KEY = "your_actual_gemini_api_key_here"
   ```

4. **Deploy:**
   - Click "Deploy"
   - Wait for deployment to complete
   - Your app will be available at: `https://your-app-name.streamlit.app`

### Step 3: Security Checklist

✅ **Verify these items before deployment:**

- [ ] `.env` file is in `.gitignore` (✅ Done)
- [ ] API key is NOT in any committed files (✅ Secured)
- [ ] `.env.example` is provided for users (✅ Created)
- [ ] Streamlit secrets are configured in cloud (⚠️ You need to do this)
- [ ] No hardcoded sensitive data in code (✅ Cleaned)

### Step 4: Local Development Setup

For other developers to run this locally:

1. **Clone repository:**
```bash
git clone https://github.com/YOUR-USERNAME/DOC_Policy_Copilot.git
cd DOC_Policy_Copilot/RAG
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Setup environment:**
```bash
cp .env.example .env
# Edit .env file to add actual API key
```

4. **Add policy documents:**
```bash
# Place PDF files in data/policies/ folder
```

5. **Run application:**
```bash
streamlit run app_no_upload.py
```

## 🔒 Security Best Practices

### API Key Management

1. **Never commit API keys to Git**
2. **Use environment variables for all secrets**
3. **Provide `.env.example` template for users**
4. **Use Streamlit Cloud secrets for production**

### File Structure for Deployment

```
DOC_Policy_Copilot/
├── RAG/
│   ├── .env.example          # ✅ Template (safe to commit)
│   ├── .env                  # ❌ Real keys (ignored by Git)
│   ├── .gitignore            # ✅ Protects sensitive files
│   ├── app_no_upload.py      # ✅ Main Streamlit app
│   ├── main.py               # ✅ RAG pipeline
│   ├── requirements.txt      # ✅ Dependencies
│   └── data/policies/        # ❌ PDF files (ignored by Git)
└── README.md                 # ✅ Project documentation
```

## 🌐 Access Your Deployed App

After successful deployment:

- **Local Development:** http://localhost:8501
- **Streamlit Cloud:** https://your-app-name.streamlit.app

## 🛠️ Troubleshooting Deployment

### Common Issues:

1. **API Key Error:**
   - Check Streamlit Cloud secrets configuration
   - Verify TOML format in secrets

2. **Import Errors:**
   - Ensure all dependencies are in `requirements.txt`
   - Check Python version compatibility

3. **File Not Found:**
   - Verify relative paths in code
   - Check data folder structure

4. **Memory Issues:**
   - Streamlit Cloud has memory limits
   - Consider optimizing document processing

### Support

- **Streamlit Cloud:** https://docs.streamlit.io/streamlit-community-cloud
- **GitHub:** https://docs.github.com/
- **Gemini API:** https://ai.google.dev/docs
