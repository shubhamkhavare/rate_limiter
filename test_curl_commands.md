# cURL Commands for Testing Rate Limiter API

## Prerequisites
Make sure the Django server is running:
```bash
python manage.py runserver
```

---

## 1. Ping Endpoint (GET /api/ping/)

### Basic Request
```bash
curl http://127.0.0.1:8000/api/ping/
```

### Test Rate Limiting (5 requests per minute)
```bash
# Request 1-5 (should succeed)
curl http://127.0.0.1:8000/api/ping/
curl http://127.0.1:8000/api/ping/
curl http://127.0.0.1:8000/api/ping/
curl http://127.0.0.1:8000/api/ping/
curl http://127.0.0.1:8000/api/ping/

# Request 6 (should return 429 - Rate Limit Exceeded)
curl http://127.0.0.1:8000/api/ping/
```

### Pretty Print JSON Response
```bash
curl http://127.0.0.1:8000/api/ping/ | python -m json.tool
```

### Windows PowerShell (if curl is aliased to Invoke-WebRequest)
```powershell
Invoke-WebRequest -Uri http://127.0.0.1:8000/api/ping/ | Select-Object -ExpandProperty Content
```

---

## 2. Custom Limit Endpoint (POST /api/custom-limit/)

### Basic Request
```bash
curl -X POST http://127.0.0.1:8000/api/custom-limit/ \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "shubham",
    "limit": 10,
    "window": 60
  }'
```

### Test with Different Identifier
```bash
curl -X POST http://127.0.0.1:8000/api/custom-limit/ \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "test_user_123",
    "limit": 5,
    "window": 30
  }'
```

### Test with Sliding Window Strategy
```bash
curl -X POST http://127.0.0.1:8000/api/custom-limit/ \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "user_sliding",
    "limit": 3,
    "window": 60,
    "strategy": "sliding"
  }'
```

### Test with Fixed Window Strategy
```bash
curl -X POST http://127.0.0.1:8000/api/custom-limit/ \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "user_fixed",
    "limit": 3,
    "window": 60,
    "strategy": "fixed"
  }'
```

### Test Rate Limiting (3 requests limit)
```bash
# Request 1-3 (should succeed)
curl -X POST http://127.0.0.1:8000/api/custom-limit/ \
  -H "Content-Type: application/json" \
  -d '{"identifier": "test_limit", "limit": 3, "window": 60}'

curl -X POST http://127.0.0.1:8000/api/custom-limit/ \
  -H "Content-Type: application/json" \
  -d '{"identifier": "test_limit", "limit": 3, "window": 60}'

curl -X POST http://127.0.0.1:8000/api/custom-limit/ \
  -H "Content-Type: application/json" \
  -d '{"identifier": "test_limit", "limit": 3, "window": 60}'

# Request 4 (should return 429 - Rate Limit Exceeded)
curl -X POST http://127.0.0.1:8000/api/custom-limit/ \
  -H "Content-Type: application/json" \
  -d '{"identifier": "test_limit", "limit": 3, "window": 60}'
```

### Test Validation Errors
```bash
# Missing identifier
curl -X POST http://127.0.0.1:8000/api/custom-limit/ \
  -H "Content-Type: application/json" \
  -d '{"limit": 10, "window": 60}'

# Invalid limit (negative)
curl -X POST http://127.0.0.1:8000/api/custom-limit/ \
  -H "Content-Type: application/json" \
  -d '{"identifier": "test", "limit": -1, "window": 60}'

# Invalid window (zero)
curl -X POST http://127.0.0.1:8000/api/custom-limit/ \
  -H "Content-Type: application/json" \
  -d '{"identifier": "test", "limit": 10, "window": 0}'
```

### Windows PowerShell
```powershell
$body = @{
    identifier = "shubham"
    limit = 10
    window = 60
} | ConvertTo-Json

Invoke-WebRequest -Uri http://127.0.0.1:8000/api/custom-limit/ `
  -Method POST `
  -ContentType "application/json" `
  -Body $body | Select-Object -ExpandProperty Content
```

---

## 3. Stats Endpoint (GET /api/stats/<identifier>/)

### Basic Request (24 hours default)
```bash
curl http://127.0.0.1:8000/api/stats/shubham/
```

### With Custom Time Range (1 hour)
```bash
curl "http://127.0.0.1:8000/api/stats/shubham/?hours=1"
```

### With Custom Time Range (12 hours)
```bash
curl "http://127.0.0.1:8000/api/stats/shubham/?hours=12"
```

### Pretty Print JSON Response
```bash
curl http://127.0.0.1:8000/api/stats/shubham/ | python -m json.tool
```

### Windows PowerShell
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/stats/shubham/?hours=24" | Select-Object -ExpandProperty Content
```

---

## 4. Complete Test Scenario

### Step 1: Make some requests to generate data
```bash
# Make 3 ping requests
curl http://127.0.0.1:8000/api/ping/
curl http://127.0.0.1:8000/api/ping/
curl http://127.0.0.1:8000/api/ping/

# Make 2 custom limit requests
curl -X POST http://127.0.0.1:8000/api/custom-limit/ \
  -H "Content-Type: application/json" \
  -d '{"identifier": "demo_user", "limit": 10, "window": 60}'

curl -X POST http://127.0.0.1:8000/api/custom-limit/ \
  -H "Content-Type: application/json" \
  -d '{"identifier": "demo_user", "limit": 10, "window": 60}'
```

### Step 2: Check stats for your IP (replace with your actual IP)
```bash
# Get your IP from ping response, then check stats
curl http://127.0.0.1:8000/api/stats/127.0.0.1/
curl http://127.0.0.1:8000/api/stats/demo_user/
```

---

## 5. Testing Rate Limit Headers (if you want to see full response)

### Show Headers and Body
```bash
curl -i http://127.0.0.1:8000/api/ping/
```

### Show Only Headers
```bash
curl -I http://127.0.0.1:8000/api/ping/
```

### Verbose Output (for debugging)
```bash
curl -v http://127.0.0.1:8000/api/ping/
```

---

## 6. Quick Test Script (Bash)

Save this as `test_all.sh`:

```bash
#!/bin/bash

echo "Testing Ping Endpoint..."
for i in {1..6}; do
  echo "Request $i:"
  curl -s http://127.0.0.1:8000/api/ping/ | python -m json.tool
  echo ""
done

echo "Testing Custom Limit Endpoint..."
for i in {1..4}; do
  echo "Request $i:"
  curl -s -X POST http://127.0.0.1:8000/api/custom-limit/ \
    -H "Content-Type: application/json" \
    -d '{"identifier": "curl_test", "limit": 3, "window": 60}' | python -m json.tool
  echo ""
done

echo "Testing Stats Endpoint..."
curl -s http://127.0.0.1:8000/api/stats/curl_test/ | python -m json.tool
```

---

## 7. Windows Batch Script

Save this as `test_all.bat`:

```batch
@echo off
echo Testing Ping Endpoint...
for /L %%i in (1,1,6) do (
    echo Request %%i:
    curl http://127.0.0.1:8000/api/ping/
    echo.
)

echo Testing Custom Limit Endpoint...
for /L %%i in (1,1,4) do (
    echo Request %%i:
    curl -X POST http://127.0.0.1:8000/api/custom-limit/ -H "Content-Type: application/json" -d "{\"identifier\": \"curl_test\", \"limit\": 3, \"window\": 60}"
    echo.
)

echo Testing Stats Endpoint...
curl http://127.0.0.1:8000/api/stats/curl_test/
```

---

## Expected Responses

### Success Response (200 OK)
```json
{
  "message": "pong",
  "remaining_requests": 4,
  "reset_time": "2024-01-15T10:30:00.123456Z"
}
```

### Rate Limit Exceeded (429 Too Many Requests)
```json
{
  "error": "Rate limit exceeded",
  "message": "Rate limit exceeded: 5/5 requests in 60s",
  "limit": 5,
  "window_seconds": 60,
  "retry_after": 60
}
```

### Stats Response (200 OK)
```json
{
  "identifier": "shubham",
  "time_range_hours": 24,
  "start_time": "2024-01-14T10:00:00.123456Z",
  "end_time": "2024-01-15T10:00:00.123456Z",
  "total_requests": 45,
  "by_endpoint": [
    {
      "endpoint": "/api/ping/",
      "count": 25,
      "last_request": "2024-01-15T10:00:00.123456Z"
    }
  ],
  "recent_requests": [...]
}
```


