# Deployment Guide for Bantuan Web App

## Quick Checklist

- [ ] Web App created in Azure
- [ ] Publish profile downloaded and added as `AZURE_WEBAPP_PUBLISH_PROFILE` secret in GitHub
- [ ] Repository pushed with all changes
- [ ] GitHub Actions workflow running
- [ ] Static files (index.html, styles.css, script.js) deployed
- [ ] web.config present in deployment

## Troubleshooting

### Issue: Default Azure page still showing

**Solution Steps:**

1. **Verify publish profile secret exists:**
   - Go to GitHub repo → Settings → Secrets and variables → Actions
   - Confirm `AZURE_WEBAPP_PUBLISH_PROFILE` secret exists

2. **Check deployment in Azure Portal:**
   - Open Azure App Service → Deployment Center
   - View deployment history
   - Check if latest deployment shows "Successful"

3. **Verify files in Azure:**
   - Open Azure App Service → SSH/Kudu Console
   - Navigate to `site/wwwroot`
   - Confirm these files exist:
     - `index.html`
     - `styles.css`
     - `script.js`
     - `web.config`

4. **Check IIS configuration:**
   - In Kudu console: `type d:\home\site\wwwroot\web.config`
   - Should show your web.config content
   - If missing or empty, deployment failed

5. **Review App Service Application Settings:**
   - Check if there are any routing overrides
   - Ensure no custom handlers are preventing static files

6. **Clear browser cache:**
   - Hard refresh: Ctrl+Shift+R (or Cmd+Shift+R on Mac)
   - Or use Incognito/Private window

## Files Included in Deployment

```
front-end/
├── index.html           (Main HTML file)
├── styles.css           (Styling)
├── script.js            (JavaScript logic)
├── web.config           (IIS configuration - CRITICAL)
├── robots.txt           (SEO)
├── startup.cmd          (App Service startup)
└── azure-config.json    (Azure configuration)
```

## Browser Console

If issues persist, check browser console (F12) for:
- Errors loading CSS
- Errors loading JavaScript
- CORS issues
- File not found errors

## Manual Deployment

If GitHub Actions fails, manually deploy:

1. Go to your App Service in Azure Portal
2. Click "Deployment Center"
3. Click "Manage publish profile"
4. Download the publish profile (.publishsettings)
5. Use Azure App Service Deployment extension in VS Code to deploy
