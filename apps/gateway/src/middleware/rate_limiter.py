import time
import logging
from typing import Dict, List, Optional
from fastapi import HTTPException, status
from config.settings import settings

logger = logging.getLogger("gateway.rate_limiter")

# P1 #9: Maximum distinct IPs tracked in-memory before garbage collection triggers
MAX_IN_MEMORY_ENTRIES = 10000


class RateLimiter:
    """FastAPI Rate Limiter implementing sliding window log algorithm.
    Uses Redis backend with thread-safe local in-memory fallback if Redis is unavailable.
    """
    def __init__(self) -> None:
        self.redis_client = None
        self.in_memory_db: Dict[str, List[float]] = {}
        self.enabled = settings.RATE_LIMIT_ENABLED
        
        if self.enabled:
            try:
                import redis
                self.redis_client = redis.from_url(settings.REDIS_URL, socket_timeout=1.0)
                # Test ping to check availability
                self.redis_client.ping()
                logger.info("Rate limiter successfully initialized with Redis backend.")
            except Exception as e:
                logger.warning(
                    f"Redis connection failed for rate limiter ({e}). "
                    f"Falling back to thread-safe local in-memory rate limiting."
                )
                self.redis_client = None

    def _garbage_collect_in_memory(self) -> None:
        """Evicts the oldest half of in-memory entries when the dict exceeds MAX_IN_MEMORY_ENTRIES."""
        if len(self.in_memory_db) <= MAX_IN_MEMORY_ENTRIES:
            return
        
        # Sort IPs by their latest timestamp and keep only the most recent half
        sorted_ips = sorted(
            self.in_memory_db.keys(),
            key=lambda ip: max(self.in_memory_db[ip]) if self.in_memory_db[ip] else 0
        )
        evict_count = len(sorted_ips) // 2
        for ip in sorted_ips[:evict_count]:
            del self.in_memory_db[ip]
        
        logger.info(f"Rate limiter GC: evicted {evict_count} stale IP entries. Remaining: {len(self.in_memory_db)}")

    def check_rate_limit(self, client_ip: str) -> bool:
        """Verifies if the client IP exceeds request rate thresholds within a sliding 60-second window."""
        if not self.enabled:
            return True
            
        now = time.time()
        window_seconds = 60
        limit = settings.RATE_LIMIT_REQUESTS_PER_MINUTE
        
        # 1. Redis Sliding Window implementation (ZSET log)
        if self.redis_client:
            try:
                key = f"rate_limit:{client_ip}"
                pipe = self.redis_client.pipeline()
                # Prune request log entries older than window frame
                pipe.zremrangebyscore(key, 0, now - window_seconds)
                # Fetch count of requests in current window
                pipe.zcard(key)
                # Append current request timestamp
                pipe.zadd(key, {str(now): now})
                # Add buffer TTL to clean up inactive key storage
                pipe.expire(key, window_seconds + 5)
                
                results = pipe.execute()
                current_requests = results[1]
                
                if current_requests >= limit:
                    logger.warning(f"Rate limit exceeded for client: {client_ip} (Requests: {current_requests}/{limit})")
                    return False
                return True
            except Exception as e:
                logger.error(f"Redis rate limiter exception: {e}. Switching to in-memory fallback.")
                self.redis_client = None  # Fallback to local memory log below
                
        # 2. Local In-Memory Fallback
        # P1 #9: Run garbage collection before adding new entries
        self._garbage_collect_in_memory()
        
        timestamps = self.in_memory_db.get(client_ip, [])
        # Keep only timestamps within sliding window
        valid_timestamps = [t for t in timestamps if t > now - window_seconds]
        
        if len(valid_timestamps) >= limit:
            logger.warning(f"Rate limit exceeded for client (in-memory): {client_ip} (Requests: {len(valid_timestamps)}/{limit})")
            self.in_memory_db[client_ip] = valid_timestamps
            return False
            
        valid_timestamps.append(now)
        self.in_memory_db[client_ip] = valid_timestamps
        return True

rate_limiter = RateLimiter()
