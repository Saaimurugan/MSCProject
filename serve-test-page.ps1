# Simple HTTP Server for Test Page
# This serves the test-api.html file on http://localhost:8000

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Starting HTTP Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Server will start on: http://localhost:8000" -ForegroundColor Yellow
Write-Host ""
Write-Host "To test the API:" -ForegroundColor Green
Write-Host "1. Open your browser" -ForegroundColor White
Write-Host "2. Navigate to: http://localhost:8000/test-api.html" -ForegroundColor White
Write-Host "3. Click 'Run All Tests'" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
    Write-Host ""
    
    # Start Python HTTP server
    python -m http.server 8000
} catch {
    Write-Host "Python not found. Trying alternative method..." -ForegroundColor Yellow
    Write-Host ""
    
    # Alternative: Use PowerShell HTTP server
    Write-Host "Starting PowerShell HTTP server..." -ForegroundColor Green
    
    $listener = New-Object System.Net.HttpListener
    $listener.Prefixes.Add("http://localhost:8000/")
    $listener.Start()
    
    Write-Host "Server started at http://localhost:8000/" -ForegroundColor Green
    Write-Host "Open http://localhost:8000/test-api.html in your browser" -ForegroundColor Yellow
    Write-Host ""
    
    while ($listener.IsListening) {
        $context = $listener.GetContext()
        $request = $context.Request
        $response = $context.Response
        
        Write-Host "Request: $($request.HttpMethod) $($request.Url.LocalPath)" -ForegroundColor Cyan
        
        $filePath = $request.Url.LocalPath.TrimStart('/')
        if ($filePath -eq '' -or $filePath -eq '/') {
            $filePath = 'test-api.html'
        }
        
        if (Test-Path $filePath) {
            $content = Get-Content $filePath -Raw -Encoding UTF8
            $buffer = [System.Text.Encoding]::UTF8.GetBytes($content)
            
            $response.ContentType = if ($filePath.EndsWith('.html')) { 'text/html' } else { 'text/plain' }
            $response.ContentLength64 = $buffer.Length
            $response.OutputStream.Write($buffer, 0, $buffer.Length)
        } else {
            $response.StatusCode = 404
            $buffer = [System.Text.Encoding]::UTF8.GetBytes("File not found: $filePath")
            $response.OutputStream.Write($buffer, 0, $buffer.Length)
        }
        
        $response.Close()
    }
    
    $listener.Stop()
}
