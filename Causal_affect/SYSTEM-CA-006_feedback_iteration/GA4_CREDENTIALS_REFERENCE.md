# GA4 Credentials Reference
# For CA-006 Feedback Dashboard

## Collected Credentials

### 1. Measurement ID
```bash
GA4_MEASUREMENT_ID="G-DMQ68JCNX5"
```
**Source**: GA4 Data Stream settings (already collected)

### 2. Property ID
```bash
GA4_PROPERTY_ID="properties/508534117"
```
**Source**: GA4 Admin → Property Settings  
**Raw Value**: 508534117  
**Formatted**: Added `properties/` prefix as required by GA4 Data API

### 3. Service Account JSON File
**Windows Path (OneDrive)**: `C:\Users\james\OneDrive\Causal Affect\google-analytics-service-account.json`

**Action Required**: Copy this file to your dev container

#### Step 1: Copy JSON file to dev container
```bash
# In your dev container terminal:
# Create secrets directory
mkdir -p /workspaces/business_ventures/Causal_affect/src/feedback_iteration/backend/secrets

# You'll need to upload the JSON file from Windows to the dev container
# Option A: Use VS Code file explorer to drag and drop the file
# Option B: Use the terminal to copy from mounted Windows drive (if available)
# Option C: Copy the JSON content and create the file manually
```

#### Step 2: Set the correct path
```bash
# Linux path in dev container (NOT Windows path):
GA4_SERVICE_ACCOUNT_PATH="./secrets/google-analytics-service-account.json"
```

### 4. API Key (Optional - Not Needed for Data API)
**Value**: `<REDACTED — rotate this key in the Google Cloud console>`

**Note**: This appears to be a GA4 API key or similar. The **Data API** uses the service account JSON file for authentication, not an API key. We'll use the service account approach as documented in the setup guide. The real value was removed from this file because the repository is public; if it was ever a live key, revoke/rotate it.

---

## Complete .env Configuration

Once you copy the JSON file to the dev container, create this `.env` file:

```bash
# File: /workspaces/business_ventures/Causal_affect/src/feedback_iteration/backend/.env

# Google Analytics 4
GA4_MEASUREMENT_ID="G-DMQ68JCNX5"
GA4_PROPERTY_ID="properties/508534117"
GA4_SERVICE_ACCOUNT_PATH="./secrets/google-analytics-service-account.json"

# Mixpanel (optional - add later if needed)
# MIXPANEL_PROJECT_TOKEN=""
# MIXPANEL_API_SECRET=""
# MIXPANEL_API_KEY=""

# Amplitude (optional - add later if needed)
# AMPLITUDE_API_KEY=""
# AMPLITUDE_SECRET_KEY=""

# App Config
ENVIRONMENT="development"
LOG_LEVEL="debug"
```

---

## Next Steps

### 1. Copy Service Account JSON to Dev Container

**Option A: Using VS Code File Explorer** (Easiest)
1. In VS Code, navigate to: `/workspaces/business_ventures/Causal_affect/src/feedback_iteration/backend/secrets/`
2. Right-click → "Upload Files..."
3. Browse to: `C:\Users\james\OneDrive\Causal Affect\google-analytics-service-account.json`
4. Upload the file

**Option B: Manual Copy-Paste**
1. Open the JSON file on Windows
2. Copy all contents
3. In VS Code terminal, create the file:
```bash
mkdir -p /workspaces/business_ventures/Causal_affect/src/feedback_iteration/backend/secrets
nano /workspaces/business_ventures/Causal_affect/src/feedback_iteration/backend/secrets/google-analytics-service-account.json
# Paste contents, Ctrl+X, Y, Enter
```

**Option C: Use WSL/Git Bash to Copy** (if available)
```bash
# From Windows terminal with WSL or Git Bash:
cp "/c/Users/james/OneDrive/Causal Affect/google-analytics-service-account.json" \\
   "/path/to/devcontainer/secrets/"
```

### 2. Verify File Permissions
```bash
# In dev container:
chmod 600 /workspaces/business_ventures/Causal_affect/src/feedback_iteration/backend/secrets/google-analytics-service-account.json
```

### 3. Add to .gitignore (Security)
```bash
# Ensure these are in .gitignore:
echo "secrets/" >> /workspaces/business_ventures/.gitignore
echo ".env" >> /workspaces/business_ventures/.gitignore
echo "*.json" >> /workspaces/business_ventures/.gitignore
```

### 4. Ready for AI Code Generator!
Once the JSON file is in place, you'll be ready to build **LAYER-CA-006-01-01** (Google Analytics Client) with real GA4 credentials.

---

## Security Notes

- ✅ Service account JSON contains sensitive credentials
- ✅ Never commit to git
- ✅ Store in `secrets/` folder (gitignored)
- ✅ Use restrictive permissions (chmod 600)
- ✅ Rotate credentials every 90 days

When you return and have the JSON file copied, you'll be all set! 🎉
