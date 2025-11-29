# Django Rate Limiter Project

A complete, production-style rate limiting system built with Django and Django Rest Framework. This project implements an advanced, optimized rate limiting solution with sliding window strategy, caching, and multiple rate limiting strategies.

## Features

- ✅ **Sliding Window Rate Limiting** - Accurate time-based rate limiting
- ✅ **Fixed Window Strategy** - Alternative bucket-based approach
- ✅ **In-Memory Caching** - Reduces database queries for better performance
- ✅ **Optimized Database Queries** - Uses indexes for fast lookups
- ✅ **IP Extraction Middleware** - Automatically extracts client IP from requests
- ✅ **RESTful API Endpoints** - Clean, well-structured API
- ✅ **Statistics Endpoint** - View request statistics by identifier
- ✅ **Admin Panel Integration** - Full Django admin support
- ✅ **Comprehensive Tests** - Unit tests for all core functionality
- ✅ **Production-Ready Architecture** - Scalable design (can easily switch to Redis)

## Project Structure

```
rate_limiter/
├── rate_limiter_project/     # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── limiter/                  # Main app
│   ├── models.py             # RateLimitLog model
│   ├── views.py              # API views
│   ├── urls.py               # URL routing
│   ├── admin.py              # Admin configuration
│   ├── middleware.py         # IP extraction middleware
│   ├── services/
│   │   └── ratelimiter.py    # Core rate limiting logic
│   └── tests.py              # Unit tests
└── README.md
```

## Installation

### Prerequisites

- Python 3.8+
- pip
- virtualenv (recommended)
- PostgreSQL 12+ (installed and running locally)

### Setup Steps

1. **Clone or navigate to the project directory:**
   ```bash
   cd rate_limiter
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On Linux/Mac
   source venv/bin/activate
   ```

3. **Install PostgreSQL (if not already installed):**
   - **Windows**: Download from [PostgreSQL Downloads](https://www.postgresql.org/download/windows/)
   - **macOS**: `brew install postgresql` or download from [PostgreSQL Downloads](https://www.postgresql.org/download/macosx/)
   - **Linux**: `sudo apt-get install postgresql postgresql-contrib` (Ubuntu/Debian) or `sudo yum install postgresql postgresql-server` (CentOS/RHEL)

4. **Create PostgreSQL database:**
   ```bash
   # Connect to PostgreSQL
   psql -U postgres
   
   # Create database
   CREATE DATABASE rate_limiter_db;
   
   # Exit psql
   \q
   ```
   
   **Note**: If your PostgreSQL user/password differs from the defaults, update `DATABASES` in `rate_limiter_project/settings.py`:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'rate_limiter_db',
           'USER': 'your_username',
           'PASSWORD': 'your_password',
           'HOST': 'localhost',
           'PORT': '5432',
       }
   }
   ```

5. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

6. **Run migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Create a superuser (optional, for admin panel):**
   ```bash
   python manage.py createsuperuser
   ```

8. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

The server will start at `http://127.0.0.1:8000/`

## How Rate Limiting Works

### Core Concepts

1. **Identifier**: A unique identifier for rate limiting (IP address, user_id, API key, etc.)
2. **Endpoint**: The API endpoint being accessed
3. **Limit**: Maximum number of requests allowed
4. **Window**: Time window in seconds (e.g., 60 = 1 minute)

### Sliding Window Strategy

The sliding window strategy counts all requests within the last `window_seconds`. For example:
- If limit is 5 requests per 60 seconds
- At time T, we count requests from (T - 60s) to T
- This provides accurate rate limiting without fixed buckets

### Fixed Window Strategy

The fixed window strategy uses time buckets. Less accurate but more performant for high-traffic scenarios.

### Caching

The system uses in-memory caching to reduce database hits:
- Cache key: `ratelimit:{identifier}:{endpoint}`
- Cache stores: (timestamp, count)
- Cache TTL: window_seconds

### Database Optimization

- Composite indexes on `(identifier, endpoint, timestamp)`
- Individual indexes on `identifier`, `endpoint`, and `timestamp`
- Efficient `.count()` queries with filtered date ranges

## API Endpoints

### 1. GET /api/ping/

Demo endpoint to test rate limiting. Rate limit: **5 requests per minute per IP**.

**Request:**
```bash
curl http://127.0.0.1:8000/api/ping/
```

**Success Response (200 OK):**
```json
{
  "message": "pong",
  "remaining_requests": 4,
  "reset_time": "2024-01-15T10:30:00.123456Z"
}
```

**Rate Limited Response (429 Too Many Requests):**
```json
{
  "error": "Rate limit exceeded",
  "message": "Rate limit exceeded: 5/5 requests in 60s",
  "limit": 5,
  "window_seconds": 60,
  "retry_after": 60
}
```

### 2. POST /api/custom-limit/

Apply rate limiting with custom parameters.

**Request:**
```bash
curl -X POST http://127.0.0.1:8000/api/custom-limit/ \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "shubham",
    "limit": 10,
    "window": 60,
    "strategy": "sliding"
  }'
```

**Request Body:**
```json
{
  "identifier": "shubham",    // Required: IP, user_id, or API key
  "limit": 10,                 // Required: Positive integer
  "window": 60,                // Required: Positive integer (seconds)
  "strategy": "sliding"        // Optional: "sliding" or "fixed" (default: "sliding")
}
```

**Success Response (200 OK):**
```json
{
  "message": "Request allowed",
  "identifier": "shubham",
  "remaining_requests": 9,
  "limit": 10,
  "window_seconds": 60,
  "reset_time": "2024-01-15T10:30:00.123456Z"
}
```

**Rate Limited Response (429 Too Many Requests):**
```json
{
  "error": "Rate limit exceeded",
  "message": "Rate limit exceeded: 10/10 requests in 60s",
  "identifier": "shubham",
  "limit": 10,
  "window_seconds": 60,
  "retry_after": 60
}
```

### 3. GET /api/stats/<identifier>/

View request statistics for an identifier.

**Request:**
```bash
curl http://127.0.0.1:8000/api/stats/shubham/?hours=24
```

**Query Parameters:**
- `hours` (optional): Time range in hours (default: 24)

**Response (200 OK):**
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
      "count": 25
    },
    {
      "endpoint": "/api/custom-limit/",
      "count": 20
    }
  ],
  "recent_requests": [
    {
      "endpoint": "/api/ping/",
      "timestamp": "2024-01-15T10:00:00.123456Z"
    }
  ]
}
```

## Testing with cURL

### Test Ping Endpoint

```bash
# Make 5 requests (within limit)
for i in {1..5}; do
  curl http://127.0.0.1:8000/api/ping/
  echo ""
done

# 6th request should be rate limited
curl http://127.0.0.1:8000/api/ping/
```

### Test Custom Limit Endpoint

```bash
# Make requests with custom identifier
curl -X POST http://127.0.0.1:8000/api/custom-limit/ \
  -H "Content-Type: application/json" \
  -d '{"identifier": "test_user", "limit": 3, "window": 60}'

# Make 3 more requests to hit the limit
for i in {1..3}; do
  curl -X POST http://127.0.0.1:8000/api/custom-limit/ \
    -H "Content-Type: application/json" \
    -d '{"identifier": "test_user", "limit": 3, "window": 60}'
  echo ""
done
```

### Test Stats Endpoint

```bash
# View stats for an identifier
curl http://127.0.0.1:8000/api/stats/test_user/?hours=1
```

## Testing with Postman

1. **Import Collection:**
   - Create a new collection in Postman
   - Add requests for each endpoint

2. **Ping Endpoint:**
   - Method: GET
   - URL: `http://127.0.0.1:8000/api/ping/`
   - Send multiple requests to test rate limiting

3. **Custom Limit Endpoint:**
   - Method: POST
   - URL: `http://127.0.0.1:8000/api/custom-limit/`
   - Headers: `Content-Type: application/json`
   - Body (raw JSON):
     ```json
     {
       "identifier": "postman_test",
       "limit": 5,
       "window": 30
     }
     ```

4. **Stats Endpoint:**
   - Method: GET
   - URL: `http://127.0.0.1:8000/api/stats/postman_test/`

## Running Tests

Run the test suite:

```bash
python manage.py test limiter
```

Test coverage includes:
- Rate limit allowed scenarios
- Rate limit exceeded scenarios
- Sliding and fixed window strategies
- Caching functionality
- Different identifiers and endpoints
- API endpoint tests
- Model tests

## Admin Panel

Access the Django admin panel at `http://127.0.0.1:8000/admin/`

Features:
- View all rate limit logs
- Filter by identifier, endpoint, and timestamp
- Search functionality
- Date hierarchy navigation
- Pagination for large datasets

## Architecture & Scalability

### Current Implementation

- **Database**: PostgreSQL (production-ready)
- **Caching**: In-memory Python dictionary
- **Indexes**: Optimized database indexes for fast queries

### Production Considerations

For production deployment, consider:

1. **Database**: Already using PostgreSQL
   - Configure connection pooling for high traffic
   - Use environment variables for credentials
   - Set up database backups

2. **Caching**: Use Redis
   - Replace `RateLimiter._cache` with Redis client
   - Better performance and distributed caching support

3. **Middleware**: Already production-ready
   - Handles X-Forwarded-For headers
   - Works with load balancers and proxies

4. **Monitoring**: Add logging and metrics
   - Log rate limit violations
   - Track statistics over time

## Code Quality

- ✅ Clean class-based views
- ✅ Separated logic into services/ratelimiter.py
- ✅ Comprehensive unit tests
- ✅ Proper error handling
- ✅ Type hints and documentation
- ✅ Follows Django best practices

## Usage in Your Own Views

To use rate limiting in your own views:

```python
from limiter.services.ratelimiter import RateLimiter, RateLimitExceeded
from rest_framework.response import Response
from rest_framework import status

class MyView(APIView):
    def get(self, request):
        identifier = request.client_ip  # From middleware
        endpoint = '/api/my-endpoint/'
        
        try:
            is_allowed, remaining, reset_time = RateLimiter.check_limit(
                identifier=identifier,
                endpoint=endpoint,
                limit=10,
                window_seconds=60,
                strategy='sliding',
                use_cache=True
            )
            
            # Your view logic here
            return Response({"data": "success"})
        
        except RateLimitExceeded as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
```

## License

This is a learning project. Feel free to use and modify as needed.

## Contributing

This is a learning project. Suggestions and improvements are welcome!

---

**Happy Learning! 🚀**

