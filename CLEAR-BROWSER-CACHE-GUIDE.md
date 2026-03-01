# Clear Browser Cache - Step by Step Guide

## The Problem

Your browser has cached the old CORS error responses from before we updated the Lambda functions. Even though the API is now working correctly (verified by our tests), the browser is showing you the cached errors.

## Verified Working

✓ API is returning 200 OK
✓ CORS headers are present:
  - Access-Control-Allow-Origin: *
  - Access-Control-Allow-Headers: Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token
  - Access-Control-Allow-Methods: GET,POST,PUT,DELETE,OPTIONS

## Solution: Clear Browser Cache

### Method 1: Hard Refresh (Try This First)

1. **Close all DevTools** (F12) - This is important!
2. **Hard refresh the page**:
   - Windows: `Ctrl + Shift + R` or `Ctrl + F5`
   - Mac: `Cmd + Shift + R`
3. **Wait 5 seconds** for the page to fully reload
4. **Try logging in** with admin/admin123

### Method 2: Clear Cache via Settings

If Method 1 doesn't work:

1. **Open DevTools**: Press `F12`
2. **Right-click the refresh button** (next to the address bar)
3. **Select "Empty Cache and Hard Reload"**
4. **Close DevTools** (F12)
5. **Refresh again**: `Ctrl + F5`

### Method 3: Clear All Cached Data

If Methods 1 & 2 don't work:

1. **Press**: `Ctrl + Shift + Delete`
2. **Select**:
   - Time range: "Last hour" or "All time"
   - Check: "Cached images and files"
   - Check: "Cookies and other site data" (optional but recommended)
3. **Click**: "Clear data"
4. **Close the browser completely**
5. **Reopen the browser**
6. **Navigate to**: http://aiassessment.in/dashboard

### Method 4: Use Incognito/Private Mode

This bypasses all cache:

1. **Open Incognito/Private window**:
   - Chrome: `Ctrl + Shift + N`
   - Firefox: `Ctrl + Shift + P`
   - Edge: `Ctrl + Shift + N`
2. **Navigate to**: http://aiassessment.in/dashboard
3. **Try logging in**: admin/admin123

If it works in incognito, the issue is definitely cached data in your normal browser.

### Method 5: Disable Cache in DevTools

For testing purposes:

1. **Open DevTools**: Press `F12`
2. **Go to Network tab**
3. **Check "Disable cache"** checkbox
4. **Keep DevTools open**
5. **Refresh the page**: `Ctrl + R`
6. **Try logging in**

### Method 6: Clear Site Data (Nuclear Option)

If nothing else works:

1. **Open DevTools**: Press `F12`
2. **Go to Application tab** (Chrome) or **Storage tab** (Firefox)
3. **Click "Clear site data"** or **"Clear All"**
4. **Confirm**
5. **Close DevTools**
6. **Refresh**: `Ctrl + F5`

## Verification Steps

After clearing cache, verify:

1. **Open DevTools**: Press `F12`
2. **Go to Console tab**
3. **Refresh the page**: `Ctrl + F5`
4. **Check for errors**:
   - ✓ No CORS errors should appear
   - ✓ No red error messages
   - ✓ API calls should show 200 OK status

5. **Go to Network tab**
6. **Refresh the page**: `Ctrl + F5`
7. **Look for the templates request**:
   - Click on the `/templates` request
   - Check "Headers" tab
   - Verify "Status Code: 200 OK"
   - Verify CORS headers are present

## Expected Results

After clearing cache:

✓ Login page loads without errors
✓ No CORS errors in console
✓ Login with admin/admin123 works
✓ Dashboard loads successfully
✓ Templates are visible (if any exist)
✓ All navigation works

## Still Not Working?

If you've tried all methods and still see errors:

### Check 1: Verify API is Working
Open PowerShell and run:
```powershell
Invoke-RestMethod -Uri "https://48c11a5co1.execute-api.ap-south-1.amazonaws.com/dev/templates" -Method GET
```

If this returns data, the API is working and it's definitely a browser cache issue.

### Check 2: Try a Different Browser
- If you're using Chrome, try Firefox or Edge
- If it works in another browser, it confirms cache issue in your primary browser

### Check 3: Check Browser Extensions
- Disable all browser extensions temporarily
- Some extensions (ad blockers, privacy tools) can interfere with CORS

### Check 4: Check Browser Console for Specific Errors
1. Open DevTools (F12)
2. Go to Console tab
3. Take a screenshot of any errors
4. Look for specific error messages

## Common Cache-Related Issues

### Issue: "Failed to load templates" but API test works
**Cause**: Browser cached the old error response
**Solution**: Use Method 3 (Clear All Cached Data)

### Issue: Login works but dashboard shows errors
**Cause**: Some requests are cached, others aren't
**Solution**: Use Method 6 (Clear Site Data)

### Issue: Works in incognito but not in normal mode
**Cause**: Definitely cached data
**Solution**: Use Method 3, then restart browser

### Issue: CORS error on specific endpoints only
**Cause**: Those specific responses are cached
**Solution**: Use Method 2 (Empty Cache and Hard Reload)

## Quick Test Commands

To verify the API is working from command line:

```powershell
# Test login
$body = '{"username":"admin","password":"admin123"}'
Invoke-RestMethod -Uri "https://48c11a5co1.execute-api.ap-south-1.amazonaws.com/dev/users/login" -Method POST -Body $body -ContentType "application/json"

# Test templates
Invoke-RestMethod -Uri "https://48c11a5co1.execute-api.ap-south-1.amazonaws.com/dev/templates" -Method GET

# Test with CORS headers
$response = Invoke-WebRequest -Uri "https://48c11a5co1.execute-api.ap-south-1.amazonaws.com/dev/templates" -Method GET -UseBasicParsing
$response.Headers.GetEnumerator() | Where-Object { $_.Key -like "*Access-Control*" }
```

If all these commands work, the API is fine and you just need to clear browser cache.

## Recommended Approach

1. **Start with Method 1** (Hard Refresh) - Quickest
2. **If that fails, try Method 4** (Incognito) - Confirms it's cache
3. **Then use Method 3** (Clear All Data) - Most thorough
4. **Finally, restart browser** - Ensures clean state

## Success Indicators

You'll know the cache is cleared when:

1. ✓ Console shows no CORS errors
2. ✓ Network tab shows 200 OK for all requests
3. ✓ Login succeeds without errors
4. ✓ Dashboard loads with "Welcome to AI Assessment!"
5. ✓ Templates load (or "No templates found")

## Important Notes

- **Always close DevTools** before doing a hard refresh
- **Wait a few seconds** after clearing cache before testing
- **Don't spam refresh** - Give the browser time to load fresh data
- **Check Network tab** to see actual request/response, not cached data

## Last Resort

If absolutely nothing works:

1. **Uninstall and reinstall the browser** (extreme but effective)
2. **Use a different computer** to verify the API works
3. **Check if there's a proxy or firewall** blocking requests
4. **Contact your network administrator** if on corporate network

But in 99% of cases, Method 3 (Clear All Cached Data) + browser restart will fix it.
