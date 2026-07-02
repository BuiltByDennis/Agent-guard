from prometheus_client import Counter, Histogram, Gauge

OPENAI_REQUEST_COUNT = Counter(
    "openai_requests_total",
    "Total number of requests made to OpenAI",
    ["agent_type", "model", "status_code"]
)

OPENAI_REQUEST_LATENCY = Histogram(
    "openai_request_latency_seconds",
    "Latency of requests made to OpenAI in seconds",
    ["agent_type", "model"]
)

OPENAI_ERROR_COUNT = Counter(
    "openai_errors_total",
    "Total number of errors from OpenAI",
    ["agent_type", "model", "error_type"]
)

DB_POOL_SIZE = Gauge(
    "db_pool_size",
    "Total size of the database connection pool including overflow"
)

DB_POOL_CHECKEDOUT = Gauge(
    "db_pool_checkedout",
    "Number of database connections currently checked out"
)

REDIS_POOL_AVAILABLE = Gauge(
    "redis_pool_available",
    "Status of Redis connection (1 = available, 0 = unavailable)"
)
